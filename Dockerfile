# Use official Python 3.10 slim image
FROM python:3.10-slim

# Install system build tools needed for scikit-surprise
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel

# Install Python dependencies
RUN pip install numpy==1.26.4 \
    pandas==2.0.3 \
    scikit-learn==1.3.2 \
    scikit-surprise==1.1.3 \
    uvicorn==0.23.2 \
    fastapi==0.107.0 \
    joblib==1.5.2

# Expose the port that Render will use
EXPOSE 10000

# Start FastAPI
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
