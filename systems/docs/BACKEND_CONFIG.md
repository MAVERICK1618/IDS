# Backend Configuration Guide

## Overview

The Flask backend API serves all data to the React frontend. This guide covers configuration for development and production.

## Current Configuration

### API Server
- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 8000
- **Debug**: False

### CORS Configuration
Currently allows requests from any origin:
```python
response.headers["Access-Control-Allow-Origin"] = "*"
response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
```

### Endpoints
Base URL: `http://localhost:8000`
API Index: `http://localhost:8000/` (lists all endpoints)

## Development Setup

### Prerequisites
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install flask flask-cors
```

### Running the Server
```bash
python3 app.py
```

The server will start on `http://localhost:8000`

### Verify Backend
```bash
# Check if backend is running
curl http://localhost:8000/

# Test specific endpoint
curl http://localhost:8000/api/status
```

## Production Configuration

### 1. CORS for Specific Origins

Update `app.py` to restrict CORS to known origins:

```python
from flask import Flask, jsonify, request

ALLOWED_ORIGINS = [
    "https://YOUR_DOMAIN",
    "https://www.YOUR_DOMAIN",
]

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
    return response
```

### 2. HTTPS Support

The Flask backend itself doesn't require code changes for HTTPS. Instead, use a reverse proxy:

#### Option A: Nginx (Recommended)

Create `/etc/nginx/sites-available/ids-api`:

```nginx
server {
    listen 443 ssl http2;
    server_name api.YOUR_DOMAIN;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://YOUR_DOMAIN' always;
        add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.YOUR_DOMAIN;
    return 301 https://$server_name$request_uri;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/ids-api /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### Option B: Apache

Create `/etc/apache2/sites-available/ids-api.conf`:

```apache
<VirtualHost *:443>
    ServerName api.YOUR_DOMAIN
    
    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
    
    # Enable CORS
    Header set Access-Control-Allow-Origin "https://YOUR_DOMAIN"
    Header set Access-Control-Allow-Methods "GET, OPTIONS"
    Header set Access-Control-Allow-Headers "Content-Type, Authorization"
    
    # Proxy configuration
    ProxyPreserveHost On
    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/
</VirtualHost>

<VirtualHost *:80>
    ServerName api.YOUR_DOMAIN
    Redirect / https://api.YOUR_DOMAIN/
</VirtualHost>
```

Enable the site:
```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo a2ensite ids-api
sudo systemctl restart apache2
```

### 3. Environment Variables

Create `backend/.env`:
```
FLASK_ENV=production
FLASK_DEBUG=0
ALLOWED_ORIGINS=https://YOUR_DOMAIN,https://www.YOUR_DOMAIN
```

Load in `app.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
```

### 4. SSL Certificates

#### Using Let's Encrypt (Free)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d api.YOUR_DOMAIN

# Auto-renewal (runs twice daily)
sudo systemctl enable certbot.timer
```

#### Self-Signed Certificate (Testing Only)

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

## Performance Optimization

### 1. Enable Caching

Add cache headers in Flask:

```python
@app.after_request
def add_cache_headers(response):
    # Cache static data for 1 hour
    if request.path.startswith('/api/ground-truth') or request.path.startswith('/api/metrics'):
        response.headers["Cache-Control"] = "public, max-age=3600"
    # Don't cache live data
    elif request.path.startswith('/api/traffic/live'):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
```

### 2. Enable Compression

```python
from flask_compress import Compress
Compress(app)
```

### 3. Use Gunicorn for Production

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Monitoring & Logging

### 1. Log File Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### 2. Request Logging

```python
@app.before_request
def log_request():
    app.logger.info(f"{request.method} {request.path}")

@app.after_request
def log_response(response):
    app.logger.info(f"Response: {response.status_code}")
    return response
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### CORS Errors in Browser
1. Check browser console for specific CORS error
2. Verify `Access-Control-Allow-Origin` header is set
3. Ensure frontend origin is in `ALLOWED_ORIGINS`
4. Check if OPTIONS preflight request succeeds

### Backend Connection Refused
1. Verify backend is running: `ps aux | grep python`
2. Check if port 8000 is listening: `netstat -tlnp | grep 8000`
3. Test curl: `curl -v http://localhost:8000/`

## Files

- `app.py` - Main Flask application with all endpoint definitions
- `.env` - Environment variables (create if needed)
- `logs/` - Log files (created automatically in production)
