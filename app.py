import os
import streamlit as st
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")

# Sidebar pages
page = st.sidebar.selectbox("Choose a page", [
    "Existing User Recommendations",
    "New User Ratings",
    "Movie Details",
    "Top Rated Movies",
    "Similar Movies"
])

# ---------------------------
# Existing User Recommendations
# ---------------------------
if page == "Existing User Recommendations":
    st.header("Get Recommendations for Existing User")
    user_id = st.number_input("Enter your User ID", min_value=1, step=1)
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Get Recommendations"):
        try:
            response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
            response.raise_for_status()
            recs = response.json()
            if recs:
                st.subheader("Top Recommendations:")
                for i, movie in enumerate(recs, 1):
                    st.write(f"{i}. {movie['title']} ({movie['genres']}) - Predicted Rating: {movie['predicted_rating']:.2f}")
            else:
                st.warning("No recommendations found for this user.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# New User Ratings
# ---------------------------
elif page == "New User Ratings":
    st.header("Submit Ratings for New User")
    ratings_input = st.text_area("Enter ratings as movie_id:rating, separated by commas (e.g. 1:5,50:3,100:4)")
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
                payload = {"userId": 1000, "ratings": ratings_dict, "top_n": top_n}
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                recs = response.json().get("recommendations", [])
                if recs:
                    st.subheader("Top Recommendations:")
                    for i, movie in enumerate(recs, 1):
                        st.write(f"{i}. {movie['title']} ({movie['genres']}) - Predicted Rating: {movie['predicted_rating']:.2f}")
                else:
                    st.warning("No recommendations found for your ratings.")
        except ValueError:
            st.error("Invalid input format. Use movie_id:rating, separated by commas.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Movie Details
# ---------------------------
elif page == "Movie Details":
    st.header("Get Movie Details")
    movie_id = st.number_input("Enter Movie ID", min_value=1, step=1)
    if st.button("Get Movie Details"):
        try:
            response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
            response.raise_for_status()
            movie = response.json()
            st.write(f"Title: {movie['title']}")
            st.write(f"Genres: {movie['genres']}")
            st.write(f"Average Rating: {movie['average_rating']}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching movie details: {e}")

# ---------------------------
# Top Rated Movies
# ---------------------------
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")
    n = st.slider("Number of movies", 1, 20, 10)
    if st.button("Get Top Rated Movies"):
        try:
            response = requests.get(f"{BACKEND_URL}/top-rated?n={n}", timeout=10)
            response.raise_for_status()
            top_movies = response.json()
            for i, movie in enumerate(top_movies, 1):
                st.write(f"{i}. {movie['title']} ({movie['genres']}) - Rating: {movie['rating']:.2f}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching top rated movies: {e}")

# ---------------------------
# Similar Movies
# ---------------------------
elif page == "Similar Movies":
    st.header("Find Similar Movies")
    movie_id = st.number_input("Enter Movie ID to find similar movies", min_value=1, step=1)
    n = st.slider("Number of similar movies", 1, 10, 5)

    if st.button("Get Similar Movies"):
        try:
            response = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={n}", timeout=10)
            response.raise_for_status()
            similar = response.json()
            for i, movie in enumerate(similar, 1):
                st.write(f"{i}. {movie['title']} ({movie['genres']})")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching similar movies: {e}")
