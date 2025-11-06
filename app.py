# app.py
import os
import streamlit as st
import requests
import pandas as pd

# ---------------------------
# Backend URL
# ---------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ---------------------------
# Fetch all movies for dropdowns
# ---------------------------
@st.cache_data
def get_all_movies():
    try:
        response = requests.get(f"{BACKEND_URL}/all-movies", timeout=10)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except requests.exceptions.RequestException:
        return pd.DataFrame(columns=["movieId", "title"])

movies_df = get_all_movies()

# ---------------------------
# Page Setup
# ---------------------------
st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")
st.title("Personalized Movie Recommender")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Select a page",
    ["Get Recommendations", "Rate Movies", "Movie Details", "Top Rated Movies", "Similar Movies"]
)

# ---------------------------
# GET RECOMMENDATIONS
# ---------------------------
if page == "Get Recommendations":
    st.header("Get Recommendations")
    user_type = st.radio("Are you an existing user or new user?", ["Existing", "New"])

    if user_type == "Existing":
        user_id = st.number_input("Enter your User ID", min_value=1, step=1)
        top_n = st.slider("Number of recommendations", 1, 10, 5)

        if st.button("Get Recommendations"):
            try:
                response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
                response.raise_for_status()
                recs = response.json()  # API returns a list of dicts
                if recs:
                    st.subheader("Top Recommendations:")
                    for i, movie in enumerate(recs, 1):
                        title = movie.get("title", "Unknown")
                        rating = round(movie.get("predicted_rating", 0), 2)
                        genres = movie.get("genres", "N/A")
                        st.write(f"{i}. {title} ({genres}) - Predicted Rating: {rating}")
                else:
                    st.warning("No recommendations found for this user.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

    else:  # New user
        st.write("Rate a few movies to get personalized recommendations")
        ratings_input = st.text_area(
            "Enter ratings as movie_id:rating, separated by commas (e.g. 1:5,50:3,100:4)"
        )
        top_n = st.slider("Number of recommendations", 1, 10, 5)

        if st.button("Get Recommendations for New User"):
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
                        for i, movie in enumerate(recs, 1):
                            title = movie.get("title", "Unknown")
                            rating = round(movie.get("predicted_rating", 0), 2)
                            genres = movie.get("genres", "N/A")
                            st.write(f"{i}. {title} ({genres}) - Predicted Rating: {rating}")
                    else:
                        st.warning("No recommendations found for your ratings.")
            except ValueError:
                st.error("Invalid input format. Use movie_id:rating, separated by commas.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

# ---------------------------
# RATE MOVIES
# ---------------------------
elif page == "Rate Movies":
    st.header("Rate a Movie")
    if movies_df.empty:
        st.warning("No movies available to rate.")
    else:
        selected_movie = st.selectbox("Select a movie to rate", movies_df["title"].tolist())
        rating = st.slider("Select your rating", 1, 5, 3)
        if st.button("Submit Rating"):
            movie_id = movies_df.loc[movies_df["title"] == selected_movie, "movieId"].values[0]
            payload = {"userId": 1000, "movieId": int(movie_id), "rating": rating}
            try:
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                st.success("Rating submitted successfully!")
            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting rating: {e}")

# ---------------------------
# MOVIE DETAILS
# ---------------------------
elif page == "Movie Details":
    st.header("Movie Details")
    if movies_df.empty:
        st.warning("No movies available.")
    else:
        selected_movie = st.selectbox("Select a movie", movies_df["title"].tolist())
        movie_id = movies_df.loc[movies_df["title"] == selected_movie, "movieId"].values[0]
        try:
            response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
            response.raise_for_status()
            movie = response.json()
            st.write(f"**Title:** {movie.get('title', 'N/A')}")
            st.write(f"**Genres:** {movie.get('genres', 'N/A')}")
            st.write(f"**Average Rating:** {round(movie.get('average_rating', 0),2)}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching movie details: {e}")

# ---------------------------
# TOP RATED MOVIES
# ---------------------------
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")
    n = st.slider("Number of top-rated movies to display", 5, 20, 10)
    try:
        response = requests.get(f"{BACKEND_URL}/top-rated?n={n}", timeout=10)
        response.raise_for_status()
        top_movies = response.json()
        if top_movies:
            for i, movie in enumerate(top_movies, 1):
                title = movie.get("title", "Unknown")
                rating = round(movie.get("rating", 0), 2)
                genres = movie.get("genres", "N/A")
                st.write(f"{i}. {title} ({genres}) - Rating: {rating}")
        else:
            st.warning("No top-rated movies found.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching top-rated movies: {e}")

# ---------------------------
# SIMILAR MOVIES
# ---------------------------
elif page == "Similar Movies":
    st.header("Similar Movies")
    if movies_df.empty:
        st.warning("No movies available.")
    else:
        selected_movie = st.selectbox("Select a movie", movies_df["title"].tolist())
        n_sim = st.slider("Number of similar movies to display", 1, 10, 5)
        movie_id = movies_df.loc[movies_df["title"] == selected_movie, "movieId"].values[0]
        try:
            response = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={n_sim}", timeout=10)
            response.raise_for_status()
            similar_movies = response.json()
            if similar_movies:
                st.subheader(f"Movies similar to {selected_movie}:")
                for i, movie in enumerate(similar_movies, 1):
                    title = movie.get("title", "Unknown")
                    genres = movie.get("genres", "N/A")
                    st.write(f"{i}. {title} ({genres})")
            else:
                st.warning("No similar movies found.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching similar movies: {e}")
