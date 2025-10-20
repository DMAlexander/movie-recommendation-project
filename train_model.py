# train_model.py
import pandas as pd
from surprise import SVD, Dataset, Reader
import pickle

# Load MovieLens data
ratings = pd.read_csv("ratings.csv")

# Prepare data for surprise
reader = Reader(rating_scale=(ratings.rating.min(), ratings.rating.max()))
data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)

# Train SVD model
trainset = data.build_full_trainset()
model = SVD()
model.fit(trainset)

# Save trained model
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)
