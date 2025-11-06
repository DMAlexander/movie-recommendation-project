# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import train_test_split
import pandas as pd
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI(title="Robust Movie Recommender API")

# ---------------------------
# File paths
# ---------------------------
MOVIES_PATH = "data/movies.csv"
RATINGS_PATH = "data/ratings.csv"
MODEL_PATH = "model/trained_model.pkl"

# ---------------------------
# Load CSVs
# ---------------------------
if not os.path.exists(MOVIES_PATH) or not os.path.exists(RATINGS_PATH):
    raise FileNotFoundError("movies.csv or ratings.csv not found in data/ folder")

movies = pd.read_csv(MOVIES_PATH)
ratings = pd.read_csv(RATINGS_PATH)

# ---------------------------
# Ensure IDs are integers
# ---------------------------
for col in ['movieId', 'userId']:
    if col in movies.columns:
        movies[col] = pd.to_numeric(movies[col], errors='coerce').fillna(0).astype(int)
    if col in ratings.columns:
        ratings[col] = pd.to_numeric(ratings[col], errors='coerce').fillna(0).astype(int)

# ---------------------------
# Convert one-hot genre columns to 'genres' column safely
# ---------------------------
genre_columns = [col for col in movies.columns[6:] if movies[col].isin([0,1]).all()]
if genre_columns:
    movies['genres'] = movies[genre_columns].apply(
        lambda row: '|'.join([genre for genre in genre_columns if row[genre] == 1]),
        axis=1
    )
else:
    movies['genres'] = ""

# ---------------------------
# Load or train model safely with fallback
# ---------------------------
os.makedirs("model", exist_ok=True)
model = None

if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print(f"✅ Loaded trained model from {MODEL_PATH}")
    except Exception as e:
        print(f"⚠️ Failed to load existing model: {e}")
        model = None

if model is None:
    print("⚠️ No trained model found — training a new SVD model on available ratings...")
    reader = Reader(rating_scale=(ratings.rating.min(), ratings.rating.max()))
    data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
    trainset, _ = train_test_split(data, test_size=0.2, random_state=42)
    model = SVD()
    model.fit(trainset)
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Model trained and saved to {MODEL_PATH}")

# ---------------------------
# Compute TF-IDF and cosine similarity if genres exist
# ---------------------------
if movies['genres'].str.strip().any():
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(movies['genres'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
else:
    cosine_sim = None

# ---------------------------
# Helper functions
# ---------------------------
def get_top_n_recommendations(user_id: int, n: int = 5):
    if user_id not in ratings["userId"].unique():
        raise HTTPException(status_code=404, detail="User ID not found")

    rated_movies = ratings.loc[ratings["userId"] == user_id, "movieId"].tolist()
    unrated_movies = movies[~movies["movieId"].isin(rated_movies)]

    predictions = [
        (movie_id, model.predict(user_id, movie_id).est)
        for movie_id in unrated_movies["movieId"]
    ]

    top_n = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]
    top_movies = movies[movies["movieId"].isin([m for m, _ in top_n])]

    return [
        {
            "movieId": int(row.movieId),
            "title": row.title,
            "genres": getattr(row, 'genres', ""),
            "predicted_rating": round(float(dict(top_n)[row.movieId]), 2)
        }
        for _, row in top_movies.iterrows()
    ]

def get_similar_movies(movie_id: int, n: int = 5):
    if cosine_sim is None:
        raise HTTPException(status_code=404, detail="Genre similarity data not available")
    if movie_id not in movies["movieId"].values:
        raise HTTPException(status_code=404, detail="Movie not found")
    idx = movies.index[movies["movieId"] == movie_id][0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:n+1]
    movie_indices = [i[0] for i in sim_scores]
    return movies.iloc[movie_indices][["movieId", "title", "genres"]].to_dict(orient="records")

# ---------------------------
# Models
# ---------------------------
class RatingInput(BaseModel):
    userId: int
    movieId: int
    rating: float

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
    avg_rating = movie_ratings.mean() if not movie_ratings.empty else None
    return {
        "movieId": int(movie.movieId),
        "title": movie.title,
        "genres": getattr(movie, 'genres', ""),
        "average_rating": round(avg_rating, 2) if avg_rating is not None else None
    }

@app.get("/movies/all")
def get_all_movies(limit: int = Query(None, ge=1)):
    """
    Returns a list of all movies with their IDs, titles, and genres.
    Optional query parameter `limit` can restrict the number of movies returned.
    """
    df = movies[["movieId", "title", "genres"]].copy()
    if limit:
        df = df.head(limit)
    return df.to_dict(orient="records")

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user_ratings = ratings[ratings["userId"] == user_id]
    if user_ratings.empty:
        raise HTTPException(status_code=404, detail="User not found")
    rated_movies = pd.merge(user_ratings, movies, on="movieId")[["movieId", "title", "rating", "genres"]].to_dict(orient="records")
    avg_rating = user_ratings["rating"].mean()
    return {"userId": user_id, "average_rating": round(avg_rating, 2), "rated_movies": rated_movies}

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
    return [
        {
            "movieId": int(row.movieId),
            "title": row.title,
            "genres": getattr(row, 'genres', ""),
            "rating": round(float(row.rating), 2)
        }
        for _, row in top_movies.iterrows()
    ]

@app.get("/similar/{movie_id}")
def similar_movies_endpoint(movie_id: int, n: int = 5):
    return get_similar_movies(movie_id, n)

@app.get("/model-info")
def model_info():
    reader = Reader(rating_scale=(ratings.rating.min(), ratings.rating.max()))
    data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    predictions = model.test(testset)
    rmse = accuracy.rmse(predictions, verbose=False)
    mae = accuracy.mae(predictions, verbose=False)
    return {
        "model_type": type(model).__name__,
        "num_ratings": len(ratings),
        "rmse_on_test": round(rmse, 4),
        "mae_on_test": round(mae, 4)
    }

@app.post("/retrain")
def retrain_model():
    global model
    reader = Reader(rating_scale=(ratings.rating.min(), ratings.rating.max()))
    data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    model = SVD()
    model.fit(trainset)
    predictions = model.test(testset)
    rmse = accuracy.rmse(predictions, verbose=False)
    mae = accuracy.mae(predictions, verbose=False)
    joblib.dump(model, MODEL_PATH)
    return {
        "message": "Model retrained successfully",
        "num_ratings": len(ratings),
        "rmse_on_test": round(rmse, 4),
        "mae_on_test": round(mae, 4)
    }
