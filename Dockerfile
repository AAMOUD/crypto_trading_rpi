FROM python:3.13-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script and utils folder
COPY main.py .
COPY utils/ ./utils/

CMD ["python", "main.py"]
