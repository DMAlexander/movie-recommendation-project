from fastapi import FastAPI
import pickle
import pandas as pd

app = FastAPI()

# Load trained model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# Load movie data
movies = pd.read_csv("movies.csv")
ratings = pd.read_csv("ratings.csv")

@app.get("/")
def read_root():
    return {"message": "Movie Recommendation API is running!"}

@app.get("/recommend/{user_id}")
def recommend(user_id: int, top_n: int = 5):
    # Generate top-N recommendations for the given user
    user_ratings = ratings[ratings.userId == user_id]
    movie_ids_watched = user_ratings.movieId.tolist()

    all_movie_ids = movies.movieId.tolist()
    movie_ids_to_predict = [mid for mid in all_movie_ids if mid not in movie_ids_watched]

    predictions = [(mid, model.predict(user_id, mid).est) for mid in movie_ids_to_predict]
    top_predictions = sorted(predictions, key=lambda x: x[1], reverse=True)[:top_n]

    recommended_movies = movies[movies.movieId.isin([mid for mid, _ in top_predictions])]
    recommended_movies["predicted_rating"] = [rating for _, rating in top_predictions]

    return recommended_movies.to_dict(orient="records")


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
