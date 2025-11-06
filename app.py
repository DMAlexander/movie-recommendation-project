# app.py
import os
import streamlit as st
import requests

# Attempt to import streamlit_autocomplete
try:
    from streamlit_autocomplete import st_autocomplete
    AUTOCOMPLETE_AVAILABLE = True
except ImportError:
    AUTOCOMPLETE_AVAILABLE = False

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Page config
st.set_page_config(page_title="Personalized Movie Recommender", layout="centered")

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "Get Recommendations",
        "Rate Movies",
        "Movie Details",
        "Top Rated Movies",
        "Similar Movies",
        "User Details"
    ]
)

# ----------------------------
# Helper functions
# ----------------------------
def fetch_movies():
    """Fetch list of all movies from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/movies/all", timeout=10)
        response.raise_for_status()
        return response.json()  # Expecting list of dicts with 'movieId', 'title', 'genres'
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading movie list: {e}")
        return []

def display_movie_info(movie):
    st.write(f"**Title:** {movie.get('title', 'N/A')}")
    st.write(f"**Genres:** {movie.get('genres', 'N/A')}")
    st.write(f"**Year:** {movie.get('year', 'N/A')}")
    if 'average_rating' in movie and movie['average_rating'] is not None:
        st.write(f"**Average Rating:** {round(movie['average_rating'],2)}")

# Load movies for autocomplete/dropdowns
all_movies = fetch_movies()
movie_titles = [m['title'] for m in all_movies]

# ----------------------------
# Page: Get Recommendations
# ----------------------------
if page == "Get Recommendations":
    st.title("Get Recommendations")

    user_type = st.radio("Are you an existing user or new user?", ["Existing", "New"])
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if user_type == "Existing":
        user_id = st.number_input("Enter your User ID", min_value=1, step=1)
        if st.button("Get Recommendations"):
            try:
                response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
                response.raise_for_status()
                recs = response.json().get("recommendations", [])
                if recs:
                    st.subheader("Top Recommendations:")
                    for i, movie in enumerate(recs, 1):
                        st.write(f"{i}. {movie.get('title')} ({movie.get('genres','N/A')}) - Predicted Rating: {round(movie.get('predicted_rating',0),2)}")
                else:
                    st.warning("No recommendations found for this user.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")
    else:  # New user
        st.write("Rate a few movies to get personalized recommendations")
        ratings_input = {}
        if AUTOCOMPLETE_AVAILABLE:
            movie_title = st_autocomplete("Select Movie", options=movie_titles)
            rating = st.number_input("Rating (1-5)", min_value=1, max_value=5, step=1)
            if st.button("Add Rating"):
                if movie_title:
                    selected_movie = next((m for m in all_movies if m['title']==movie_title), None)
                    if selected_movie:
                        ratings_input[selected_movie['movieId']] = rating
                        st.success(f"Added {movie_title}: {rating}")
        else:
            st.write("Autocomplete not available. Use Movie IDs.")
            movie_id = st.number_input("Movie ID", min_value=1, step=1)
            rating = st.number_input("Rating (1-5)", min_value=1, max_value=5, step=1)
            if st.button("Add Rating"):
                ratings_input[movie_id] = rating

        if st.button("Get Recommendations"):
            if not ratings_input:
                st.warning("Please add at least one rating.")
            else:
                payload = {"user_id": 1000, "ratings": ratings_input, "top_n": top_n}
                try:
                    response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                    response.raise_for_status()
                    recs = response.json().get("recommendations", [])
                    if recs:
                        st.subheader("Top Recommendations:")
                        for i, movie in enumerate(recs, 1):
                            st.write(f"{i}. {movie.get('title')} ({movie.get('genres','N/A')}) - Predicted Rating: {round(movie.get('predicted_rating',0),2)}")
                    else:
                        st.warning("No recommendations found for your ratings.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching recommendations: {e}")

# ----------------------------
# Page: Rate Movies
# ----------------------------
elif page == "Rate Movies":
    st.title("Rate Movies")
    if AUTOCOMPLETE_AVAILABLE:
        movie_title = st_autocomplete("Select Movie", options=movie_titles)
        rating = st.number_input("Rating (1-5)", min_value=1, max_value=5, step=1)
        if st.button("Submit Rating"):
            if movie_title:
                selected_movie = next((m for m in all_movies if m['title']==movie_title), None)
                if selected_movie:
                    payload = {"userId": 1000, "movieId": selected_movie['movieId'], "rating": rating}
                    try:
                        response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                        response.raise_for_status()
                        st.success(f"Rating submitted for {movie_title}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error submitting rating: {e}")
    else:
        st.write("Autocomplete not available. Use Movie IDs.")
        movie_id = st.number_input("Movie ID", min_value=1, step=1)
        rating = st.number_input("Rating (1-5)", min_value=1, max_value=5, step=1)
        if st.button("Submit Rating"):
            payload = {"userId": 1000, "movieId": movie_id, "rating": rating}
            try:
                response = requests.post(f"{BACKEND_URL}/rate", json=payload, timeout=10)
                response.raise_for_status()
                st.success(f"Rating submitted for Movie ID {movie_id}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting rating: {e}")

# ----------------------------
# Page: Movie Details
# ----------------------------
elif page == "Movie Details":
    st.title("Movie Details")
    if AUTOCOMPLETE_AVAILABLE:
        movie_title = st_autocomplete("Select Movie", options=movie_titles)
        if st.button("Get Movie Details") and movie_title:
            selected_movie = next((m for m in all_movies if m['title']==movie_title), None)
            if selected_movie:
                try:
                    response = requests.get(f"{BACKEND_URL}/movies/{selected_movie['movieId']}", timeout=10)
                    response.raise_for_status()
                    movie = response.json()
                    display_movie_info(movie)
                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching movie: {e}")
    else:
        movie_id = st.number_input("Movie ID", min_value=1, step=1)
        if st.button("Get Movie Details"):
            try:
                response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
                response.raise_for_status()
                movie = response.json()
                display_movie_info(movie)
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching movie: {e}")

# ----------------------------
# Page: Top Rated Movies
# ----------------------------
elif page == "Top Rated Movies":
    st.title("Top Rated Movies")
    n = st.slider("Number of movies", 1, 20, 10)
    try:
        response = requests.get(f"{BACKEND_URL}/top-rated?n={n}", timeout=10)
        response.raise_for_status()
        movies_list = response.json()
        for movie in movies_list:
            st.write(f"{movie.get('title')} ({movie.get('genres','N/A')}) - Rating: {round(movie.get('rating',0),2)}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching top-rated movies: {e}")

# ----------------------------
# Page: Similar Movies
# ----------------------------
elif page == "Similar Movies":
    st.title("Similar Movies")
    if AUTOCOMPLETE_AVAILABLE:
        movie_title = st_autocomplete("Select Movie", options=movie_titles)
        n = st.slider("Number of similar movies", 1, 10, 5)
        if st.button("Get Similar Movies") and movie_title:
            selected_movie = next((m for m in all_movies if m['title']==movie_title), None)
            if selected_movie:
                try:
                    response = requests.get(f"{BACKEND_URL}/similar/{selected_movie['movieId']}?n={n}", timeout=10)
                    response.raise_for_status()
                    sim_movies = response.json()
                    for movie in sim_movies:
                        st.write(f"{movie.get('title')} ({movie.get('genres','N/A')})")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching similar movies: {e}")
    else:
        movie_id = st.number_input("Movie ID", min_value=1, step=1)
        n = st.slider("Number of similar movies", 1, 10, 5)
        if st.button("Get Similar Movies"):
            try:
                response = requests.get(f"{BACKEND_URL}/similar/{movie_id}?n={n}", timeout=10)
                response.raise_for_status()
                sim_movies = response.json()
                for movie in sim_movies:
                    st.write(f"{movie.get('title')} ({movie.get('genres','N/A')})")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching similar movies: {e}")

# ----------------------------
# Page: User Details
# ----------------------------
elif page == "User Details":
    st.title("User Details")
    user_id = st.number_input("Enter User ID", min_value=1, step=1)
    if st.button("Get User Details"):
        try:
            response = requests.get(f"{BACKEND_URL}/users/{user_id}", timeout=10)
            response.raise_for_status()
            user = response.json()
            st.write(f"User ID: {user.get('userId')}")
            st.write(f"Average Rating: {round(user.get('average_rating',0),2)}")
            st.subheader("Rated Movies:")
            for m in user.get('rated_movies', []):
                st.write(f"{m.get('title')} ({m.get('genres','N/A')}) - Rating: {round(m.get('rating',0),2)}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user: {e}")
