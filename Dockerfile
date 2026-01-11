# Use specific version for reproducibility
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies if needed (e.g. for pdfplumber dependencies if any missing in slim)
# python-slim is usually enough for these packages, but let's be safe for visual debugging tools or reportlab fonts if needed.
# For now, minimal.

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p fp/dump fp/organized static

# Expose port
EXPOSE 8000

# Run commands
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
