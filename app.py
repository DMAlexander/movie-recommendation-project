import os
import streamlit as st
import requests
import pandas as pd

# ---------------------------
# Backend URL
# ---------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")
st.title("Personalized Movie Recommender")

# ---------------------------
# Fetch all movie titles for autocomplete
# ---------------------------
try:
    response = requests.get(f"{BACKEND_URL}/movies_list", timeout=10)
    response.raise_for_status()
    all_movies = response.json()  # expects list of {"movieId": int, "title": str}
    movie_titles = [m["title"] for m in all_movies]
except requests.exceptions.RequestException:
    movie_titles = []

# ---------------------------
# Sidebar Navigation
# ---------------------------
page = st.sidebar.selectbox(
    "Navigation",
    [
        "Get Recommendations",
        "Rate Movies",
        "Movie Details",
        "User Details",
        "Top Rated Movies",
        "Similar Movies"
    ]
)

# ---------------------------
# Get Recommendations
# ---------------------------
if page == "Get Recommendations":
    st.header("Get Recommendations")

    user_type = st.radio("User Type", ["Existing", "New"])

    if user_type == "Existing":
        user_id = st.number_input("Enter your User ID", min_value=1, step=1)
        top_n = st.slider("Number of recommendations", 1, 10, 5)

        if st.button("Get Recommendations"):
            try:
                response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
                response.raise_for_status()
                recs = response.json().get("recommendations", [])
                if recs:
                    st.subheader("Top Recommendations:")
                    for i, movie in enumerate(recs, 1):
                        st.write(f"{i}. {movie['title']} ({movie.get('genres','N/A')}) - Predicted Rating: {movie['predicted_rating']:.2f}")
                else:
                    st.warning("No recommendations found for this user.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

    else:  # New user
        st.write("Rate a few movies to get personalized recommendations")
        ratings_input = {}
        for _ in range(3):  # Allow user to rate 3 movies initially
            selected_movie = st.selectbox("Select a Movie", [""] + movie_titles, key=f"new_movie_{_}")
            if selected_movie:
                rating = st.slider(f"Rating for {selected_movie}", 1.0, 5.0, 3.0, key=f"rating_{_}")
                movie_id = next((m["movieId"] for m in all_movies if m["title"] == selected_movie), None)
                if movie_id:
                    ratings_input[movie_id] = rating

        top_n = st.slider("Number of recommendations", 1, 10, 5)

        if st.button("Get Recommendations (New User)"):
            if not ratings_input:
                st.warning("Please rate at least one movie.")
            else:
                try:
                    payload = {"new_ratings": ratings_input}
                    response = requests.get(f"{BACKEND_URL}/recommend/1000?n={top_n}", params=payload, timeout=10)
                    response.raise_for_status()
                    recs = response.json().get("recommendations", [])
                    if recs:
                        st.subheader("Top Recommendations:")
                        for i, movie in enumerate(recs, 1):
                            st.write(f"{i}. {movie['title']} ({movie.get('genres','N/A')}) - Predicted Rating: {movie['predicted_rating']:.2f}")
                    else:
                        st.warning("No recommendations found.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Rate Movies
# ---------------------------
elif page == "Rate Movies":
    st.header("Rate a Movie")
    selected_movie = st.selectbox("Select Movie", [""] + movie_titles)
    if selected_movie:
        movie_id = next((m["movieId"] for m in all_movies if m["title"] == selected_movie), None)
        rating = st.slider("Rating", 1.0, 5.0, 3.0)
        user_id = st.number_input("User ID", min_value=1, step=1)
        if st.button("Submit Rating"):
            payload = {"userId": user_id, "movieId": movie_id, "rating": rating}
            try:
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                st.success(f"Rating submitted: {rating} stars for {selected_movie}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting rating: {e}")

# ---------------------------
# Movie Details
# ---------------------------
elif page == "Movie Details":
    st.header("Movie Details")
    selected_movie = st.selectbox("Select Movie", [""] + movie_titles)
    if selected_movie and st.button("Get Movie Details"):
        movie_id = next((m["movieId"] for m in all_movies if m["title"] == selected_movie), None)
        try:
            response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
            response.raise_for_status()
            movie = response.json()
            st.write(f"Title: {movie['title']}")
            st.write(f"Genres: {movie.get('genres','N/A')}")
            st.write(f"Average Rating: {movie.get('average_rating','N/A')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching movie: {e}")

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
            user = response.json()
            st.write(f"User ID: {user['userId']}")
            st.write(f"Average Rating: {user['average_rating']}")
            st.subheader("Rated Movies:")
            for m in user["rated_movies"]:
                st.write(f"{m['title']} - Rating: {m['rating']:.2f}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user info: {e}")

# ---------------------------
# Top Rated Movies
# ---------------------------
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")
    top_n = st.slider("Number of top movies", 1, 20, 10)
    if st.button("Get Top Rated Movies"):
        try:
            response = requests.get(f"{BACKEND_URL}/top-rated?n={top_n}", timeout=10)
            response.raise_for_status()
            movies_list = response.json()
            for i, movie in enumerate(movies_list, 1):
                st.write(f"{i}. {movie['title']} ({movie.get('genres','N/A')}) - Rating: {movie['rating']:.2f}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching top rated movies: {e}")

# ---------------------------
# Similar Movies
# ---------------------------
elif page == "Similar Movies":
    st.header("Find Similar Movies")
    selected_movie = st.selectbox("Select Movie", [""] + movie_titles)
    top_n = st.slider("Number of similar movies", 1, 10, 5)
    if selected_movie and st.button("Get Similar Movies"):
        movie_id = next((m["movieId"] for m in all_movies if m["title"] == selected_movie), None)
        try:
            response = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={top_n}", timeout=10)
            response.raise_for_status()
            sim_movies = response.json()
            for i, movie in enumerate(sim_movies, 1):
                st.write(f"{i}. {movie['title']} ({movie.get('genres','N/A')})")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching similar movies: {e}")
