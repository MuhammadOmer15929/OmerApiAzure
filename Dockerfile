# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make sure the model file exists
RUN if [ ! -f "model/last_model_with_architecture.h5" ]; then echo "Model file not found!"; exit 1; fi

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run gunicorn server
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
