# app.py
import os
import streamlit as st
import requests

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "https://movie-recommendation-project-1-8xns.onrender.com")

# ---------------------------
# Streamlit Page Config
# ---------------------------
st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.sidebar.title("Menu")
page = st.sidebar.radio(
    "Go to",
    ["Home", "Get Recommendations", "Rate Movie", "Top Rated Movies", "Movie Details", "Similar Movies", "User Info"]
)

# ---------------------------
# Helper: Load all movies for autocomplete
# ---------------------------
@st.cache_data
def load_movies():
    try:
        response = requests.get(f"{BACKEND_URL}/movies/all", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading movie list: {e}")
        return []

movies_list = load_movies()
movie_titles = [movie["title"] for movie in movies_list]

# ---------------------------
# Home Page
# ---------------------------
if page == "Home":
    st.title("Personalized Movie Recommender")
    st.write("Use the sidebar to navigate between pages.")

# ---------------------------
# Get Recommendations
# ---------------------------
elif page == "Get Recommendations":
    st.title("Get Movie Recommendations")

    user_type = st.radio("Are you an existing user or new user?", ["Existing", "New"])

    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if user_type == "Existing":
        user_id = st.number_input("Enter your User ID", min_value=1, step=1)

        if st.button("Get Recommendations"):
            try:
                response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
                response.raise_for_status()
                recs = response.json()
                if recs:
                    st.subheader("Top Recommendations")
                    for i, movie in enumerate(recs, 1):
                        st.write(f"{i}. {movie['title']} (Predicted Rating: {movie['predicted_rating']:.2f}, Genres: {movie.get('genres','N/A')})")
                else:
                    st.warning("No recommendations found for this user.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

    else:  # New User
        st.write("Rate a few movies to get personalized recommendations")
        st.write("Use the movie dropdown or enter IDs manually.")

        ratings_input = st.text_area(
            "Enter ratings as movie_id:rating, separated by commas (e.g. 1:5,50:3,100:4)"
        )

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
                        st.subheader("Top Recommendations")
                        for i, movie in enumerate(recs, 1):
                            st.write(f"{i}. {movie['title']} (Predicted Rating: {movie['predicted_rating']:.2f}, Genres: {movie.get('genres','N/A')})")
                    else:
                        st.warning("No recommendations found for your ratings.")
            except ValueError:
                st.error("Invalid input format. Use movie_id:rating, separated by commas.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Rate Movie
# ---------------------------
elif page == "Rate Movie":
    st.title("Rate a Movie")

    selected_movie = st.selectbox("Select a movie to rate", movie_titles)
    rating = st.slider("Your rating", 1, 5, 3)

    if st.button("Submit Rating"):
        movie_id = next((m["movieId"] for m in movies_list if m["title"] == selected_movie), None)
        if movie_id:
            payload = {"userId": 1000, "movieId": movie_id, "rating": rating}
            try:
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                st.success(f"Rating submitted for '{selected_movie}': {rating}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting rating: {e}")
        else:
            st.warning("Movie not found.")

# ---------------------------
# Top Rated Movies
# ---------------------------
elif page == "Top Rated Movies":
    st.title("Top Rated Movies")
    top_n = st.slider("Number of movies to display", 1, 20, 10)

    try:
        response = requests.get(f"{BACKEND_URL}/top-rated?n={top_n}", timeout=10)
        response.raise_for_status()
        top_movies = response.json()
        for i, movie in enumerate(top_movies, 1):
            st.write(f"{i}. {movie['title']} (Rating: {movie['rating']:.2f}, Genres: {movie.get('genres','N/A')})")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching top rated movies: {e}")

# ---------------------------
# Movie Details
# ---------------------------
elif page == "Movie Details":
    st.title("Movie Details")

    selected_movie = st.selectbox("Select a movie", movie_titles)

    if st.button("Get Movie Details"):
        movie_id = next((m["movieId"] for m in movies_list if m["title"] == selected_movie), None)
        if movie_id:
            try:
                response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
                response.raise_for_status()
                movie = response.json()
                st.write("Title:", movie["title"])
                st.write("Genres:", movie.get("genres", "N/A"))
                st.write("Average Rating:", movie.get("average_rating", "N/A"))
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching movie details: {e}")
        else:
            st.warning("Movie not found.")

# ---------------------------
# Similar Movies
# ---------------------------
elif page == "Similar Movies":
    st.title("Find Similar Movies")

    selected_movie = st.selectbox("Select a movie", movie_titles)
    top_n = st.slider("Number of similar movies", 1, 10, 5)

    if st.button("Find Similar"):
        movie_id = next((m["movieId"] for m in movies_list if m["title"] == selected_movie), None)
        if movie_id:
            try:
                response = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={top_n}", timeout=10)
                response.raise_for_status()
                similar = response.json()
                if similar:
                    st.subheader(f"Movies similar to '{selected_movie}'")
                    for i, movie in enumerate(similar, 1):
                        st.write(f"{i}. {movie['title']} (Genres: {movie.get('genres','N/A')})")
                else:
                    st.warning("No similar movies found.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching similar movies: {e}")
        else:
            st.warning("Movie not found.")

# ---------------------------
# User Info
# ---------------------------
elif page == "User Info":
    st.title("User Information")
    user_id = st.number_input("Enter User ID", min_value=1, step=1)

    if st.button("Get User Info"):
        try:
            response = requests.get(f"{BACKEND_URL}/users/{user_id}", timeout=10)
            response.raise_for_status()
            user = response.json()
            st.write(f"User ID: {user['userId']}")
            st.write(f"Average Rating: {user['average_rating']:.2f}")
            st.subheader("Rated Movies")
            for m in user["rated_movies"]:
                st.write(f"{m['title']} - Rating: {m['rating']:.2f}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user info: {e}")
