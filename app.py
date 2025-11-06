# app.py
import os
import requests
import pandas as pd
import streamlit as st
from streamlit_autocomplete import st_autocomplete

# ===================================
# PAGE CONFIG (must be first)
# ===================================
st.set_page_config(page_title="Movie Recommender", layout="wide")

# ===================================
# CONFIGURATION
# ===================================
BACKEND_URL = os.getenv("BACKEND_URL", "https://movie-recommendation-project-1-8xns.onrender.com")
st.title("Movie Recommendation System")

# ===================================
# SIDEBAR NAVIGATION
# ===================================
page = st.sidebar.radio(
    "Navigation",
    [
        "Get Recommendations",
        "Rate Movies",
        "Movie Details",
        "Similar Movies",
        "Top Rated Movies",
        "User Lookup"
    ]
)

# ===================================
# UTILITY FUNCTIONS
# ===================================

@st.cache_data(ttl=3600)
def fetch_movies():
    """Fetch all movie titles once and cache them for 1 hour."""
    try:
        response = requests.get(f"{BACKEND_URL}/movies/all", timeout=10)
        response.raise_for_status()
        movies = response.json()
        return {m["title"]: m["movieId"] for m in movies}
    except Exception as e:
        st.error(f"⚠️ Could not load movie list: {e}")
        return {}

def safe_get(url, **kwargs):
    """Wrapper for GET requests with safe error handling."""
    try:
        response = requests.get(url, timeout=10, **kwargs)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None

# Load movies for autocomplete
movies_dict = fetch_movies()
movie_titles = list(movies_dict.keys())


# =======================================================
# PAGE 1 — Get Recommendations
# =======================================================
if page == "Get Recommendations":
    st.header("Get Personalized Recommendations")

    user_type = st.radio("User Type", ["Existing", "New"], horizontal=True)

    if user_type == "Existing":
        user_id = st.number_input("Enter your User ID", min_value=1, step=1)
        top_n = st.slider("Number of recommendations", 1, 10, 5)

        if st.button("Get Recommendations"):
            data = safe_get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}")
            if data:
                st.subheader("Top Recommendations")
                for i, m in enumerate(data, start=1):
                    st.write(f"{i}. {m['title']} ({m.get('year', 'N/A')}) — ⭐ {round(m['predicted_rating'], 2)}")

    else:
        st.write("Rate a few movies to get personalized recommendations")

        ratings_input = st.text_area(
            "Enter ratings as movie_id:rating, separated by commas (e.g., 1:5,50:3,100:4)"
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
                    response = requests.post(f"{BACKEND_URL}/rate/", json=payload, timeout=10)
                    response.raise_for_status()
                    recs = response.json().get("recommendations", [])
                    if recs:
                        st.subheader("Top Recommendations")
                        for i, movie in enumerate(recs, 1):
                            st.write(f"{i}. {movie}")
                    else:
                        st.warning("No recommendations found.")
            except Exception as e:
                st.error(f"Error: {e}")


# =======================================================
# PAGE 2 — Rate Movies
# =======================================================
elif page == "Rate Movies":
    st.header("Rate a Movie")

    movie_title = st_autocomplete("Search Movie Title", movie_titles, key="rate_movie")
    movie_id = movies_dict.get(movie_title) if movie_title else st.number_input("Or enter Movie ID directly", min_value=1, step=1)
    rating = st.slider("Your Rating", 1.0, 5.0, 3.0, 0.5)
    user_id = st.number_input("Your User ID", min_value=1, step=1)

    if st.button("Submit Rating"):
        payload = {"user_id": user_id, "movie_id": movie_id, "rating": rating}
        response = requests.post(f"{BACKEND_URL}/rate-movie/", json=payload, timeout=10)
        if response.status_code == 200:
            st.success("✅ Rating submitted successfully!")
        else:
            st.error(f"❌ Failed to submit rating: {response.text}")


# =======================================================
# PAGE 3 — Movie Details (Title or ID)
# =======================================================
elif page == "Movie Details":
    st.header("Movie Details Lookup")

    search_mode = st.radio("Search by:", ["Title", "Movie ID"], horizontal=True)

    if search_mode == "Title":
        title = st_autocomplete("Type a movie title", movie_titles, key="movie_title_search")
        if st.button("Search by Title"):
            if title:
                data = safe_get(f"{BACKEND_URL}/movies/title/{title}")
                if data:
                    st.write(f"🎬 **{data['title']} ({data.get('year', 'N/A')})**")
                    st.write(f"Genre: {data.get('genres', 'N/A')}")
                    st.write(f"⭐ Average Rating: {round(data.get('average_rating', 0), 2)}")
            else:
                st.warning("Please enter a title.")

    else:
        movie_id = st.number_input("Enter Movie ID", min_value=1, step=1)
        if st.button("Get Movie by ID"):
            data = safe_get(f"{BACKEND_URL}/movies/{movie_id}")
            if data:
                st.write(f"🎬 **{data['title']} ({data.get('year', 'N/A')})**")
                st.write(f"Genre: {data.get('genres', 'N/A')}")
                st.write(f"⭐ Average Rating: {round(data.get('average_rating', 0), 2)}")


# =======================================================
# PAGE 4 — Similar Movies
# =======================================================
elif page == "Similar Movies":
    st.header("Find Similar Movies")

    movie_title = st_autocomplete("Search Movie Title", movie_titles, key="similar_movie")
    movie_id = movies_dict.get(movie_title) if movie_title else st.number_input("Or enter Movie ID", min_value=1, step=1)
    top_n = st.slider("Number of similar movies", 1, 10, 5)

    if st.button("Get Similar Movies"):
        data = safe_get(f"{BACKEND_URL}/similar/{movie_id}?n={top_n}")
        if data:
            st.subheader("Similar Movies")
            for i, m in enumerate(data, 1):
                st.write(f"{i}. {m['title']} ({m.get('year', 'N/A')}) — {m.get('genres', 'N/A')}")


# =======================================================
# PAGE 5 — Top Rated Movies
# =======================================================
elif page == "Top Rated Movies":
    st.header("Top Rated Movies")

    top_n = st.slider("How many movies?", 1, 20, 10)
    data = safe_get(f"{BACKEND_URL}/top-rated?n={top_n}")

    if data:
        for i, m in enumerate(data, start=1):
            st.write(f"{i}. {m['title']} ({m.get('year', 'N/A')})")
            st.write(f"Genre: {m.get('genres', 'N/A')}")
            st.write(f"⭐ Average Rating: {round(m.get('average_rating', 0), 2)}")
            st.divider()


# =======================================================
# PAGE 6 — User Lookup
# =======================================================
elif page == "User Lookup":
    st.header("User Lookup")

    user_id = st.number_input("Enter User ID", min_value=1, step=1)
    if st.button("Get User Info"):
        data = safe_get(f"{BACKEND_URL}/users/{user_id}")
        if data:
            st.write("### User Info")
            st.json(data)
