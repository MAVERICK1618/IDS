# Frontend-Backend Integration Setup Guide

## Project Structure

```
IDS/
├── frontend/                 # React + Vite
│   ├── src/
│   │   ├── services/
│   │   │   └── api.ts        # API client (new)
│   │   ├── hooks/
│   │   │   ├── useAgentFeed.ts        # Updated
│   │   │   ├── usePacketStream.ts     # Updated
│   │   │   ├── useAttackFeed.ts       # Updated
│   │   │   ├── useEvaluation.ts       # Updated
│   │   │   └── useRLTraining.ts       # Mock data (unchanged)
│   │   ├── components/panels/
│   │   │   ├── PacketMonitorPanel.tsx # Updated (error handling)
│   │   │   ├── AgentFeedPanel.tsx     # Updated (error handling)
│   │   │   ├── AttackTimelinePanel.tsx# Updated (error handling)
│   │   │   └── MetricsPanelWrapper.tsx# Updated (error handling)
│   │   └── App.tsx
│   ├── .env.local            # Dev config (new)
│   ├── .env.production       # Prod config (new)
│   ├── .env.example          # Template (new)
│   ├── vite.config.ts        # Updated with API proxy
│   ├── API_INTEGRATION.md    # API docs (new)
│   └── package.json
│
├── backend/                  # Flask
│   ├── app.py               # Updated with .env support
│   └── .env.production      # (optional) Production config
│
└── BACKEND_CONFIG.md        # Backend config guide (new)
    DEPLOYMENT.md            # This file
```

## API Endpoint Mapping

| Frontend | Backend Endpoint | Purpose |
|----------|---|---|
| usePacketStream | /api/traffic/live | Network traffic packets |
| useAgentFeed | /api/agent/messages | Agent log messages |
| useAttackFeed | /api/alerts | Detected attacks/alerts |
| useEvaluation | /api/metrics | Model evaluation metrics |
| useRLTraining | (mock) | RL training progress (mock data) |

## Development Environment Setup

### 1. Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### 2. Backend Setup

```bash
# Create and activate virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install flask flask-cors python-dotenv

# Run backend
python3 app.py
```

Backend will be available at: `http://localhost:8000`

### 3. Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Create development config (optional - uses http://localhost:8000 by default)
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# Run frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### 4. Verify Integration

Open browser and check:
1. Frontend: http://localhost:5173
2. Backend: http://localhost:8000
3. Developer console (DevTools) → Network tab → filter by `/api` to see requests

### 5. Testing API Endpoints

```bash
# Test backend connectivity
curl http://localhost:8000/api/status
curl http://localhost:8000/api/alerts
curl http://localhost:8000/api/metrics

# Test frontend connectivity
# Open http://localhost:5173 in browser
# Should see API data in the panels (if data exists in backend)
```

## Production Deployment

### 1. Build Frontend

```bash
cd frontend

# Create production config
echo "VITE_API_BASE_URL=https://api.YOUR_DOMAIN" > .env.production

# Build
npm run build

# Output in dist/ directory
```

### 2. Configure Backend CORS (Production)

Edit `backend/app.py` to restrict CORS:

```python
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://YOUR_DOMAIN").split(",")
```

Create `backend/.env`:
```
FLASK_ENV=production
ALLOWED_ORIGINS=https://YOUR_DOMAIN,https://www.YOUR_DOMAIN
```

### 3. Setup HTTPS with Reverse Proxy

Choose one:

#### Option A: Nginx + Let's Encrypt

```bash
# Install Nginx and Certbot
sudo apt-get install nginx certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot certonly --nginx -d api.YOUR_DOMAIN

# Configure Nginx (see BACKEND_CONFIG.md for full config)
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### Option B: Apache + Let's Encrypt

```bash
# Install Apache and Certbot
sudo apt-get install apache2 certbot python3-certbot-apache

# Get SSL certificate
sudo certbot certonly --apache -d api.YOUR_DOMAIN

# Enable modules
sudo a2enmod proxy proxy_http headers rewrite ssl
sudo systemctl start apache2
sudo systemctl enable apache2
```

### 4. Run Backend (Production)

```bash
cd backend
source venv/bin/activate

# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

Or use supervisord for process management:

```bash
# Install supervisor
sudo apt-get install supervisor

# Create /etc/supervisor/conf.d/ids-api.conf:
[program:ids-api]
command=/home/test/IDS/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
directory=/home/test/IDS/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ids-api.log

# Start service
sudo systemctl start supervisor
sudo systemctl enable supervisor
```

### 5. Deploy Frontend (Production)

Options:

#### Option A: Static Web Server (Nginx/Apache)

```bash
# Copy built files
sudo cp -r frontend/dist/* /var/www/html/

# Configure as SPA (important!)
# See BACKEND_CONFIG.md for Nginx configuration
```

#### Option B: Node.js Server

```bash
# Install serve or similar
npm install -g serve

# Run
serve -s frontend/dist -l 3000
```

#### Option C: Docker

```bash
# Build frontend
docker build -f frontend/Dockerfile -t ids-frontend .

# Run
docker run -p 80:80 ids-frontend
```

## HTTPS Configuration

### Files to Reference
- `BACKEND_CONFIG.md` - Detailed backend HTTPS setup
- `frontend/.env.production` - Frontend production configuration

