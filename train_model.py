# train_model.py
from surprise import SVD, Dataset
from surprise.model_selection import train_test_split
import pickle

# Load built-in MovieLens dataset (100k ratings)
data = Dataset.load_builtin('ml-100k')
trainset, testset = train_test_split(data, test_size=0.2)

# Train model
model = SVD()
model.fit(trainset)

# Save model for later use
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model trained and saved as model.pkl")