#!/bin/bash
# Railway deployment script
# This script runs before the web process starts

echo "🚀 Starting Railway deployment..."

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

echo "✅ Deployment preparation complete!"
