# backend/Dockerfile
FROM python:3.12-slim

# Create a non-root user
RUN useradd -m appuser

WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary source files (adjust as needed)
COPY main.py ./
COPY worker.py ./
COPY models.py ./
COPY utils/ ./utils/
COPY vendors/ ./vendors/
COPY tests/ ./tests/

# Switch to non-root user
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]