# Use an official Python runtime as a parent image
FROM python:3.11-slim
LABEL org.opencontainers.image.source="https://github.com/dmitriy-b/blockchain-client-testing"

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8089 available to the world outside this container
EXPOSE 8089

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run pytest when the container launches
CMD ["pytest"]