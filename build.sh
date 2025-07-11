#!/bin/bash

# Build script for Render deployment
echo "Building React frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build complete!" 