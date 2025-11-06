import os
import requests
import streamlit as st

# ----------------------------------------
# Backend URL (Render API)
# ----------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ----------------------------------------
# Page Setup
# ----------------------------------------
st.set_page_config(page_title="Movie Recommendation System", layout="centered")
st.title("Movie Recommendation System")

# ----------------------------------------
# Section 1: Top Recommendations
# ----------------------------------------
st.header("Top Recommendations")

user_id = st.number_input("Enter User ID", min_value=1, step=1)
top_n = st.slider("Number of recommendations", 1, 10, 5)

if st.button("Get Recommendations"):
    try:
        response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
        response.raise_for_status()
        recs = response.json()

        if isinstance(recs, list) and recs:
            st.subheader("Recommended Movies:")
            for i, movie in enumerate(recs, 1):
                title = movie.get("title", "Unknown")
                rating = round(movie.get("predicted_rating", 0), 2)
                st.write(f"{i}. {title} (Predicted Rating: {rating})")
        else:
            st.warning("No recommendations found for this user.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching recommendations: {e}")

# ----------------------------------------
# Section 2: Movie Details (by ID or Title)
# ----------------------------------------
st.header("Movie Details")

lookup_type = st.radio("Search by:", ["Movie ID", "Title"])

if lookup_type == "Movie ID":
    movie_id = st.number_input("Enter Movie ID", min_value=1, step=1)
    title_query = None
else:
    title_query = st.text_input("Enter Movie Title")
    movie_id = None

if st.button("Get Movie Details"):
    try:
        # If searching by title, look up top-rated list for a match
        if lookup_type == "Title" and title_query.strip():
            all_movies = requests.get(f"{BACKEND_URL}/top-rated?n=1000", timeout=10).json()
            match = next((m for m in all_movies if title_query.lower() in m["title"].lower()), None)
            if not match:
                st.warning("Movie not found. Try a different title.")
            else:
                movie_id = match["movieId"]

        if movie_id:
            response = requests.get(f"{BACKEND_URL}/movies/{int(movie_id)}", timeout=10)
            response.raise_for_status()
            movie = response.json()

            st.subheader(movie["title"])
            st.write(f"**Genre:** {movie.get('genres', 'N/A')}")
            st.write(f"**Average Rating:** {movie.get('average_rating', 'N/A')}")
        else:
            st.info("Please enter a valid Movie ID or Title.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching movie details: {e}")

# ----------------------------------------
# Section 3: User Details
# ----------------------------------------
st.header("User Details")

user_id_lookup = st.number_input("Enter User ID to View Details", min_value=1, step=1, key="user_details")

if st.button("Get User Details"):
    try:
        response = requests.get(f"{BACKEND_URL}/users/{int(user_id_lookup)}", timeout=10)
        response.raise_for_status()
        user = response.json()

        st.write(f"**User ID:** {user['userId']}")
        st.write(f"**Average Rating:** {user.get('average_rating', 'N/A')}")

        st.subheader("Rated Movies:")
        rated_movies = user.get("rated_movies", [])
        if rated_movies:
            for m in rated_movies:
                st.write(f"- {m['title']} (Rating: {m['rating']})")
        else:
            st.info("No rated movies found for this user.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching user details: {e}")

# ----------------------------------------
# Section 4: Rate Movie
# ----------------------------------------
st.header("Rate Movie")

rate_user_id = st.number_input("Your User ID", min_value=1, step=1, key="rate_user")
rate_movie_id = st.number_input("Movie ID to Rate", min_value=1, step=1)
rate_value = st.slider("Rating (1 to 5)", 1.0, 5.0, 3.0, 0.5)

if st.button("Submit Rating"):
    try:
        payload = {"userId": int(rate_user_id), "movieId": int(rate_movie_id), "rating": float(rate_value)}
        response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
        response.raise_for_status()
        st.success("Rating submitted successfully!")
    except requests.exceptions.RequestException as e:
        st.error(f"Error submitting rating: {e}")

# ----------------------------------------
# Section 5: Top-Rated Movies
# ----------------------------------------
st.header("Top-Rated Movies")

n_top = st.slider("Number of top-rated movies", 1, 20, 5, key="top_rated_slider")

if st.button("Show Top-Rated Movies"):
    try:
        response = requests.get(f"{BACKEND_URL}/top-rated?n={n_top}", timeout=10)
        response.raise_for_status()
        top_movies = response.json()

        if top_movies:
            for i, movie in enumerate(top_movies, 1):
                title = movie.get("title", "Unknown")
                rating = round(movie.get("rating", 0.0), 2)
                genre = movie.get("genres", "N/A")
                st.write(f"{i}. {title} ({genre}) — ⭐ {rating}")
        else:
            st.warning("No top-rated movies found.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching top-rated movies: {e}")

# ----------------------------------------
# Section 6: Similar Movies
# ----------------------------------------
st.header("Similar Movies")

sim_movie_id = st.number_input("Enter Movie ID to Find Similar", min_value=1, step=1, key="similar_movie")

if st.button("Get Similar Movies"):
    try:
        response = requests.get(f"{BACKEND_URL}/similar/{int(sim_movie_id)}", timeout=10)
        response.raise_for_status()
        similar_movies = response.json()

        if similar_movies:
            st.subheader("Movies similar to your selection:")
            for m in similar_movies:
                st.write(f"- {m['title']} ({m.get('genres', 'N/A')})")
        else:
            st.warning("No similar movies found.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching similar movies: {e}")
