# app.py
import os
import streamlit as st
import requests

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")

# ---------------------------
# Sidebar navigation
# ---------------------------
page = st.sidebar.selectbox(
    "Choose a page",
    [
        "Get Recommendations",
        "New User Ratings",
        "Movie Details",
        "Top-Rated Movies",
        "Rate Movie",
        "Similar Movies"
    ]
)

# ---------------------------
# Helper function to fetch movies list for autocomplete
# ---------------------------
@st.cache_data
def get_all_movies():
    try:
        response = requests.get(f"{BACKEND_URL}/top-rated?n=2000", timeout=10)
        response.raise_for_status()
        return [movie["title"] for movie in response.json()]
    except:
        return []

all_movies = get_all_movies()

# ---------------------------
# GET RECOMMENDATIONS - Existing Users
# ---------------------------
if page == "Get Recommendations":
    st.header("Get Recommendations for Existing Users")
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
                    st.write(f"{i}. {movie['title']} ({movie.get('genres', 'N/A')}) - Predicted Rating: {movie['predicted_rating']}")
            else:
                st.warning("No recommendations found for this user.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# NEW USER RATINGS
# ---------------------------
elif page == "New User Ratings":
    st.header("Rate Movies as a New User")
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
                payload = {"userId": 1000, "ratings": ratings_dict, "top_n": top_n}
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                recs = response.json().get("recommendations", [])
                if recs:
                    st.subheader("Top Recommendations:")
                    for i, movie in enumerate(recs, 1):
                        st.write(f"{i}. {movie['title']} ({movie.get('genres', 'N/A')}) - Predicted Rating: {movie['predicted_rating']}")
                else:
                    st.warning("No recommendations found for your ratings.")
        except ValueError:
            st.error("Invalid input format. Use movie_id:rating, separated by commas.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# MOVIE DETAILS
# ---------------------------
elif page == "Movie Details":
    st.header("Lookup Movie Details")
    selected_movie = st.selectbox("Search by movie title", all_movies)

    if selected_movie:
        try:
            # First get movieId
            movie_id = None
            response_top = requests.get(f"{BACKEND_URL}/top-rated?n=2000", timeout=10)
            response_top.raise_for_status()
            for m in response_top.json():
                if m["title"] == selected_movie:
                    movie_id = m["movieId"]
                    break

            if movie_id is None:
                st.warning("Movie not found.")
            else:
                response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
                response.raise_for_status()
                movie = response.json()
                st.write(f"**Title:** {movie['title']}")
                st.write(f"**Genres:** {movie.get('genres', 'N/A')}")
                st.write(f"**Year:** {movie.get('year', 'N/A')}")
                st.write(f"**Average Rating:** {movie.get('average_rating', 'N/A')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching movie: {e}")

# ---------------------------
# TOP-RATED MOVIES
# ---------------------------
elif page == "Top-Rated Movies":
    st.header("Top-Rated Movies")
    top_n = st.slider("Number of top-rated movies", 1, 20, 10)

    try:
        response = requests.get(f"{BACKEND_URL}/top-rated?n={top_n}", timeout=10)
        response.raise_for_status()
        movies_list = response.json()
        for i, movie in enumerate(movies_list, 1):
            st.write(f"{i}. {movie['title']} ({movie.get('genres', 'N/A')}) - Rating: {movie['rating']}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching top-rated movies: {e}")

# ---------------------------
# RATE MOVIE
# ---------------------------
elif page == "Rate Movie":
    st.header("Rate a Movie")
    movie_to_rate = st.selectbox("Select movie", all_movies)
    rating = st.slider("Your rating", 1.0, 5.0, 3.0)

    if st.button("Submit Rating"):
        try:
            # Get movieId
            movie_id = None
            response_top = requests.get(f"{BACKEND_URL}/top-rated?n=2000", timeout=10)
            response_top.raise_for_status()
            for m in response_top.json():
                if m["title"] == movie_to_rate:
                    movie_id = m["movieId"]
                    break

            if movie_id is None:
                st.warning("Movie not found.")
            else:
                payload = {"userId": 1000, "movieId": movie_id, "rating": rating}
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                st.success(f"Rating submitted for '{movie_to_rate}' successfully!")
        except requests.exceptions.RequestException as e:
            st.error(f"Error submitting rating: {e}")

# ---------------------------
# SIMILAR MOVIES
# ---------------------------
elif page == "Similar Movies":
    st.header("Find Similar Movies")
    selected_movie = st.selectbox("Select movie", all_movies)
    top_n = st.slider("Number of similar movies", 1, 10, 5)

    if st.button("Get Similar Movies"):
        try:
            movie_id = None
            response_top = requests.get(f"{BACKEND_URL}/top-rated?n=2000", timeout=10)
            response_top.raise_for_status()
            for m in response_top.json():
                if m["title"] == selected_movie:
                    movie_id = m["movieId"]
                    break

            if movie_id is None:
                st.warning("Movie not found.")
            else:
                response = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={top_n}", timeout=10)
                response.raise_for_status()
                movies_list = response.json()
                for i, movie in enumerate(movies_list, 1):
                    st.write(f"{i}. {movie['title']} ({movie.get('genres', 'N/A')})")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching similar movies: {e}")
