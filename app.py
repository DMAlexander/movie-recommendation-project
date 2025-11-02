# app.py
import os
import re
import streamlit as st
import requests
import pandas as pd

# Backend URL (Render)
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Load local movies data (optional, for genre lookup)
MOVIES_PATH = "data/movies.csv"
if os.path.exists(MOVIES_PATH):
    movies = pd.read_csv(MOVIES_PATH)
else:
    movies = pd.DataFrame(columns=["movieId", "title", "genres"])

# Ensure consistent column names
movies.columns = [c.strip() for c in movies.columns]

# If one-hot genre columns exist, combine them into a single 'genres' column
genre_columns = [c for c in movies.columns if c not in ["movieId", "title", "genres"]]
if genre_columns and not "genres" in movies.columns:
    movies["genres"] = movies[genre_columns].apply(
        lambda row: "|".join([col for col in genre_columns if row[col] == 1]), axis=1
    )

st.set_page_config(page_title="Personalized Movie Recommender", layout="centered")
st.title("Personalized Movie Recommender")

user_type = st.radio("Are you an existing user or new user?", ["Existing", "New"])


def display_recommendations(recs):
    """Show recommended movies with title, genres, and predicted rating."""
    for i, movie in enumerate(recs, 1):
        title = movie.get("title", "N/A")
        movie_id = movie.get("movieId", None)
        predicted_rating = movie.get("predicted_rating", "N/A")

        # Extract year if present in title
        match = re.search(r"\((\d{4})\)", title)
        year = match.group(1) if match else "N/A"

        # Get genres
        genres = "N/A"
        if movie_id is not None and not movies.empty:
            row = movies[movies["movieId"] == movie_id]
            if not row.empty:
                genres = row.iloc[0].get("genres", "N/A")
                if not isinstance(genres, str) or not genres.strip():
                    genres = "N/A"

        # Clean up title: remove year in parentheses if present
        clean_title = re.sub(r"\s*\(\d{4}\)", "", title)

        st.write(f"{i}. {clean_title} ({year}) — Genres: {genres} — Predicted Rating: {predicted_rating:.2f}")


# ---------------- Existing Users ----------------
if user_type == "Existing":
    user_id = st.number_input("Enter your User ID", min_value=1, step=1)
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Get Recommendations"):
        try:
            response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
            response.raise_for_status()
            recs = response.json()

            if recs:
                st.subheader("Top Recommendations:")
                display_recommendations(recs)
            else:
                st.warning("No recommendations found for this user.")

        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")


# ---------------- New Users ----------------
else:
    st.write("Rate a few movies to get personalized recommendations")
    st.write("Use Movie IDs from 1 to 1682 (MovieLens 100k)")

    ratings_input = st.text_area(
        "Enter ratings as movie_id:rating, separated by commas (e.g. 1:5,50:3,100:4)"
    )
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Get Recommendations"):
        try:
            ratings_dict = {}
            for pair in ratings_input.split(","):
                if ":" in pair:
                    mid, r = pair.strip().split(":")
                    ratings_dict[int(mid)] = float(r)

            if not ratings_dict:
                st.warning("Please enter at least one valid rating.")
            else:
                payload = {"user_id": 1000, "ratings": ratings_dict, "top_n": top_n}
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                recs = response.json()

                if recs:
                    st.subheader("Top Recommendations:")
                    display_recommendations(recs)
                else:
                    st.warning("No recommendations found for your ratings.")

        except ValueError:
            st.error("Invalid input format. Use movie_id:rating, separated by commas.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")


# ---------------- Lookup Movie by ID ----------------
st.write("---")
st.subheader("Lookup Movie by ID")

movie_lookup_id = st.number_input("Enter Movie ID", min_value=1, step=1, key="lookup_id")
if st.button("Get Movie Info", key="lookup_movie"):
    try:
        response = requests.get(f"{BACKEND_URL}/movies/{movie_lookup_id}", timeout=10)
        response.raise_for_status()
        movie = response.json()

        st.write(f"**Title:** {movie.get('title', 'N/A')}")
        st.write(f"**Genres:** {movie.get('genres', 'N/A')}")
        st.write(f"**Average Rating:** {movie.get('average_rating', 'N/A')}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching movie info: {e}")
