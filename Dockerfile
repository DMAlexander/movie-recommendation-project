FROM python:3.9-slim

# Install system build tools
RUN apt-get update && apt-get install -y build-essential gfortran && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install dependencies with compatible versions
RUN pip install numpy==1.24.4 \
    pandas==2.0.3 \
    scikit-learn==1.3.2 \
    scikit-surprise==1.1.3 \
    uvicorn==0.23.2 \
    fastapi==0.107.0 \
    joblib==1.5.2

EXPOSE 10000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
