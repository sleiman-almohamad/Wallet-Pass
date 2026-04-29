#!/bin/bash

# Tunnel startup script for Wallet Passes
PORT_BACKEND=8100
PORT_FRONTEND=8500

echo "=========================================="
echo "Starting Cloudflare Tunnels"
echo "=========================================="

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null
then
    echo "❌ cloudflared not found."
    echo "Please install it first:"
    echo "curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared"
    echo "chmod +x cloudflared"
    echo "sudo mv cloudflared /usr/local/bin/"
    exit 1
fi

# Kill any existing cloudflared processes to avoid confusion
echo "🧹 Cleaning up old tunnels..."
pkill cloudflared

echo "🚀 Starting Backend Tunnel (Port $PORT_BACKEND)..."
cloudflared tunnel --url http://localhost:$PORT_BACKEND > /tmp/tunnel_backend.log 2>&1 &
BACKEND_PID=$!

echo "🚀 Starting Frontend Tunnel (Port $PORT_FRONTEND)..."
cloudflared tunnel --url http://localhost:$PORT_FRONTEND > /tmp/tunnel_frontend.log 2>&1 &
FRONTEND_PID=$!

echo "⏳ Waiting for URLs to generate..."
sleep 5

BACKEND_URL=$(grep -a -o 'https://[-0-9a-z]*\.trycloudflare.com' /tmp/tunnel_backend.log | head -n 1)
FRONTEND_URL=$(grep -a -o 'https://[-0-9a-z]*\.trycloudflare.com' /tmp/tunnel_frontend.log | head -n 1)

echo ""
echo "=========================================="
echo "✅ TUNNELS ACTIVE"
echo "=========================================="
echo "🔗 BACKEND URL:  $BACKEND_URL"
echo "   (Set this as PUBLIC_URL in .env)"
echo ""
echo "🔗 FRONTEND URL: $FRONTEND_URL"
echo "   (Share this with your colleague!)"
echo "=========================================="
echo ""
echo "Tunnels are running in the background (PIDs: $BACKEND_PID, $FRONTEND_PID)"
echo "To stop them, run: pkill cloudflared"
echo ""
echo "Logs are available at:"
echo "  - /tmp/tunnel_backend.log"
echo "  - /tmp/tunnel_frontend.log"
