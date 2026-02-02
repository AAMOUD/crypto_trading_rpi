FROM python:3.11-slim

WORKDIR /app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install dependencies in a virtualenv managed by pipenv
RUN pipenv install --deploy --system

# Copy your script and utils folder
COPY main.py .
COPY utils/ ./utils/

CMD ["python", "main.py"]
