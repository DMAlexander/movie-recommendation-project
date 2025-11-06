import os
import requests
import streamlit as st

# ============================================================
# CONFIGURATION
# ============================================================
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Movie Recommender System", layout="centered")

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Get Recommendations", "Rate Movies", "Movie Details", "Similar Movies", "Top Rated Movies"]
)

# Cache all movie data once for dropdown lists
@st.cache_data
def load_movies():
    try:
        response = requests.get(f"{BACKEND_URL}/movies/all", timeout=15)
        response.raise_for_status()
        data = response.json()
        return {movie["movieId"]: movie["title"] for movie in data}
    except Exception as e:
        st.error(f"Error loading movie list: {e}")
        return {}

movie_dict = load_movies()
movie_titles = list(movie_dict.values())

# ============================================================
# 1️⃣ GET RECOMMENDATIONS
# ============================================================
if page == "Get Recommendations":
    st.title("Get Recommendations")

    user_type = st.radio("Are you an existing or new user?", ["Existing", "New"])

    if user_type == "Existing":
        user_id = st.number_input("Enter your User ID", min_value=1, step=1)
        top_n = st.slider("Number of recommendations", 1, 10, 5)

        if st.button("Get Recommendations"):
            try:
                response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=15)
                response.raise_for_status()
                recs = response.json()
                if recs:
                    st.subheader("Top Recommendations")
                    for i, movie in enumerate(recs, 1):
                        title = movie.get("title", "Unknown Title")
                        pred = movie.get("predicted_rating", "N/A")
                        st.write(f"{i}. {title} (Predicted Rating: {round(pred, 2) if isinstance(pred, float) else pred})")
                else:
                    st.info("No recommendations found.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

    else:
        st.subheader("New User — Rate Movies to Get Recommendations")
        st.write("Enter ratings as `movie_id:rating`, separated by commas. Example: `1:5,50:3,100:4`")

        ratings_input = st.text_area("Your Ratings")
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
                    payload = {"user_id": 1000, "ratings": ratings_dict, "top_n": top_n}
                    response = requests.post(f"{BACKEND_URL}/rate/", json=payload, timeout=15)
                    response.raise_for_status()
                    recs = response.json()
                    if recs:
                        st.subheader("Top Recommendations")
                        for i, movie in enumerate(recs, 1):
                            st.write(f"{i}. {movie}")
                    else:
                        st.info("No recommendations found.")
            except Exception as e:
                st.error(f"Error fetching recommendations: {e}")

# ============================================================
# 2️⃣ RATE MOVIES
# ============================================================
elif page == "Rate Movies":
    st.title("Rate a Movie")

    user_id = st.number_input("Enter your User ID", min_value=1, step=1)
    movie_title = st.selectbox("Select a Movie", movie_titles, index=None, placeholder="Start typing a movie title...")
    rating = st.slider("Your Rating", 0.5, 5.0, 3.0, 0.5)

    if st.button("Submit Rating"):
        try:
            if not movie_title:
                st.warning("Please select a movie.")
            else:
                movie_id = next((mid for mid, title in movie_dict.items() if title == movie_title), None)
                if not movie_id:
                    st.error("Movie not found.")
                else:
                    payload = {"user_id": user_id, "movie_id": movie_id, "rating": rating}
                    response = requests.post(f"{BACKEND_URL}/rate_movie/", json=payload, timeout=15)
                    response.raise_for_status()
                    st.success("✅ Rating submitted successfully!")
        except Exception as e:
            st.error(f"Error submitting rating: {e}")

# ============================================================
# 3️⃣ MOVIE DETAILS (Lookup by Title)
# ============================================================
elif page == "Movie Details":
    st.title("Movie Details")

    movie_title = st.selectbox("Search for a Movie", movie_titles, index=None, placeholder="Start typing a movie title...")

    if movie_title:
        movie_id = next((mid for mid, title in movie_dict.items() if title == movie_title), None)
        if movie_id:
            try:
                response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=15)
                response.raise_for_status()
                movie = response.json()
                st.subheader(movie["title"])
                st.write(f"**Genres:** {movie.get('genres', 'N/A')}")
                st.write(f"**Average Rating:** {round(movie.get('average_rating', 0), 2)}")
            except Exception as e:
                st.error(f"Error fetching movie details: {e}")

# ============================================================
# 4️⃣ SIMILAR MOVIES
# ============================================================
elif page == "Similar Movies":
    st.title("Similar Movies")

    movie_title = st.selectbox("Select a Movie", movie_titles, index=None, placeholder="Start typing a movie title...")

    if movie_title:
        movie_id = next((mid for mid, title in movie_dict.items() if title == movie_title), None)
        if movie_id:
            try:
                response = requests.get(f"{BACKEND_URL}/similar/{movie_id}", timeout=15)
                response.raise_for_status()
                similar_movies = response.json()
                if similar_movies:
                    st.subheader(f"Movies similar to '{movie_title}':")
                    for i, movie in enumerate(similar_movies, 1):
                        st.write(f"{i}. {movie['title']} (Predicted Rating: {round(movie.get('predicted_rating', 0), 2)})")
                else:
                    st.info("No similar movies found.")
            except Exception as e:
                st.error(f"Error fetching similar movies: {e}")

# ============================================================
# 5️⃣ TOP RATED MOVIES
# ============================================================
elif page == "Top Rated Movies":
    st.title("Top Rated Movies")

    try:
        response = requests.get(f"{BACKEND_URL}/top-rated", timeout=15)
        response.raise_for_status()
        movies = response.json()

        if movies:
            for i, movie in enumerate(movies, 1):
                title = movie.get("title", "Unknown Title")
                genres = movie.get("genres", "N/A")
                avg_rating = round(movie.get("average_rating", 0), 2)
                st.write(f"{i}. **{title}** — Genre: {genres} | Rating: {avg_rating}")
        else:
            st.info("No top-rated movies found.")
    except Exception as e:
        st.error(f"Error fetching top-rated movies: {e}")
