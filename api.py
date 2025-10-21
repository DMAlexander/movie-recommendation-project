from fastapi import FastAPI, HTTPException
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
import pandas as pd
import joblib
import os

app = FastAPI()

# File paths
MOVIES_PATH = "data/movies.csv"
RATINGS_PATH = "data/ratings.csv"
MODEL_PATH = "model/trained_model.pkl"

# Step 1: Load data
if not os.path.exists(MOVIES_PATH) or not os.path.exists(RATINGS_PATH):
    raise FileNotFoundError("movies.csv or ratings.csv not found in data/ folder")

movies = pd.read_csv(MOVIES_PATH)
ratings = pd.read_csv(RATINGS_PATH)

# Step 2: Load or train model
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
    trainset, _ = train_test_split(data, test_size=0.2)
    model = SVD()
    model.fit(trainset)
    os.makedirs("model", exist_ok=True)
    joblib.dump(model, MODEL_PATH)

# Step 3: Helper to get movie recommendations
def get_top_n_recommendations(user_id: int, n: int = 5):
    if user_id not in ratings["userId"].unique():
        raise HTTPException(status_code=404, detail="User ID not found")

    # Movies the user hasn’t rated
    rated_movies = ratings.loc[ratings["userId"] == user_id, "movieId"].tolist()
    unrated_movies = movies[~movies["movieId"].isin(rated_movies)]

    # Predict ratings for unrated movies
    predictions = [
        (movie_id, model.predict(user_id, movie_id).est)
        for movie_id in unrated_movies["movieId"]
    ]

    # Get top N
    top_n = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]
    top_movies = movies[movies["movieId"].isin([m for m, _ in top_n])]

    return [
        {"movieId": row.movieId, "title": row.title, "predicted_rating": float(dict(top_n)[row.movieId])}
        for _, row in top_movies.iterrows()
    ]

# Step 4: Routes
@app.get("/")
def root():
    return {"message": "Movie recommender API is running!"}

@app.get("/recommend/{user_id}")
def recommend_movies(user_id: int, n: int = 5):
    return get_top_n_recommendations(user_id, n)
