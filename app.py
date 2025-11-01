# app.py
import os
import streamlit as st
import requests

# Backend URL (Render URL or local)
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Movie Recommender", layout="centered")
st.title("Movie Recommender System")

user_type = st.radio("Are you an existing user or new user?", ["Existing", "New"])

if user_type == "Existing":
    user_id = st.number_input("Enter your User ID", min_value=1, step=1)
    top_n = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Get Recommendations"):
        try:
            response = requests.get(f"{BACKEND_URL}/recommend/{user_id}?n={top_n}", timeout=10)
            response.raise_for_status()

            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, list):
                recs = data
            elif isinstance(data, dict):
                recs = data.get("recommendations", [])
            else:
                recs = []

            if recs:
                st.subheader("Top Recommendations")
                for i, movie in enumerate(recs, 1):
                    st.write(f"{i}. {movie}")
            else:
                st.warning("No recommendations found for this user.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")

else:  # New user
    st.write("Rate a few movies to get personalized recommendations.")
    st.write("Use Movie IDs from 1 to 1682 (MovieLens 100k dataset).")

    ratings_input = st.text_area(
        "Enter ratings as movie_id:rating, separated by commas (e.g. 1:5,50:3,100:4)"
    )
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
                response = requests.post(f"{BACKEND_URL}/rate/", json=payload, timeout=10)
                response.raise_for_status()

                data = response.json()
                if isinstance(data, list):
                    recs = data
                elif isinstance(data, dict):
                    recs = data.get("recommendations", [])
                else:
                    recs = []

                if recs:
                    st.subheader("Top Recommendations")
                    for i, movie in enumerate(recs, 1):
                        st.write(f"{i}. {movie}")
                else:
                    st.warning("No recommendations found for your ratings.")
        except ValueError:
            st.error("Invalid input format. Use movie_id:rating, separated by commas.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching recommendations: {e}")


st.header("Search Movie by ID")

movie_id = st.number_input("Enter a Movie ID to look up", min_value=1, step=1)

if st.button("Get Movie Details"):
    try:
        response = requests.get(f"{BACKEND_URL}/movies/{movie_id}", timeout=10)
        response.raise_for_status()

        data = response.json()

        # Display movie details in a clean format
        st.subheader("Movie Details")
        if isinstance(data, dict):
            title = data.get("title", "Unknown Title")
            genre = data.get("genre", "N/A")
            year = data.get("year", "N/A")

            st.write(f"**Title:** {title}")
            st.write(f"**Genre:** {genre}")
            st.write(f"**Year:** {year}")

            if "description" in data:
                st.write(f"**Description:** {data['description']}")
        else:
            st.warning("Unexpected response format. Check the API response structure.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error("Movie not found. Please check the Movie ID.")
        else:
            st.error(f"Server error: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching movie details: {e}")

