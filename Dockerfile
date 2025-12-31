# Python image for reduced attack surface
FROM python:3.10-slim

# Install GCC compiler (essential to build your core_engine on Linux)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Set the work directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# COMPILE THE CORE ENGINE (The Native Smart Shield)
# Converts scanner.c to a Linux-compatible .so (Shared Object)
WORKDIR /app/core_engine
RUN gcc -shared -o scanner.so -fPIC scanner.c

# Start the Gateway Server
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]