#!/bin/bash

# Port definitions
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Sentinel Civic in Ngrok Mode...${NC}"

# Check for ngrok
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}Error: ngrok is not installed or not in your PATH.${NC}"
    echo "Please install it using Homebrew:"
    echo "  brew install ngrok/tap/ngrok"
    echo "Or download it from https://ngrok.com/download"
    echo "After installation, authenticate with your token:"
    echo "  ngrok config add-authtoken <your-token>"
    exit 1
fi

# Function to kill processes on exit
cleanup() {
    echo -e "\n${RED}Shutting down processes...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

# 1. Start Backend
echo "Starting Backend on port $BACKEND_PORT..."
source venv/bin/activate
uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

# Wait for backend to be ready (simple check)
sleep 3

# 2. Start Frontend
echo "Starting Frontend on port $FRONTEND_PORT..."
cd src/interfaces/frontend
npm run dev -- --port $FRONTEND_PORT &
FRONTEND_PID=$!
cd - > /dev/null

# Wait for frontend to be ready
sleep 3

# 3. Start Ngrok
echo -e "${GREEN}Starting Ngrok Tunnel for port $FRONTEND_PORT...${NC}"
# We only need to expose the frontend because it proxies /api to the backend locally
ngrok http $FRONTEND_PORT --log=stdout > ngrok.log &
NGROK_PID=$!

# Wait for ngrok to initialize
sleep 3

# Extract URL from ngrok log or API
# Note: This might require jq. If not available, we print instructions.
if command -v jq &> /dev/null; then
    # Give ngrok a moment to really start
    sleep 2
    TUNNEL_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    if [ "$TUNNEL_URL" != "null" ]; then
         echo -e "${GREEN}------------------------------------------------------------${NC}"
         echo -e "${GREEN} YOUR APP IS ONLINE AT: ${TUNNEL_URL} ${NC}"
         echo -e "${GREEN}------------------------------------------------------------${NC}"
    else
         echo -e "${RED}Could not auto-detect Ngrok URL. Check the ngrok dashboard or terminal output.${NC}"
    fi
else
    echo -e "${GREEN}Ngrok is running!${NC}"
    echo "Cannot auto-detect URL (install jq for that)."
    echo "Please check the terminal web interface at http://127.0.0.1:4040"
fi

echo "Press Ctrl+C to stop everything."
wait
