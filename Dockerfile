# Use the official Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file and install the dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that the FastAPI app will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]