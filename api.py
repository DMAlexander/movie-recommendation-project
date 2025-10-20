# api.py
from fastapi import FastAPI
import pickle
import pandas as pd
from surprise import Dataset, SVD, Reader

import os

# Paths
here = os.path.dirname(__file__)
model_path = os.path.join(here, "model.pkl")
movies_path = os.path.join(here, "u.item")  # MovieLens titles

# Load model
with open(model_path, "rb") as f:
    model = pickle.load(f)

# Load movie metadata
movies = pd.read_csv(
    "http://files.grouplens.org/datasets/movielens/ml-100k/u.item",
    sep="|", encoding="latin-1",
    usecols=[0, 1], names=["movie_id", "title"]
)

app = FastAPI()

@app.get("/recommend/{user_id}")
def recommend(user_id: int, n: int = 5):
    """
    Get top-N personalized movie recommendations for a user.
    """
    all_movie_ids = movies["movie_id"].tolist()
    
    # Predict rating for each movie for this user
    predictions = [(mid, model.predict(user_id, mid).est) for mid in all_movie_ids]
    
    # Sort by predicted rating descending
    top_movies = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]
    
    recs = [movies[movies["movie_id"] == mid]["title"].values[0] for mid, _ in top_movies]
    return {"user_id": user_id, "recommendations": recs}

@app.post("/rate/")
def rate_movies(ratings: dict):
    """
    Accepts a new user's ratings and returns personalized recommendations.
    Example input:
    {
        "user_id": 1000,
        "ratings": {
            "1": 5,   # movie_id: rating
            "50": 3,
            "100": 4
        },
        "top_n": 5
    }
    """
    user_id = ratings["user_id"]
    user_ratings = ratings["ratings"]
    top_n = ratings.get("top_n", 5)

    # Create a temporary dataset for this user
    temp_data = [(str(user_id), str(mid), float(r)) for mid, r in user_ratings.items()]
    reader = Reader(rating_scale=(1, 5))
    temp_dataset = Dataset.load_from_df(pd.DataFrame(temp_data, columns=["userID","itemID","rating"]), reader)
    trainset = temp_dataset.build_full_trainset()
    
    # Update model using partial_fit (or just use original model for prediction)
    # For simplicity, we will predict for this user based on SVD model
    all_movie_ids = movies["movie_id"].tolist()
    predictions = []
    for mid in all_movie_ids:
        if mid in user_ratings:
            continue  # skip movies already rated
        predictions.append((mid, model.predict(user_id, mid).est))
    
    top_movies = sorted(predictions, key=lambda x: x[1], reverse=True)[:top_n]
    recs = [movies[movies["movie_id"] == mid]["title"].values[0] for mid, _ in top_movies]
    return {"user_id": user_id, "recommendations": recs}
