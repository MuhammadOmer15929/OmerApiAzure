FROM python:3.11

WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download model file during build
RUN mkdir -p model && \
    curl -L 'https://drive.google.com/uc?export=download&id=1PLucaH0gaI-euAvtwzwduypUbRchcTQV' -o model/last_model_with_architecture.h5

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
