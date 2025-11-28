# Use official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy the entire project into the container
COPY . .

# Install required Python packages directly
RUN pip install --no-cache-dir flask requests

# Expose Flask port
EXPOSE 5000

# Run the Flask app using app.py (which calls create_app())
CMD ["python", "app.py"]
