import os
import zipfile
import urllib.request
import pandas as pd

# ==================================================
# 1. Download MovieLens 100K dataset if not present
# ==================================================
DATA_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
DATA_DIR = "ml-100k"
ZIP_PATH = "ml-100k.zip"

if not os.path.exists(DATA_DIR):
    if not os.path.exists(ZIP_PATH):
        print("📥 Downloading MovieLens 100K dataset...")
        urllib.request.urlretrieve(DATA_URL, ZIP_PATH)
    print("📦 Extracting dataset...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall(".")
else:
    print("✅ Dataset folder already exists.")

# ==================================================
# 2. Load and convert u.data (ratings)
# ==================================================
print("🧩 Processing ratings...")
ratings = pd.read_csv(
    os.path.join(DATA_DIR, "u.data"),
    sep="\t",
    names=["userId", "movieId", "rating", "timestamp"]
)
ratings.to_csv("ratings.csv", index=False)

# ==================================================
# 3. Load and convert u.item (movies)
# ==================================================
print("🎬 Processing movies...")
movie_cols = [
    "movieId", "title", "release_date", "video_release_date",
    "imdb_url", "unknown", "Action", "Adventure", "Animation",
    "Children", "Comedy", "Crime", "Documentary", "Drama",
    "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery",
    "Romance", "Sci-Fi", "Thriller", "War", "Western"
]
movies = pd.read_csv(
    os.path.join(DATA_DIR, "u.item"),
    sep="|",
    encoding="ISO-8859-1",
    names=movie_cols,
    usecols=range(len(movie_cols))  # ignore trailing NaNs
)
movies.to_csv("movies.csv", index=False)

# ==================================================
# 4. Load and convert u.user (users)
# ==================================================
print("👤 Processing users...")
users = pd.read_csv(
    os.path.join(DATA_DIR, "u.user"),
    sep="|",
    names=["userId", "age", "gender", "occupation", "zip_code"]
)
users.to_csv("users.csv", index=False)

# ==================================================
# 5. Load and convert u.genre (genres)
# ==================================================
print("🏷️ Processing genres...")
genres = pd.read_csv(
    os.path.join(DATA_DIR, "u.genre"),
    sep="|",
    names=["genre", "genreId"],
    engine="python"
)
genres.dropna(inplace=True)  # remove trailing empty lines
genres.to_csv("genres.csv", index=False)

# ==================================================
# 6. Done
# ==================================================
print("✅ All CSVs created successfully!")
print("Generated files: ratings.csv, movies.csv, users.csv, genres.csv")
