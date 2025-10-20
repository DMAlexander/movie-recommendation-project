# app.py
import streamlit as st
import requests

st.title("🎬 Personalized Movie Recommender")

user_type = st.radio("Are you an existing user or new user?", ["Existing", "New"])

if user_type == "Existing":
    user_id = st.number_input("Enter your User ID", min_value=1, step=1)
    top_n = st.slider("Number of recommendations", 1, 10, 5)
    
    if st.button("Get Recommendations"):
        response = requests.get(f"http://127.0.0.1:8000/recommend/{user_id}?n={top_n}")
        if response.status_code == 200:
            recs = response.json()["recommendations"]
            st.subheader("Top Recommendations:")
            for i, movie in enumerate(recs, 1):
                st.write(f"{i}. {movie}")
        else:
            st.error("Error fetching recommendations")

else:  # New user
    st.write("Rate a few movies to get personalized recommendations")
    st.write("Use Movie IDs from 1 to 1682 (MovieLens 100k)")
    
    ratings_input = st.text_area("Enter ratings as movie_id:rating, separated by commas (e.g. 1:5,50:3,100:4)")
    top_n = st.slider("Number of recommendations", 1, 10, 5)
    
    if st.button("Get Recommendations"):
        try:
            ratings_dict = {}
            for pair in ratings_input.split(","):
                mid, r = pair.strip().split(":")
                ratings_dict[int(mid)] = float(r)
            
            payload = {"user_id": 1000, "ratings": ratings_dict, "top_n": top_n}
            response = requests.post("http://127.0.0.1:8000/rate/", json=payload)
            if response.status_code == 200:
                recs = response.json()["recommendations"]
                st.subheader("Top Recommendations:")
                for i, movie in enumerate(recs, 1):
                    st.write(f"{i}. {movie}")
            else:
                st.error("Error fetching recommendations")
        except Exception as e:
            st.error(f"Invalid input: {e}")