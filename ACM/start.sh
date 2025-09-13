#!/bin/bash

echo "🏃‍♂️ Starting InShape Application..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Please create a .env file with your Strava OAuth credentials."
    echo "See STRAVA_OAUTH_SETUP.md for instructions."
    echo ""
    exit 1
fi

# Check if frontend .env.local exists
if [ ! -f in-shape-frontend/.env.local ]; then
    echo "📝 Creating frontend environment file..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:5000" > in-shape-frontend/.env.local
fi

# Function to check if a port is in use
check_port() {
    lsof -ti:$1 > /dev/null 2>&1
}

# Check if ports are already in use
if check_port 5000; then
    echo "⚠️  Port 5000 is already in use. Please stop the service using this port."
    exit 1
fi

if check_port 3000; then
    echo "⚠️  Port 3000 is already in use. Please stop the service using this port."
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."

# Check Python dependencies
if ! pip show flask > /dev/null 2>&1; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check Node dependencies
if [ ! -d "in-shape-frontend/node_modules" ]; then
    echo "Installing Node.js dependencies..."
    cd in-shape-frontend
    npm install
    cd ..
fi

echo ""
echo "🚀 Starting backend server on port 5000..."

# Start backend in background
python backend/app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo "🎨 Starting frontend server on port 3000..."

# Start frontend in background
cd in-shape-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Application started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "⚡ Backend:  http://localhost:5000"
echo ""
echo "📚 Setup instructions: See STRAVA_OAUTH_SETUP.md"
echo ""
echo "Press Ctrl+C to stop both servers..."

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for user to stop
wait
