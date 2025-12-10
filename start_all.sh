#!/bin/bash

echo "=========================================="
echo "Starting Wallet Passes Application"
echo "=========================================="
echo ""

# Start Docker services (MariaDB, phpMyAdmin, API)
echo "📦 Starting Docker services..."
sudo docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
echo ""
echo "✅ Services Status:"
sudo docker-compose ps

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

# Wait a moment for API to start
sleep 3

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
