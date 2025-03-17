# Use a minimal Ubuntu base image
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip python3-distutils \
    nodejs npm

# Set working directory
WORKDIR /app

# Copy all your project files into the container
COPY . /app

# Upgrade pip, install Python dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r backend/requirements.txt

# Build your frontend
RUN cd frontend && npm install && npm run build

# Expose the port FastAPI will run on
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
