#!/bin/bash

echo "=========================================="
echo "Starting Wallet Passes Application"
echo "=========================================="
echo ""

# Check if Docker containers are already running
echo "🔍 Checking Docker services status..."

# Check if we can access docker (try without sudo first, then with sudo)
#if docker ps &>/dev/null; then
#    DOCKER_CMD="docker"
#else
#    DOCKER_CMD="sudo docker"
#fi

# Count running containers
#RUNNING_CONTAINERS=$($DOCKER_CMD ps --filter "name=walletpasses" --format "{{.Names}}" 2>/dev/null | wc -l)

#if [ "$RUNNING_CONTAINERS" -ge 2 ]; then
#    echo "✅ Docker services are already running!"
#    echo ""
#    echo "Running containers:"
#    $DOCKER_CMD ps --filter "name=walletpasses" --format "  - {{.Names}} ({{.Status}})"
#else
echo "📦 Starting Docker services..."
sudo docker compose up -d
    
    # Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5
    
echo ""
echo "✅ Services started successfully!"
#fi

echo ""
echo "=========================================="
echo "Services Available:"
echo "=========================================="
echo "📊 phpMyAdmin:  http://localhost:8080"
echo "   Username: root"
echo "   Password: 123456789"
echo ""
echo "🚀 FastAPI:     http://localhost:8000"
echo "   Docs:       http://localhost:8000/docs"
echo ""
echo "🗄️  MariaDB:     localhost:3306"
echo "   Database:   wallet_passes"
echo ""
echo "=========================================="
echo ""

# Start the FastAPI server in the background
echo "🚀 Starting FastAPI server in background..."
uv run python -m uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload > /tmp/api.log 2>&1 &
API_PID=$!
echo "   API PID: $API_PID"
echo "   API logs: /tmp/api.log"

# Wait for API to be ready (up to 30 seconds)
echo "⏳ Waiting for FastAPI server to be ready..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ FastAPI server is ready!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "⚠️  FastAPI server did not start within 30 seconds. Check /tmp/api.log"
        echo "   Continuing anyway..."
    fi
    sleep 1
done

# Start the Flet GUI application
echo ""
echo "🖥️  Starting Flet application..."
uv run python main.py

# When Flet app closes, optionally stop the API
echo ""
echo "Flet application closed."
read -p "Do you want to stop the API server? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Stopping API server (PID: $API_PID)..."
    kill $API_PID
    echo "API server stopped."
fi
