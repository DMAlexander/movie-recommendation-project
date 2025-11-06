# app.py
import os
import streamlit as st
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")

# ---------------------------
# Fetch all movies for dropdowns
# ---------------------------
@st.cache_data
def fetch_all_movies():
    try:
        response = requests.get(f"{BACKEND_URL}/movies/all", timeout=10)
        response.raise_for_status()
        movies_list = response.json()
        # Map title -> movieId
        return {movie["title"]: movie["movieId"] for movie in movies_list}
    except requests.exceptions.RequestException:
        st.error("Error loading movie list from backend.")
        return {}

all_movies = fetch_all_movies()
all_movie_titles = list(all_movies.keys())

# ---------------------------
# Sidebar for page selection
# ---------------------------
page = st.sidebar.selectbox(
    "Choose a page",
    [
        "Get Recommendations",
        "Movie Details",
        "Top Rated Movies",
        "Rate Movie",
        "Similar Movies",
        "User Details"
    ]
)

# ---------------------------
# Get Recommendations
# ---------------------------
if page == "Get Recommendations":
    st.header("Get Recommendations")
    user_id = st.number_input("Enter your User ID", min_value=1, step=1)
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Get Recommendations"):
        try:
            response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
            response.raise_for_status()
            recs = response.json()
            if isinstance(recs, list) and recs:
                st.subheader("Top Recommendations:")
                for i, movie in enumerate(recs, 1):
                    st.write(f"{i}. {movie['title']} (Predicted Rating: {movie['predicted_rating']:.2f})")
            else:
                st.warning("No recommendations found for this user.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Movie Details by ID or Title
# ---------------------------
elif page == "Movie Details":
    st.header("Movie Details")
    search_by = st.radio("Search by", ["Movie ID", "Movie Title"])

    movie_id = None
    if search_by == "Movie ID":
        movie_id = st.number_input("Enter Movie ID", min_value=1, step=1)
    else:
        movie_title = st.selectbox("Select Movie Title", [""] + all_movie_titles)
        if movie_title:
            movie_id = all_movies[movie_title]

    if st.button("Get Movie Details") and movie_id:
        try:
            response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
            response.raise_for_status()
            movie = response.json()
            st.write(f"**Title:** {movie['title']}")
            st.write(f"**Genres:** {movie.get('genres', 'N/A')}")
            st.write(f"**Year:** {movie.get('year', 'N/A')}")
            st.write(f"**Average Rating:** {movie.get('average_rating', 'N/A')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching movie details: {e}")

# ---------------------------
# Top Rated Movies
# ---------------------------
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")
    top_n = st.slider("Number of movies to display", 1, 20, 10)
    if st.button("Load Top Rated"):
        try:
            response = requests.get(f"{BACKEND_URL}/top-rated?n={top_n}", timeout=10)
            response.raise_for_status()
            top_movies = response.json()
            for i, movie in enumerate(top_movies, 1):
                st.write(
                    f"{i}. {movie['title']} | "
                    f"Genres: {movie.get('genres', 'N/A')} | "
                    f"Rating: {movie['rating']:.2f}"
                )
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching top-rated movies: {e}")

# ---------------------------
# Rate Movie
# ---------------------------
elif page == "Rate Movie":
    st.header("Rate Movie")
    movie_title = st.selectbox("Select Movie to Rate", [""] + all_movie_titles)
    rating = st.slider("Your Rating", 0.5, 5.0, 3.0, 0.5)
    user_id = st.number_input("Your User ID", min_value=1, step=1)

    if st.button("Submit Rating") and movie_title:
        movie_id = all_movies[movie_title]
        payload = {"userId": user_id, "movieId": movie_id, "rating": rating}
        try:
            response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
            response.raise_for_status()
            st.success("Rating submitted successfully!")
        except requests.exceptions.RequestException as e:
            st.error(f"Error submitting rating: {e}")

# ---------------------------
# Similar Movies
# ---------------------------
elif page == "Similar Movies":
    st.header("Similar Movies")
    movie_title = st.selectbox("Select Movie", [""] + all_movie_titles)
    top_n = st.slider("Number of similar movies", 1, 10, 5)

    if st.button("Get Similar Movies") and movie_title:
        movie_id = all_movies[movie_title]
        try:
            response = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={top_n}", timeout=10)
            response.raise_for_status()
            similar_movies = response.json()
            for i, movie in enumerate(similar_movies, 1):
                st.write(f"{i}. {movie['title']} | Genres: {movie.get('genres', 'N/A')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching similar movies: {e}")

# ---------------------------
# User Details
# ---------------------------
elif page == "User Details":
    st.header("User Details")
    user_id = st.number_input("Enter User ID", min_value=1, step=1)
    if st.button("Get User Info"):
        try:
            response = requests.get(f"{BACKEND_URL}/users/{user_id}", timeout=10)
            response.raise_for_status()
            user_info = response.json()
            st.write(f"**User ID:** {user_info['userId']}")
            st.write(f"**Average Rating:** {user_info['average_rating']}")
            st.subheader("Rated Movies")
            for movie in user_info.get("rated_movies", []):
                st.write(f"{movie['title']} | Rating: {movie['rating']}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user details: {e}")
