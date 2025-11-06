# app.py
import os
import streamlit as st
import requests
from streamlit_autocomplete import st_autocomplete  # pip install streamlit-autocomplete if needed

# 🔹 Replace this with your Render backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Home",
    "Movie Details",
    "User Details",
    "Top Rated Movies",
    "Get Recommendations",  # Existing users
    "Rate Movies",          # New users
    "Similar Movies"
])

# ---------------------------
# Home
# ---------------------------
if page == "Home":
    st.title("Personalized Movie Recommender")
    st.write("Use the sidebar to navigate to different sections.")

# ---------------------------
# Movie Details
# ---------------------------
elif page == "Movie Details":
    st.header("Movie Details Lookup")
    # Autocomplete: fetch all movie titles from backend or maintain a list
    try:
        resp = requests.get(f"{BACKEND_URL}/top-rated?n=5000", timeout=10)
        resp.raise_for_status()
        movie_titles = [m["title"] for m in resp.json()]
    except:
        movie_titles = []

    movie_title = st_autocomplete("Select a movie", movie_titles)
    top_n = st.slider("Number of similar recommendations", 1, 10, 5)

    if st.button("Get Movie Details"):
        try:
            # Lookup by title first
            movie_resp = requests.get(f"{BACKEND_URL}/movies/title/{movie_title}", timeout=10)
            movie_resp.raise_for_status()
            movie = movie_resp.json()
            st.subheader(f"{movie['title']} ({movie.get('year','N/A')})")
            st.write(f"Genres: {movie.get('genres','N/A')}")
            st.write(f"Average Rating: {movie.get('average_rating','N/A')}")

            # Similar movies
            sim_resp = requests.get(f"{BACKEND_URL}/similar/{movie['movieId']}?n={top_n}", timeout=10)
            sim_resp.raise_for_status()
            similar = sim_resp.json()
            if similar:
                st.subheader("Similar Movies:")
                for i, m in enumerate(similar,1):
                    st.write(f"{i}. {m['title']} | Genres: {m.get('genres','N/A')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching movie details: {e}")

# ---------------------------
# User Details
# ---------------------------
elif page == "User Details":
    st.header("User Lookup")
    user_id = st.number_input("Enter User ID", min_value=1, step=1)
    if st.button("Get User Info"):
        try:
            resp = requests.get(f"{BACKEND_URL}/users/{user_id}", timeout=10)
            resp.raise_for_status()
            user = resp.json()
            st.write(f"User ID: {user['userId']}")
            st.write(f"Average Rating: {user['average_rating']}")
            st.subheader("Rated Movies:")
            for r in user["rated_movies"]:
                st.write(f"{r['title']} | Rating: {round(r['rating'],2)}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user info: {e}")

# ---------------------------
# Top Rated Movies
# ---------------------------
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")
    top_n = st.slider("Number of top movies to show", 1, 20, 10)
    if st.button("Show Top Rated"):
        try:
            resp = requests.get(f"{BACKEND_URL}/top-rated?n={top_n}", timeout=10)
            resp.raise_for_status()
            movies = resp.json()
            for i, m in enumerate(movies,1):
                st.write(f"{i}. {m['title']} | Rating: {round(m['rating'],2)} | Genres: {m.get('genres','N/A')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching top rated movies: {e}")

# ---------------------------
# Get Recommendations (Existing User)
# ---------------------------
elif page == "Get Recommendations":
    st.header("Get Recommendations (Existing User)")
    user_id = st.number_input("Enter your User ID", min_value=1, step=1)
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Get Recommendations"):
        try:
            resp = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
            resp.raise_for_status()
            recs = resp.json().get("recommendations", [])
            if recs:
                st.subheader("Top Recommendations:")
                for i, movie in enumerate(recs, 1):
                    st.write(f"{i}. {movie['title']} | Predicted Rating: {round(movie['predicted_rating'],2)} | Genres: {movie.get('genres','N/A')}")
            else:
                st.warning("No recommendations found for this user.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Rate Movies (New User)
# ---------------------------
elif page == "Rate Movies":
    st.header("Rate Movies (New User)")
    new_user_id = st.number_input("Assign a User ID", min_value=1000, step=1)

    ratings_input = st.text_area(
        "Enter ratings as movie_title:rating, separated by commas (e.g. Toy Story (1995):5, Jumanji (1995):4)"
    )
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Submit Ratings and Get Recommendations"):
        try:
            ratings_dict = {}
            for pair in ratings_input.split(","):
                if ":" in pair:
                    title, r = pair.strip().split(":")
                    ratings_dict[title.strip()] = float(r)
            if not ratings_dict:
                st.warning("Please enter at least one valid rating.")
            else:
                payload = {"userId": new_user_id, "ratings": ratings_dict, "top_n": top_n}
                resp = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                resp.raise_for_status()
                recs = resp.json().get("recommendations", [])
                if recs:
                    st.subheader("Top Recommendations for New User:")
                    for i, movie in enumerate(recs, 1):
                        st.write(f"{i}. {movie['title']} | Predicted Rating: {round(movie['predicted_rating'],2)} | Genres: {movie.get('genres','N/A')}")
                else:
                    st.warning("No recommendations found for your ratings.")
        except ValueError:
            st.error("Invalid input format. Use movie_title:rating, separated by commas.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# Similar Movies
# ---------------------------
elif page == "Similar Movies":
    st.header("Similar Movies Lookup")
    movie_title = st_autocomplete("Select a movie", movie_titles)
    top_n = st.slider("Number of similar movies to show", 1, 10, 5)

    if st.button("Get Similar Movies"):
        try:
            movie_resp = requests.get(f"{BACKEND_URL}/movies/title/{movie_title}", timeout=10)
            movie_resp.raise_for_status()
            movie = movie_resp.json()
            sim_resp = requests.get(f"{BACKEND_URL}/similar/{movie['movieId']}?n={top_n}", timeout=10)
            sim_resp.raise_for_status()
            similar = sim_resp.json()
            if similar:
                st.subheader(f"Movies similar to {movie['title']}:")
                for i, m in enumerate(similar, 1):
                    st.write(f"{i}. {m['title']} | Genres: {m.get('genres','N/A')}")
            else:
                st.warning("No similar movies found.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching similar movies: {e}")
