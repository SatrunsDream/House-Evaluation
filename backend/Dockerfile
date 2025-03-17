# Use Python 3.9 slim image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN python3 -m ensurepip && python3 -m pip install --upgrade pip

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 