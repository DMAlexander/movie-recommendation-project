from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
import pandas as pd
import joblib
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

app = FastAPI(title="Movie Recommendation API")

# ---------- Data Loading ----------
MOVIES_PATH = "movies.csv"
RATINGS_PATH = "ratings.csv"
MODEL_PATH = "model.pkl"

# Load datasets
movies_df = pd.read_csv(MOVIES_PATH)
ratings_df = pd.read_csv(RATINGS_PATH)

# Compute average ratings
movie_ratings = ratings_df.groupby("movieId")["rating"].mean().reset_index(name="average_rating")
movies_df = movies_df.merge(movie_ratings, on="movieId", how="left").fillna({"average_rating": 0})

# ---------- Model Loading ----------
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    # Train SVD model if none exists
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings_df[["userId", "movieId", "rating"]], reader)
    trainset = data.build_full_trainset()
    model = SVD()
    model.fit(trainset)
    joblib.dump(model, MODEL_PATH)

# ---------- Text Vectorizer for Similar Movies ----------
tfidf = TfidfVectorizer(stop_words="english")
movies_df["genres"] = movies_df["genres"].fillna("")
tfidf_matrix = tfidf.fit_transform(movies_df["genres"])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# ---------- Request Models ----------
class RatingRequest(BaseModel):
    user_id: int
    ratings: dict  # {movie_id: rating}
    top_n: int = 5


# ---------- Endpoints ----------

@app.get("/")
def root():
    return {"message": "Movie Recommendation API is running!"}


# ✅ Get movie by ID
@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = movies_df[movies_df["movieId"] == movie_id]
    if movie.empty:
        raise HTTPException(status_code=404, detail="Movie not found")
    m = movie.iloc[0]
    return {
        "movieId": int(m.movieId),
        "title": m.title,
        "genres": m.genres if pd.notna(m.genres) else "N/A",
        "average_rating": round(float(m.average_rating), 2)
    }


# ✅ Get movie by title (for autocomplete)
@app.get("/movies/search/")
def search_movies(q: str):
    results = movies_df[movies_df["title"].str.contains(q, case=False, na=False)].head(10)
    return [
        {
            "movieId": int(row.movieId),
            "title": row.title,
            "genres": row.genres if pd.notna(row.genres) else "N/A",
            "average_rating": round(float(row.average_rating), 2),
        }
        for _, row in results.iterrows()
    ]


# ✅ Get all movies (for dropdowns)
@app.get("/movies/all")
def get_all_movies():
    return [
        {
            "movieId": int(row.movieId),
            "title": row.title,
            "genres": row.genres if pd.notna(row.genres) else "N/A",
            "average_rating": round(float(row.average_rating), 2),
        }
        for _, row in movies_df.iterrows()
    ]


# ✅ Get top-rated movies
@app.get("/top-rated")
def get_top_rated(n: int = 10):
    top_movies = movies_df.sort_values(by="average_rating", ascending=False).head(n)
    return [
        {
            "movieId": int(row.movieId),
            "title": row.title,
            "genres": row.genres if pd.notna(row.genres) else "N/A",
            "average_rating": round(float(row.average_rating), 2),
        }
        for _, row in top_movies.iterrows()
    ]


# ✅ Get similar movies
@app.get("/similar/{movie_id}")
def get_similar_movies(movie_id: int, n: int = 5):
    if movie_id not in movies_df["movieId"].values:
        raise HTTPException(status_code=404, detail="Movie not found")

    idx = movies_df.index[movies_df["movieId"] == movie_id][0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:n + 1]
    similar_indices = [i[0] for i in sim_scores]

    results = movies_df.iloc[similar_indices]
    return [
        {
            "movieId": int(row.movieId),
            "title": row.title,
            "genres": row.genres if pd.notna(row.genres) else "N/A",
            "average_rating": round(float(row.average_rating), 2),
        }
        for _, row in results.iterrows()
    ]


# ✅ Get recommendations for existing user
@app.get("/recommend/{user_id}")
def recommend_movies(user_id: int, n: int = 5):
    if user_id not in ratings_df["userId"].unique():
        raise HTTPException(status_code=404, detail="User not found")

    all_movie_ids = movies_df["movieId"].tolist()
    rated_movie_ids = ratings_df[ratings_df["userId"] == user_id]["movieId"].tolist()
    unrated_movies = [m for m in all_movie_ids if m not in rated_movie_ids]

    predictions = [(mid, model.predict(user_id, mid).est) for mid in unrated_movies]
    predictions.sort(key=lambda x: x[1], reverse=True)
    top_preds = predictions[:n]

    return {
        "user_id": user_id,
        "recommendations": [
            {
                "movieId": int(movies_df.loc[movies_df["movieId"] == mid, "movieId"].values[0]),
                "title": movies_df.loc[movies_df["movieId"] == mid, "title"].values[0],
                "genres": movies_df.loc[movies_df["movieId"] == mid, "genres"].values[0],
                "predicted_rating": round(float(score), 2),
            }
            for mid, score in top_preds
        ],
    }


# ✅ Rate movies and get recommendations (for new users)
@app.post("/rate/")
def rate_movies(request: RatingRequest):
    user_id = request.user_id
    new_ratings = pd.DataFrame(
        [{"userId": user_id, "movieId": mid, "rating": r} for mid, r in request.ratings.items()]
    )

    combined_ratings = pd.concat([ratings_df, new_ratings], ignore_index=True)
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(combined_ratings[["userId", "movieId", "rating"]], reader)
    trainset = data.build_full_trainset()

    new_model = SVD()
    new_model.fit(trainset)

    all_movie_ids = movies_df["movieId"].tolist()
    rated_movie_ids = list(request.ratings.keys())
    unrated_movies = [m for m in all_movie_ids if m not in rated_movie_ids]

    predictions = [(mid, new_model.predict(user_id, mid).est) for mid in unrated_movies]
    predictions.sort(key=lambda x: x[1], reverse=True)
    top_preds = predictions[:request.top_n]

    return {
        "user_id": user_id,
        "recommendations": [
            {
                "movieId": int(movies_df.loc[movies_df["movieId"] == mid, "movieId"].values[0]),
                "title": movies_df.loc[movies_df["movieId"] == mid, "title"].values[0],
                "genres": movies_df.loc[movies_df["movieId"] == mid, "genres"].values[0],
                "predicted_rating": round(float(score), 2),
            }
            for mid, score in top_preds
        ],
    }
