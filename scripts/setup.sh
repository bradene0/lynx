#!/bin/bash

# LYNX Development Setup Script

echo "🌌 Setting up LYNX - Linked Knowledge Network Explorer"
echo "=================================================="

# Check if required tools are installed
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    else
        echo "✅ $1 is available"
    fi
}

echo "Checking prerequisites..."
check_command "node"
check_command "npm"
check_command "docker"
check_command "python3"

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "❌ Node.js version 20 or higher is required. Current version: $(node --version)"
    exit 1
fi

echo "✅ Node.js version is compatible: $(node --version)"

# Install dependencies
echo ""
echo "Installing dependencies..."
npm install

# Set up environment files
echo ""
echo "Setting up environment files..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env and add your OpenAI API key"
else
    echo "✅ .env file already exists"
fi

if [ ! -f scripts/ingestion/.env ]; then
    cp scripts/ingestion/.env.example scripts/ingestion/.env
    echo "✅ Created ingestion .env file from template"
fi

# Start Docker services
echo ""
echo "Starting Docker services..."
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run database migrations
echo ""
echo "Running database migrations..."
cd apps/web && npm run db:migrate
cd ../..

echo ""
echo "🎉 LYNX setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OpenAI API key"
echo "2. Run 'npm run dev' to start the development server"
echo "3. Run 'npm run ingest' to populate the database with initial data"
echo ""
echo "Happy exploring! 🌌"
