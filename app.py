import os
import streamlit as st
import requests

# 🔹 Backend URL (update this environment variable on Render)
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Movie Recommender", layout="centered")
st.title("Movie Recommender Web App")

# --- Sidebar Navigation ---
page = st.sidebar.selectbox(
    "Select Page",
    [
        "Home",
        "Get Recommendations",
        "Get Movie Details",
        "Get User Details",
        "Rate Movie"
    ]
)

# --- HOME ---
if page == "Home":
    st.subheader("Welcome to the Movie Recommendation System")
    st.write("Use the sidebar to get recommendations, view movies, look up users, or rate movies.")

# --- GET RECOMMENDATIONS ---
elif page == "Get Recommendations":
    user_type = st.radio("Are you an existing user or a new user?", ["Existing", "New"])

    if user_type == "Existing":
        user_id = st.number_input("Enter your User ID", min_value=1, step=1)
        top_n = st.slider("Number of recommendations", 1, 10, 5)

        if st.button("Get Recommendations"):
            try:
                response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
                response.raise_for_status()
                data = response.json()
                recs = data if isinstance(data, list) else data.get("recommendations", [])

                if recs:
                    st.subheader("Top Recommendations:")
                    for i, movie in enumerate(recs, 1):
                        title = movie.get("title", "Unknown Title")
                        genres = movie.get("genres", "N/A")
                        year = movie.get("year", "N/A")
                        avg_rating = movie.get("average_rating", "N/A")
                        st.write(f"{i}. {title} ({year}) - {genres} | Avg Rating: {avg_rating}")
                else:
                    st.warning("No recommendations found for this user.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

    else:  # New user
        st.write("Rate a few movies to get personalized recommendations.")
        st.write("Use Movie IDs from 1 to 1682 (MovieLens 100k).")

        ratings_input = st.text_area(
            "Enter ratings as movie_id:rating, separated by commas (e.g. 1:5,50:3,100:4)"
        )
        top_n = st.slider("Number of recommendations", 1, 10, 5)

        if st.button("Get New User Recommendations"):
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
                    data = response.json()
                    recs = data if isinstance(data, list) else data.get("recommendations", [])

                    if recs:
                        st.subheader("Top Recommendations:")
                        for i, movie in enumerate(recs, 1):
                            title = movie.get("title", "Unknown Title")
                            genres = movie.get("genres", "N/A")
                            year = movie.get("year", "N/A")
                            avg_rating = movie.get("average_rating", "N/A")
                            st.write(f"{i}. {title} ({year}) - {genres} | Avg Rating: {avg_rating}")
                    else:
                        st.warning("No recommendations found for your ratings.")
            except ValueError:
                st.error("Invalid input format. Use movie_id:rating, separated by commas.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching recommendations: {e}")

# --- GET MOVIE DETAILS ---
elif page == "Get Movie Details":
    movie_id = st.number_input("Enter Movie ID", min_value=1, step=1)

    if st.button("Get Movie Details"):
        try:
            response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
            response.raise_for_status()
            movie = response.json()

            if movie:
                st.subheader(f"{movie.get('title', 'Unknown Title')}")
                st.write(f"Movie ID: {movie.get('movieId', 'N/A')}")
                st.write(f"Genre: {movie.get('genres', 'N/A')}")
                st.write(f"Average Rating: {movie.get('average_rating', 'N/A')}")
            else:
                st.warning("No movie found with that ID.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching movie details: {e}")

# --- GET USER DETAILS ---
elif page == "Get User Details":
    st.subheader("Look Up User Details")
    user_id = st.number_input("Enter User ID", min_value=1, step=1)

    if st.button("Get User Details"):
        try:
            response = requests.get(f"{BACKEND_URL}/users/{user_id}", timeout=10)
            response.raise_for_status()
            user = response.json()

            if user:
                st.write(f"**User ID:** {user.get('userId', 'N/A')}")
                st.write(f"**Age:** {user.get('age', 'N/A')}")
                st.write(f"**Gender:** {user.get('gender', 'N/A')}")
                st.write(f"**Occupation:** {user.get('occupation', 'N/A')}")
                st.write(f"**Zip Code:** {user.get('zip_code', 'N/A')}")
            else:
                st.warning("No user found with that ID.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching user details: {e}")

# --- RATE MOVIE ---
elif page == "Rate Movie":
    st.subheader("Rate a Movie")

    user_id = st.number_input("Enter User ID", min_value=1, step=1)
    movie_id = st.number_input("Enter Movie ID", min_value=1, step=1)
    rating = st.slider("Rating (1–5)", 1.0, 5.0, 3.0, step=0.5)

    if st.button("Submit Rating"):
        try:
            payload = {
                "user_id": int(user_id),
                "ratings": {int(movie_id): float(rating)},
                "top_n": 5
            }
            response = requests.post(f"{BACKEND_URL}/rate/", json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            recs = data if isinstance(data, list) else data.get("recommendations", [])

            st.success(f"Rating submitted successfully for Movie ID {movie_id}.")
            if recs:
                st.subheader("New Recommendations:")
                for i, movie in enumerate(recs, 1):
                    title = movie.get("title", "Unknown Title")
                    genres = movie.get("genres", "N/A")
                    year = movie.get("year", "N/A")
                    avg_rating = movie.get("average_rating", "N/A")
                    st.write(f"{i}. {title} ({year}) - {genres} | Avg Rating: {avg_rating}")
            else:
                st.info("No new recommendations generated.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error submitting rating: {e}")
