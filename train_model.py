# train_model.py
import pandas as pd
from surprise import SVD, Dataset, Reader, accuracy
from surprise.model_selection import train_test_split, GridSearchCV
import pickle
import os

# ---------------------------
# Load MovieLens ratings
# ---------------------------
ratings = pd.read_csv("data/ratings.csv")

# ---------------------------
# Prepare data for Surprise
# ---------------------------
reader = Reader(rating_scale=(ratings.rating.min(), ratings.rating.max()))
data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)

# ---------------------------
# Split into train/test
# ---------------------------
trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

# ---------------------------
# Optional: Hyperparameter tuning
# ---------------------------
param_grid = {
    'n_factors': [50, 100, 150],      # latent factors
    'n_epochs': [20, 30],             # number of SGD iterations
    'lr_all': [0.002, 0.005],         # learning rate
    'reg_all': [0.02, 0.05]           # regularization
}

gs = GridSearchCV(SVD, param_grid, measures=['rmse'], cv=3, joblib_verbose=1)
gs.fit(data)  # Grid search uses CV on full dataset

print("Best RMSE:", gs.best_score['rmse'])
print("Best hyperparameters:", gs.best_params['rmse'])

# Use best hyperparameters
best_params = gs.best_params['rmse']
model = SVD(
    n_factors=best_params['n_factors'],
    n_epochs=best_params['n_epochs'],
    lr_all=best_params['lr_all'],
    reg_all=best_params['reg_all']
)

# ---------------------------
# Train final model on full training set
# ---------------------------
model.fit(trainset)

# ---------------------------
# Evaluate on test set
# ---------------------------
predictions = model.test(testset)
rmse = accuracy.rmse(predictions)
mae = accuracy.mae(predictions)
print(f"Test RMSE: {rmse:.4f}, MAE: {mae:.4f}")

# ---------------------------
# Save trained model
# ---------------------------
os.makedirs("model", exist_ok=True)
with open("model/trained_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model saved to model/model.pkl")
