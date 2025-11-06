# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import os
from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

# ---------------------------
# File paths
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOVIES_PATH = os.path.join(BASE_DIR, "data/movies.csv")
RATINGS_PATH = os.path.join(BASE_DIR, "data/ratings.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model/trained_model.pkl")

app = FastAPI(title="Robust Movie Recommender API")

# ---------------------------
# Globals
# ---------------------------
movies: pd.DataFrame = None
ratings: pd.DataFrame = None
model: SVD = None
cosine_sim = None

# ---------------------------
# Models
# ---------------------------
class RatingInput(BaseModel):
    userId: int
    movieId: int
    rating: float

# ---------------------------
# Startup event
# ---------------------------
@app.on_event("startup")
def startup_event():
    global movies, ratings, model, cosine_sim

    # Load CSVs
    if not os.path.exists(MOVIES_PATH) or not os.path.exists(RATINGS_PATH):
        raise FileNotFoundError("movies.csv or ratings.csv not found in data/ folder")

    movies = pd.read_csv(MOVIES_PATH)
    ratings = pd.read_csv(RATINGS_PATH)

    # Ensure IDs are integers
    for col in ["movieId", "userId"]:
        if col in movies.columns:
            movies[col] = pd.to_numeric(movies[col], errors="coerce").fillna(0).astype(int)
        if col in ratings.columns:
            ratings[col] = pd.to_numeric(ratings[col], errors="coerce").fillna(0).astype(int)

    # Convert one-hot genre columns to 'genres'
    genre_columns = [col for col in movies.columns[6:] if movies[col].isin([0,1]).all()]
    if genre_columns:
        movies["genres"] = movies[genre_columns].apply(
            lambda row: "|".join([genre for genre in genre_columns if row[genre] == 1]),
            axis=1
        )
    else:
        movies["genres"] = ""

    # Load or train model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    else:
        reader = Reader(rating_scale=(1,5))
        data = Dataset.load_from_df(ratings[["userId", "movieId", "rating"]], reader)
        trainset, _ = train_test_split(data, test_size=0.2)
        model = SVD()
        model.fit(trainset)
        os.makedirs(os.path.join(BASE_DIR, "model"), exist_ok=True)
        joblib.dump(model, MODEL_PATH)

    # TF-IDF and cosine similarity for genres
    if movies["genres"].str.strip().any():
        tfidf = TfidfVectorizer(stop_words="english")
        tfidf_matrix = tfidf.fit_transform(movies["genres"])
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    else:
        cosine_sim = None

# ---------------------------
# Helper functions
# ---------------------------
def get_top_n_recommendations(user_id: int, n: int = 5) -> List[Dict]:
    if user_id not in ratings["userId"].unique():
        raise HTTPException(status_code=404, detail="User ID not found")

    rated_movies = ratings.loc[ratings["userId"] == user_id, "movieId"].tolist()
    unrated_movies = movies[~movies["movieId"].isin(rated_movies)]

    predictions = [(movie_id, model.predict(user_id, movie_id).est) for movie_id in unrated_movies["movieId"]]
    top_n = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]

    return [
        {
            "movieId": int(mid),
            "title": movies.loc[movies["movieId"] == mid, "title"].values[0],
            "genres": movies.loc[movies["movieId"] == mid, "genres"].values[0],
            "predicted_rating": round(float(rating), 2)
        }
        for mid, rating in top_n
    ]

def get_similar_movies(movie_id: int, n: int = 5) -> List[Dict]:
    if cosine_sim is None:
        raise HTTPException(status_code=404, detail="Genre similarity data not available")
    if movie_id not in movies["movieId"].values:
        raise HTTPException(status_code=404, detail="Movie not found")
    idx = movies.index[movies["movieId"] == movie_id][0]
    sim_scores = sorted(list(enumerate(cosine_sim[idx])), key=lambda x: x[1], reverse=True)[1:n+1]
    movie_indices = [i[0] for i in sim_scores]
    return movies.iloc[movie_indices][["movieId", "title", "genres"]].to_dict(orient="records")

# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def root():
    return {"message": "Robust Movie Recommender API is running!"}

@app.get("/recommend/{user_id}")
def recommend_movies(user_id: int, n: int = 5):
    return {"recommendations": get_top_n_recommendations(user_id, n)}

@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = movies.loc[movies["movieId"] == movie_id]
    if movie.empty:
        raise HTTPException(status_code=404, detail="Movie not found")
    movie = movie.iloc[0]
    movie_ratings = ratings.loc[ratings["movieId"] == movie_id, "rating"]
    avg_rating = round(movie_ratings.mean(), 2) if not movie_ratings.empty else None
    return {
        "movieId": int(movie.movieId),
        "title": movie.title,
        "genres": getattr(movie, "genres", "N/A"),
        "average_rating": avg_rating
    }

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user_ratings = ratings[ratings["userId"] == user_id]
    if user_ratings.empty:
        raise HTTPException(status_code=404, detail="User not found")
    rated_movies = pd.merge(user_ratings, movies, on="movieId")[["movieId", "title", "genres", "rating"]].to_dict(orient="records")
    avg_rating = round(user_ratings["rating"].mean(), 2)
    return {"userId": user_id, "average_rating": avg_rating, "rated_movies": rated_movies}

@app.post("/rate")
def rate_movie(rating_input: RatingInput):
    global ratings
    ratings = pd.concat([ratings, pd.DataFrame([rating_input.dict()])], ignore_index=True)
    return {"message": "Rating submitted successfully", "data": rating_input.dict()}

@app.get("/top-rated")
def top_rated(n: int = 10):
    avg_ratings = ratings.groupby("movieId")["rating"].mean().reset_index()
    top_movies = avg_ratings.sort_values("rating", ascending=False).head(n)
    top_movies = pd.merge(top_movies, movies, on="movieId")
    top_movies["rating"] = top_movies["rating"].round(2)
    return top_movies[["movieId", "title", "genres", "rating"]].to_dict(orient="records")

@app.get("/similar/{movie_id}")
def similar_movies_endpoint(movie_id: int, n: int = 5):
    return get_similar_movies(movie_id, n)

@app.get("/all-movies")
def all_movies():
    return movies[["movieId", "title"]].to_dict(orient="records")
