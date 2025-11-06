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

# ============================================================
# FILE PATHS
# ============================================================
MOVIES_PATH = "data/movies.csv"
RATINGS_PATH = "data/ratings.csv"
MODEL_PATH = "model/trained_model.pkl"

# ============================================================
# LOAD MOVIES & RATINGS
# ============================================================
if not os.path.exists(MOVIES_PATH) or not os.path.exists(RATINGS_PATH):
    raise FileNotFoundError("Missing movies.csv or ratings.csv in data/ folder")

movies = pd.read_csv(MOVIES_PATH)
ratings = pd.read_csv(RATINGS_PATH)

# Convert numeric IDs
for col in ['movieId', 'userId']:
    if col in movies.columns:
        movies[col] = pd.to_numeric(movies[col], errors='coerce').fillna(0).astype(int)
    if col in ratings.columns:
        ratings[col] = pd.to_numeric(ratings[col], errors='coerce').fillna(0).astype(int)

# ============================================================
# COMBINE GENRE COLUMNS IF NEEDED
# ============================================================
genre_columns = [c for c in movies.columns if movies[c].isin([0, 1]).all()]
if genre_columns:
    movies['genres'] = movies[genre_columns].apply(
        lambda row: '|'.join([c for c in genre_columns if row[c] == 1]),
        axis=1
    )
elif 'genres' not in movies.columns:
    movies['genres'] = 'Unknown'

# ============================================================
# LOAD OR TRAIN MODEL
# ============================================================
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception:
        model = SVD()
else:
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
    trainset, _ = train_test_split(data, test_size=0.2, random_state=42)
    model = SVD()
    model.fit(trainset)
    os.makedirs("model", exist_ok=True)
    joblib.dump(model, MODEL_PATH)

# ============================================================
# TF-IDF COSINE SIMILARITY (for similar movies)
# ============================================================
if 'genres' in movies.columns and movies['genres'].str.strip().any():
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(movies['genres'].fillna(''))
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
else:
    cosine_sim = None

# ============================================================
# Pydantic Models
# ============================================================
class RatingInput(BaseModel):
    user_id: int
    movie_id: int
    rating: float

class NewUserInput(BaseModel):
    user_id: int
    ratings: dict
    top_n: int = 5

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_top_n_recommendations(user_id: int, n: int = 5):
    """Generate Top-N recommendations for a given user."""
    if user_id not in ratings["userId"].unique():
        raise HTTPException(status_code=404, detail="User ID not found")

    rated_movies = ratings.loc[ratings["userId"] == user_id, "movieId"].tolist()
    unrated_movies = movies[~movies["movieId"].isin(rated_movies)]

    predictions = [(mid, model.predict(user_id, mid).est) for mid in unrated_movies["movieId"]]
    top_n = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]

    top_movies = movies[movies["movieId"].isin([m for m, _ in top_n])]
    pred_dict = dict(top_n)

    results = []
    for _, row in top_movies.iterrows():
        results.append({
            "movieId": int(row.movieId),
            "title": row.title,
            "genres": row.get("genres", "Unknown"),
            "predicted_rating": round(pred_dict.get(row.movieId, 0), 2)
        })
    return results

def get_similar_movies(movie_id: int, n: int = 5):
    """Find movies similar by genre using cosine similarity."""
    if cosine_sim is None:
        raise HTTPException(status_code=404, detail="No genre similarity data available.")
    if movie_id not in movies["movieId"].values:
        raise HTTPException(status_code=404, detail="Movie not found.")

    idx = movies.index[movies["movieId"] == movie_id][0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:n + 1]
    movie_indices = [i[0] for i in sim_scores]
    return movies.iloc[movie_indices][["movieId", "title", "genres"]].to_dict(orient="records")

# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def root():
    return {"message": "🎥 Movie Recommender API is online!"}

# --- MOVIES ---
@app.get("/movies/all")
def get_all_movies():
    """Return all movies (for dropdown autocomplete)."""
    return movies[["movieId", "title", "genres"]].to_dict(orient="records")

@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = movies.loc[movies["movieId"] == movie_id]
    if movie.empty:
        raise HTTPException(status_code=404, detail="Movie not found.")
    movie = movie.iloc[0]
    movie_ratings = ratings.loc[ratings["movieId"] == movie_id, "rating"]
    avg_rating = round(movie_ratings.mean(), 2) if not movie_ratings.empty else None
    return {
        "movieId": int(movie.movieId),
        "title": movie.title,
        "genres": movie.get("genres", "Unknown"),
        "average_rating": avg_rating
    }

# --- USERS ---
@app.get("/users/{user_id}")
def get_user(user_id: int):
    user_ratings = ratings[ratings["userId"] == user_id]
    if user_ratings.empty:
        raise HTTPException(status_code=404, detail="User not found.")
    rated_movies = pd.merge(user_ratings, movies, on="movieId")[["movieId", "title", "rating"]]
    avg_rating = round(user_ratings["rating"].mean(), 2)
    return {
        "userId": user_id,
        "average_rating": avg_rating,
        "rated_movies": rated_movies.to_dict(orient="records")
    }

# --- RECOMMENDATIONS ---
@app.get("/recommend/{user_id}")
def recommend_movies(user_id: int, n: int = 5):
    return get_top_n_recommendations(user_id, n)

# --- SIMILAR MOVIES ---
@app.get("/similar/{movie_id}")
def similar_movies(movie_id: int, n: int = 5):
    return get_similar_movies(movie_id, n)

# --- RATE EXISTING MOVIE ---
@app.post("/rate_movie")
def rate_movie(rating_input: RatingInput):
    global ratings
    ratings = pd.concat(
        [ratings, pd.DataFrame([{
            "userId": rating_input.user_id,
            "movieId": rating_input.movie_id,
            "rating": rating_input.rating
        }])],
        ignore_index=True
    )
    return {"message": "Rating submitted successfully."}

# --- RATE & RECOMMEND (for NEW USERS) ---
@app.post("/rate/")
def rate_and_recommend(input_data: NewUserInput):
    global ratings
    user_id = input_data.user_id
    for movie_id, rating in input_data.ratings.items():
        ratings = pd.concat(
            [ratings, pd.DataFrame([{
                "userId": user_id,
                "movieId": int(movie_id),
                "rating": float(rating)
            }])],
            ignore_index=True
        )
    return get_top_n_recommendations(user_id, input_data.top_n)

# --- TOP RATED MOVIES ---
@app.get("/top-rated")
def top_rated(n: int = 10):
    avg_ratings = ratings.groupby("movieId")["rating"].mean().reset_index()
    top_movies = avg_ratings.sort_values("rating", ascending=False).head(n)
    merged = pd.merge(top_movies, movies, on="movieId", how="left")
    merged["rating"] = merged["rating"].round(2)
    merged["genres"] = merged["genres"].fillna("Unknown")
    return merged[["movieId", "title", "genres", "rating"]].to_dict(orient="records")

# --- MODEL INFO ---
@app.get("/model-info")
def model_info():
    if ratings.empty:
        raise HTTPException(status_code=404, detail="No rating data available.")

    reader = Reader(rating_scale=(ratings.rating.min(), ratings.rating.max()))
    data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    predictions = model.test(testset)
    rmse = accuracy.rmse(predictions, verbose=False)
    mae = accuracy.mae(predictions, verbose=False)

    return {
        "model_type": type(model).__name__,
        "num_ratings": len(ratings),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4)
    }
