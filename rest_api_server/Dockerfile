# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Add the necessary directories to PYTHONPATH
ENV PYTHONPATH="/app:/app/api/grpc:${PYTHONPATH}"

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 for the Django app
EXPOSE 8000

# Command to run both the Django app and the RabbitMQ consumer
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000 & python /app/rest_api_server/rabbitmq_consumer.py"]
