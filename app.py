# app.py
import os
import streamlit as st
import requests

# ---------------------------
# Backend URL
# ---------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")
st.title("Personalized Movie Recommender")

# ---------------------------
# Helper functions
# ---------------------------
@st.cache_data(show_spinner=False)
def fetch_movies_list():
    try:
        response = requests.get(f"{BACKEND_URL}/top-rated?n=2000", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

# ---------------------------
# Sidebar Navigation
# ---------------------------
page = st.sidebar.selectbox(
    "Navigate",
    [
        "Top Recommendations",
        "Movie Details",
        "User Info",
        "Rate Movie",
        "Top Rated Movies",
        "Similar Movies"
    ]
)

# ---------------------------
# Top Recommendations
# ---------------------------
if page == "Top Recommendations":
    st.header("Top Recommendations")
    user_id = st.number_input("Enter your User ID", min_value=1, step=1)
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Get Recommendations"):
        try:
            response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
            response.raise_for_status()
            recs = response.json()
            if recs:
                st.subheader("Recommended Movies:")
                for i, movie in enumerate(recs, 1):
                    title = movie.get("title", "Unknown")
                    genres = movie.get("genres", "N/A")
                    avg = round(movie.get("predicted_rating", 0), 2)
                    st.write(f"{i}. {title} — {genres} — ⭐ {avg}")
            else:
                st.warning("No recommendations found for this user.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Movie Details
# ---------------------------
elif page == "Movie Details":
    st.header("Movie Details")
    movies = fetch_movies_list()
    titles = [movie["title"] for movie in movies]

    search_mode = st.radio("Search by:", ["Title", "Movie ID"])

    if search_mode == "Title":
        user_input = st.text_input("Type part of the movie title:")
        filtered_titles = [t for t in titles if user_input.lower() in t.lower()]
        selected_title = st.selectbox("Select a movie:", filtered_titles) if filtered_titles else None

        if selected_title and st.button("Get Details"):
            selected_movie = next((m for m in movies if m["title"] == selected_title), None)
            if selected_movie:
                st.json(selected_movie)
            else:
                st.warning("Movie not found.")

    else:
        movie_id = st.number_input("Enter Movie ID", min_value=1, step=1)
        if st.button("Get Details"):
            try:
                response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
                response.raise_for_status()
                st.json(response.json())
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching movie details: {e}")

# ---------------------------
# User Info
# ---------------------------
elif page == "User Info":
    st.header("User Information")
    user_id = st.number_input("Enter User ID", min_value=1, step=1)

    if st.button("Get User Info"):
        try:
            response = requests.get(f"{BACKEND_URL}/users/{user_id}", timeout=10)
            response.raise_for_status()
            user_data = response.json()
            st.json(user_data)
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user info: {e}")

# ---------------------------
# Rate Movie
# ---------------------------
elif page == "Rate Movie":
    st.header("Rate a Movie")
    movies = fetch_movies_list()
    titles = [movie["title"] for movie in movies]

    user_id = st.number_input("Your User ID", min_value=1, step=1)
    movie_input = st.text_input("Type movie title to rate:")
    filtered_titles = [t for t in titles if movie_input.lower() in t.lower()]
    selected_title = st.selectbox("Select movie:", filtered_titles) if filtered_titles else None

    rating = st.slider("Your Rating", 1, 5, 3)

    if st.button("Submit Rating") and selected_title:
        selected_movie = next((m for m in movies if m["title"] == selected_title), None)
        if selected_movie:
            payload = {
                "userId": user_id,
                "movieId": selected_movie["movieId"],
                "rating": rating
            }
            try:
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                st.success("Rating submitted successfully!")
            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting rating: {e}")

# ---------------------------
# Top Rated Movies
# ---------------------------
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")
    top_n = st.slider("Number of movies to show", 1, 50, 10)

    movies = fetch_movies_list()
    sorted_movies = sorted(movies, key=lambda x: x.get("average_rating", 0), reverse=True)[:top_n]

    for i, movie in enumerate(sorted_movies, 1):
        title = movie.get("title", "Unknown")
        genres = movie.get("genres", "N/A")
        avg = round(movie.get("average_rating", 0), 2)
        st.write(f"{i}. {title} — {genres} — ⭐ {avg}")

# ---------------------------
# Similar Movies
# ---------------------------
elif page == "Similar Movies":
    st.header("Similar Movies")
    movies = fetch_movies_list()
    titles = [movie["title"] for movie in movies]

    user_input = st.text_input("Type a movie title:")
    filtered_titles = [t for t in titles if user_input.lower() in t.lower()]
    selected_title = st.selectbox("Select a movie:", filtered_titles) if filtered_titles else None
    top_n = st.slider("Number of similar movies", 1, 10, 5)

    if selected_title and st.button("Find Similar Movies"):
        selected_movie = next((m for m in movies if m["title"] == selected_title), None)
        if selected_movie:
            movie_id = selected_movie.get("movieId")
            try:
                response = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={top_n}", timeout=10)
                response.raise_for_status()
                similar_movies = response.json()
                if similar_movies:
                    st.subheader("Similar Movies:")
                    for i, movie in enumerate(similar_movies, 1):
                        title = movie.get("title", "Unknown")
                        genres = movie.get("genres", "N/A")
                        avg = round(movie.get("average_rating", 0), 2)
                        st.write(f"{i}. {title} — {genres} — ⭐ {avg}")
                else:
                    st.warning("No similar movies found.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching similar movies: {e}")
