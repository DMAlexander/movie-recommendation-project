# app.py
import os
import streamlit as st
import requests

# ---------------------------
# Backend URL
# ---------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(page_title="Personalized Movie Recommender", layout="centered")

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.sidebar.title("Movie Recommender")
page = st.sidebar.radio("Choose a page", [
    "Get Recommendations", 
    "Rate Movies", 
    "Movie Details", 
    "User Details", 
    "Top Rated Movies", 
    "Similar Movies"
])

# ---------------------------
# Helper to fetch all movies for dropdown/autocomplete
# ---------------------------
@st.cache_data
def fetch_all_movies():
    try:
        response = requests.get(f"{BACKEND_URL}/movies/all", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        st.error("Error loading movie list from backend")
        return []

all_movies = fetch_all_movies()
movie_titles = [m["title"] for m in all_movies]

# ---------------------------
# Page: Get Recommendations
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
            if recs:
                st.subheader("Top Recommendations:")
                for i, movie in enumerate(recs, 1):
                    st.write(f"{i}. {movie['title']} ({movie.get('genres', 'N/A')}) - Predicted Rating: {round(movie.get('predicted_rating', 0), 2)}")
            else:
                st.warning("No recommendations found for this user.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Page: Rate Movies (New User)
# ---------------------------
elif page == "Rate Movies":
    st.header("Rate Movies (New User)")
    st.write("Rate some movies to get personalized recommendations")

    selected_movies = st.multiselect("Select movies to rate", movie_titles)
    ratings_input = {}
    for movie in selected_movies:
        rating = st.slider(f"Rating for {movie}", 1, 5, 3)
        ratings_input[movie] = rating

    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Get Recommendations"):
        if not ratings_input:
            st.warning("Please select at least one movie to rate.")
        else:
            payload = {
                "user_id": 1000,  # temporary new user ID
                "ratings": {m["movieId"]: r for m, r in zip(selected_movies, ratings_input.values())},
                "top_n": top_n
            }
            try:
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                recs = response.json().get("recommendations", [])
                if recs:
                    st.subheader("Top Recommendations:")
                    for i, movie in enumerate(recs, 1):
                        st.write(f"{i}. {movie['title']} ({movie.get('genres', 'N/A')}) - Predicted Rating: {round(movie.get('predicted_rating', 0), 2)}")
                else:
                    st.warning("No recommendations found for your ratings.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Page: Movie Details
# ---------------------------
elif page == "Movie Details":
    st.header("Movie Details")
    search_type = st.radio("Search by", ["ID", "Title"])
    movie_info = None

    if search_type == "ID":
        movie_id = st.number_input("Enter Movie ID", min_value=1, step=1)
        if st.button("Get Movie Info"):
            try:
                response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
                response.raise_for_status()
                movie_info = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching movie: {e}")
    else:  # Title search
        movie_title = st.text_input("Enter Movie Title", "")
        if st.button("Get Movie Info"):
            movie_match = next((m for m in all_movies if m["title"].lower() == movie_title.lower()), None)
            if movie_match:
                try:
                    response = requests.get(f"{BACKEND_URL}/movies/{movie_match['movieId']}", timeout=10)
                    response.raise_for_status()
                    movie_info = response.json()
                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching movie: {e}")
            else:
                st.warning("Movie not found.")

    if movie_info:
        st.subheader(f"{movie_info['title']} ({movie_info.get('year', 'N/A')})")
        st.write(f"Genres: {movie_info.get('genres', 'N/A')}")
        st.write(f"Average Rating: {round(movie_info.get('average_rating', 0), 2)}")

# ---------------------------
# Page: User Details
# ---------------------------
elif page == "User Details":
    st.header("User Details")
    user_id = st.number_input("Enter User ID", min_value=1, step=1)
    if st.button("Get User Info"):
        try:
            response = requests.get(f"{BACKEND_URL}/users/{user_id}", timeout=10)
            response.raise_for_status()
            user_data = response.json()
            st.write(f"User ID: {user_data['userId']}")
            st.write(f"Average Rating: {round(user_data.get('average_rating', 0), 2)}")
            st.subheader("Rated Movies:")
            for m in user_data.get("rated_movies", []):
                st.write(f"{m['title']} ({m.get('genres', 'N/A')}) - Rating: {round(m.get('rating', 0), 2)}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user info: {e}")

# ---------------------------
# Page: Top Rated Movies
# ---------------------------
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")
    top_n = st.slider("Number of top-rated movies", 1, 20, 10)
    if st.button("Get Top Rated"):
        try:
            response = requests.get(f"{BACKEND_URL}/top-rated?n={top_n}", timeout=10)
            response.raise_for_status()
            top_movies = response.json()
            for i, m in enumerate(top_movies, 1):
                st.write(f"{i}. {m['title']} ({m.get('genres', 'N/A')}) - Rating: {round(m.get('rating', 0), 2)}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching top-rated movies: {e}")

# ---------------------------
# Page: Similar Movies
# ---------------------------
elif page == "Similar Movies":
    st.header("Similar Movies")
    movie_title = st.text_input("Enter Movie Title", "")
    top_n = st.slider("Number of similar movies", 1, 10, 5)

    if st.button("Get Similar Movies"):
        movie_match = next((m for m in all_movies if m["title"].lower() == movie_title.lower()), None)
        if movie_match:
            try:
                response = requests.get(f"{BACKEND_URL}/similar/{movie_match['movieId']}?n={top_n}", timeout=10)
                response.raise_for_status()
                similar = response.json()
                if similar:
                    st.subheader(f"Movies similar to {movie_title}:")
                    for i, m in enumerate(similar, 1):
                        st.write(f"{i}. {m['title']} ({m.get('genres', 'N/A')})")
                else:
                    st.warning("No similar movies found.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching similar movies: {e}")
        else:
            st.warning("Movie not found.")