### Key Points
1. Frontend `.env.production` must use HTTPS URL
2. Backend reverse proxy (Nginx/Apache) handles HTTPS
3. Obtain SSL certificate from Let's Encrypt (free)
4. Update CORS ALLOWED_ORIGINS in backend for production domain
5. All API communication is encrypted in production

## Environment Variables

### Frontend

**Development (.env.local)**
```
VITE_API_BASE_URL=http://localhost:8000
```

**Production (.env.production)**
```
VITE_API_BASE_URL=https://api.YOUR_DOMAIN
```

### Backend

**Development**
```
FLASK_ENV=development
ALLOWED_ORIGINS=*
```

**Production (.env)**
```
FLASK_ENV=production
ALLOWED_ORIGINS=https://YOUR_DOMAIN,https://www.YOUR_DOMAIN
```

## Configuration Files Changes

### New Files Created
1. `frontend/src/services/api.ts` - API client
2. `frontend/.env.local` - Dev environment
3. `frontend/.env.production` - Prod environment
4. `frontend/.env.example` - Template
5. `frontend/API_INTEGRATION.md` - Integration docs
6. `BACKEND_CONFIG.md` - Backend docs
7. `DEPLOYMENT.md` - This file

### Modified Files
1. `frontend/src/hooks/useAgentFeed.ts` - API calls instead of mock
2. `frontend/src/hooks/usePacketStream.ts` - API calls instead of mock
3. `frontend/src/hooks/useAttackFeed.ts` - API calls instead of mock
4. `frontend/src/hooks/useEvaluation.ts` - API calls instead of mock
5. `frontend/src/components/panels/PacketMonitorPanel.tsx` - Error handling
6. `frontend/src/components/panels/AgentFeedPanel.tsx` - Error handling
7. `frontend/src/components/panels/AttackTimelinePanel.tsx` - Error handling
8. `frontend/src/components/panels/MetricsPanelWrapper.tsx` - Error handling
9. `frontend/vite.config.ts` - API proxy configuration
10. `backend/app.py` - .env support and CORS configuration

### Unchanged
- `frontend/src/hooks/useRLTraining.ts` - Uses mock data (no backend endpoint)
- All component UI logic
- All styling
- Database models and business logic

## Testing Checklist

### Development
- [ ] Backend running on localhost:8000
- [ ] Frontend running on localhost:5173
- [ ] Verify API calls in browser DevTools Network tab
- [ ] Check all panels show real data (if data exists)
- [ ] Test error handling by stopping backend
- [ ] Verify hook polling intervals

### Production
- [ ] Frontend .env.production configured with HTTPS
- [ ] Backend ALLOWED_ORIGINS configured for domain
- [ ] SSL certificates installed and valid
- [ ] CORS headers present in responses
- [ ] API requests use HTTPS URLs
- [ ] Frontend built and deployed
- [ ] Test from actual domain (not localhost)
- [ ] Check browser console for mixed content warnings
- [ ] Verify authentication headers if needed

## Troubleshooting

### API Requests Failing
1. Check backend is running: `curl http://localhost:8000/`
2. Check frontend console for CORS errors
3. Verify VITE_API_BASE_URL in .env.local
4. Check network tab in DevTools

### CORS Errors
1. Verify backend ALLOWED_ORIGINS includes frontend origin
2. Check preflight OPTIONS requests succeed
3. Verify headers are present in response
4. Test with `curl -i http://localhost:8000/api/status`

### No Data Showing
1. Verify backend data files exist
2. Check if system is running (data collection)
3. Test endpoint directly: `curl http://localhost:8000/api/alerts`
4. Check hook polling (should see requests every N seconds)

### Build Issues
1. Clear node_modules: `rm -rf node_modules && npm install`
2. Clear build cache: `rm -rf dist`
3. Check Node version: `node --version` (should be 16+)

## Performance Optimization

### Frontend
- Built with Vite for fast development
- React 19 with hooks for efficient re-renders
- Polling intervals tuned for real-time feel
- Error boundaries for graceful error handling

### Backend
- Efficient CSV/JSON reading with limit parameter
- Process caching for lab status checks
- Can add response caching for static endpoints

### Network
- API proxy in dev reduces CORS complexity
- Production uses reverse proxy for optimal performance
- Consider adding API response caching

## Security Considerations

### Current Setup
- CORS allows any origin in development
- No authentication required
- HTTP only in development (OK)

### Production Requirements
1. Enable HTTPS (required)
2. Restrict CORS to known origins
3. Consider adding API key authentication
4. Use environment variables for sensitive config
5. Monitor logs for suspicious activity
6. Regular SSL certificate renewal

## Monitoring and Logging

### Frontend
- Browser console for errors
- Network tab for request/response inspection
- Error states displayed in UI

### Backend
- Console output for basic info
- Can add file logging for production
- Monitor API response times

## Commands Reference

### Development
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python3 app.py

# Terminal 2: Frontend  
cd frontend && npm run dev
```

### Production Build
```bash
cd frontend
npm run build
# Output: dist/
```

### Production Run (Gunicorn)
```bash
cd backend && gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Next Steps

1. Configure production domain and environment
2. Set up SSL certificates
3. Deploy frontend to static hosting or CDN
4. Deploy backend with reverse proxy
5. Update DNS records
6. Monitor logs and performance
7. Set up automated backups
8. Plan for scaling if needed

## Support

For issues or questions:
1. Check `API_INTEGRATION.md` for frontend-specific details
2. Check `BACKEND_CONFIG.md` for backend-specific details
3. Review browser DevTools Network tab
4. Check server logs for errors
