FROM python:3.11-slim

WORKDIR /app

# Upgrade pip first
RUN python -m pip install --upgrade pip

# Install OPTIMADE server and dependencies
RUN pip install "optimade[server]" --upgrade

# Copy your config and server files
COPY . .

# Expose OPTIMADE server port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "optimade.server.main:app", "--host", "0.0.0.0", "--port", "8000"]

