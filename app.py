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
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Movie Details", "User Details", "Top Rated Movies", "Rate Movies", "Similar Movies"])

# Fetch all movie titles for autocomplete
try:
    movies_resp = requests.get(f"{BACKEND_URL}/top-rated?n=2000", timeout=10)
    movies_resp.raise_for_status()
    movie_titles = [m["title"] for m in movies_resp.json()]
except Exception:
    movie_titles = []

# ---------------------------
# Home Page
# ---------------------------
if page == "Home":
    st.title("Personalized Movie Recommender")
    st.write("Select a section from the sidebar to get started.")

# ---------------------------
# Movie Details
# ---------------------------
elif page == "Movie Details":
    st.header("Movie Details")
    movie_choice = st.selectbox("Select a movie by title", options=movie_titles)
    
    if movie_choice:
        # Find movie ID
        try:
            movie_data_resp = requests.get(f"{BACKEND_URL}/top-rated?n=2000", timeout=10)
            movie_data_resp.raise_for_status()
            movie_data = next((m for m in movie_data_resp.json() if m["title"] == movie_choice), None)
            if movie_data:
                movie_id = movie_data["movieId"]
                resp = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
                resp.raise_for_status()
                movie = resp.json()
                st.subheader(f"{movie['title']}")
                st.write(f"Genres: {movie.get('genres', 'N/A')}")
                st.write(f"Average Rating: {movie.get('average_rating', 'N/A')}")
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
            resp = requests.get(f"{BACKEND_URL}/users/{user_id}", timeout=10)
            resp.raise_for_status()
            user = resp.json()
            st.subheader(f"User {user['userId']}")
            st.write(f"Average Rating: {user['average_rating']}")
            st.write("Rated Movies:")
            for m in user["rated_movies"]:
                st.write(f"{m['title']} | Rating: {round(m['rating'],2)} | Genres: {m.get('genres','N/A')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user info: {e}")

# ---------------------------
# Top Rated Movies
# ---------------------------
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")
    n_top = st.slider("Number of top movies", min_value=5, max_value=50, value=10)
    
    try:
        resp = requests.get(f"{BACKEND_URL}/top-rated?n={n_top}", timeout=10)
        resp.raise_for_status()
        top_movies = resp.json()
        for m in top_movies:
            st.write(f"{m['title']} | Rating: {round(m['rating'],2)} | Genres: {m.get('genres','N/A')}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching top rated movies: {e}")

# ---------------------------
# Rate Movies (New Users)
# ---------------------------
elif page == "Rate Movies":
    st.header("Rate Movies (New User)")
    new_user_id = st.number_input("Assign a User ID", min_value=1000, step=1)
    
    ratings_input = st.text_area(
        "Enter ratings as movie_title:rating, separated by commas (e.g. Toy Story (1995):5, Jumanji (1995):4)"
    )
    top_n = st.slider("Number of recommendations", 1, 10, 5)
    
    if st.button("Get Recommendations"):
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
                    st.subheader("Top Recommendations:")
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
    st.header("Similar Movies")
    sim_movie_choice = st.selectbox("Select a movie", options=movie_titles)
    n_sim = st.slider("Number of similar movies", 1, 10, 5)
    
    if sim_movie_choice:
        try:
            # Find movie ID
            movie_data_resp = requests.get(f"{BACKEND_URL}/top-rated?n=2000", timeout=10)
            movie_data_resp.raise_for_status()
            movie_data = next((m for m in movie_data_resp.json() if m["title"] == sim_movie_choice), None)
            if movie_data:
                movie_id = movie_data["movieId"]
                resp = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={n_sim}", timeout=10)
                resp.raise_for_status()
                similar_movies = resp.json()
                st.subheader(f"Movies similar to {sim_movie_choice}:")
                for m in similar_movies:
                    st.write(f"{m['title']} | Genres: {m.get('genres','N/A')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching similar movies: {e}")
