# api.py
from fastapi import FastAPI, HTTPException, Query
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
# Load CSVs safely
# ---------------------------
if not os.path.exists(MOVIES_PATH) or not os.path.exists(RATINGS_PATH):
    raise FileNotFoundError("movies.csv or ratings.csv not found in data/ folder")

movies = pd.read_csv(MOVIES_PATH)
ratings = pd.read_csv(RATINGS_PATH)

# Ensure IDs are integers
for col in ['movieId', 'userId']:
    if col in movies.columns:
        movies[col] = pd.to_numeric(movies[col], errors='coerce').fillna(0).astype(int)
    if col in ratings.columns:
        ratings[col] = pd.to_numeric(ratings[col], errors='coerce').fillna(0).astype(int)

# Create 'genres' column if not exists
if 'genres' not in movies.columns or movies['genres'].isna().all():
    genre_columns = [col for col in movies.columns[6:] if movies[col].isin([0,1]).all()]
    if genre_columns:
        movies['genres'] = movies[genre_columns].apply(
            lambda row: '|'.join([genre for genre in genre_columns if row[genre] == 1]),
            axis=1
        )
    else:
        movies['genres'] = ""

# Extract year from title
movies['year'] = movies['title'].str.extract(r'\((\d{4})\)').fillna("N/A")

# ---------------------------
# Load or train model
# ---------------------------
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print(f"✅ Loaded trained model from {MODEL_PATH}")
else:
    reader = Reader(rating_scale=(1,5))
    data = Dataset.load_from_df(ratings[['userId','movieId','rating']], reader)
    trainset, _ = train_test_split(data, test_size=0.2, random_state=42)
    model = SVD()
    model.fit(trainset)
    os.makedirs("model", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Trained and saved model to {MODEL_PATH}")

# ---------------------------
# TF-IDF cosine similarity for genres
# ---------------------------
if movies['genres'].str.strip().any():
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(movies['genres'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
else:
    cosine_sim = None

# ---------------------------
# Models
# ---------------------------
class RatingInput(BaseModel):
    user_id: int
    ratings: dict
    top_n: int = 5

# ---------------------------
# Helper Functions
# ---------------------------
def get_top_n_recommendations(user_id: int, n: int = 5):
    rated_movies = ratings.loc[ratings["userId"] == user_id, "movieId"].tolist()
    unrated_movies = movies[~movies["movieId"].isin(rated_movies)]

    predictions = [(movie_id, model.predict(user_id, movie_id).est) for movie_id in unrated_movies["movieId"]]
    top_n = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]
    top_movies = movies[movies["movieId"].isin([m for m,_ in top_n])]

    return [
        {
            "movieId": int(row.movieId),
            "title": row.title,
            "genres": row.genres if 'genres' in row and row.genres else "N/A",
            "year": row.year,
            "predicted_rating": round(float(dict(top_n)[row.movieId]),2)
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
    return movies.iloc[movie_indices][["movieId","title","genres","year"]].to_dict(orient="records")

# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def root():
    return {"message": "Robust Movie Recommender API is running!"}

# Top-N recommendations
@app.get("/recommend/{user_id}")
def recommend_movies(user_id: int, n: int = 5):
    return get_top_n_recommendations(user_id, n)

# Movie info by ID
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
        "genres": movie.genres if movie.genres else "N/A",
        "year": movie.year,
        "average_rating": round(avg_rating,2) if avg_rating else None
    }

# All movies (for autocomplete dropdown)
@app.get("/movies/all")
def get_all_movies():
    return movies[["movieId","title","genres","year"]].to_dict(orient="records")

# User info
@app.get("/users/{user_id}")
def get_user(user_id: int):
    user_ratings = ratings[ratings["userId"] == user_id]
    if user_ratings.empty:
        raise HTTPException(status_code=404, detail="User not found")
    rated_movies = pd.merge(user_ratings, movies, on="movieId")[["movieId","title","genres","year","rating"]].to_dict(orient="records")
    avg_rating = user_ratings["rating"].mean()
    return {"userId": user_id, "average_rating": round(avg_rating,2), "rated_movies": rated_movies}

# Submit rating and get top-N recommendations
@app.post("/rate")
def rate_movie(rating_input: RatingInput):
    global ratings
    new_rows = [{"userId": rating_input.user_id, "movieId": int(mid), "rating": float(r)} for mid, r in rating_input.ratings.items()]
    ratings = pd.concat([ratings, pd.DataFrame(new_rows)], ignore_index=True)
    top_recs = get_top_n_recommendations(rating_input.user_id, rating_input.top_n)
    return {"message": "Rating submitted successfully", "recommendations": top_recs}

# Top-rated movies
@app.get("/top-rated")
def top_rated(n: int = 10):
    avg_ratings = ratings.groupby("movieId")["rating"].mean().reset_index()
    top_movies = avg_ratings.sort_values("rating", ascending=False).head(n)
    top_movies = pd.merge(top_movies, movies, on="movieId")
    return top_movies[["movieId","title","genres","year","rating"]].to_dict(orient="records")

# Similar movies
@app.get("/similar/{movie_id}")
def similar_movies_endpoint(movie_id: int, n: int = 5):
    return get_similar_movies(movie_id, n)
