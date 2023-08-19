# Use an official Python runtime as a base image
FROM python:3.8-slim-buster

# Copy the local src directory contents into the container at /app/src
COPY src/ /app/src
# Copy the local config.json into the container at /app
COPY config.json /app
# Change the working directory to /app/src
WORKDIR /app/src

# Install Flask and flask-cors
RUN pip install Flask flask-cors schedule

# Make port available to the world outside this container
EXPOSE 8007

# Define environment variable to tell Flask where to find the app
ENV FLASK_APP=proxy.py

# Run Flask app when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=8007"]