# Frontend-Backend Integration Summary

## Project Overview

Successfully integrated React frontend with Flask backend for the IDS Dashboard. The frontend now makes real API calls to the backend instead of using mock data.

## What Was Done

### 1. Created API Client Service
**File**: `frontend/src/services/api.ts`
- Centralized API communication layer
- Environment-based URL configuration (HTTP for dev, HTTPS for prod)
- Proper error handling and type definitions
- All 20+ backend endpoints exposed as TypeScript functions
- Support for cross-origin requests with credentials

### 2. Updated Frontend Hooks
All hooks now fetch real data from backend API:

| Hook | Endpoint | Purpose |
|------|----------|---------|
| `usePacketStream` | `/api/traffic/live` | Live network traffic |
| `useAgentFeed` | `/api/agent/messages` | Agent log messages |
| `useAttackFeed` | `/api/alerts` | Detected attacks |
| `useEvaluation` | `/api/metrics` | ML metrics |
| `useRLTraining` | (mock) | RL training (no backend endpoint) |

### 3. Environment Configuration
Created environment variable files:
- `.env.local` - Development (localhost:8000)
- `.env.production` - Production (configure HTTPS domain)
- `.env.example` - Template for reference

### 4. Enhanced Panel Components
Updated all panel components with error handling:
- `PacketMonitorPanel`
- `AgentFeedPanel`
- `AttackTimelinePanel`
- `MetricsPanelWrapper`

Error messages display when API calls fail.

### 5. Backend Updates
Modified `backend/app.py`:
- Added optional `.env` file support via python-dotenv
- Made CORS configurable (still allows any origin by default)
- Added FLASK_ENV detection for development/production
- Support for `ALLOWED_ORIGINS` configuration

### 6. Comprehensive Documentation
Created three detailed guides:
- **API_INTEGRATION.md** - API architecture, endpoints, hooks, debugging
- **BACKEND_CONFIG.md** - Backend setup, production CORS, HTTPS setup, SSL certificates
- **DEPLOYMENT.md** - Complete deployment guide, environment setup, testing checklist

### 7. Vite Configuration
Updated `vite.config.ts`:
- Added API proxy for development (reduces CORS complexity)
- Configured path alias for cleaner imports
- Proper build optimization

## Files Changed

### New Files (7)
```
frontend/src/services/api.ts                 # API client
frontend/.env.local                          # Dev environment
frontend/.env.production                     # Prod environment  
frontend/.env.example                        # Template
frontend/API_INTEGRATION.md                  # API docs
BACKEND_CONFIG.md                            # Backend config guide
DEPLOYMENT.md                                # Deployment guide
```

### Modified Files (11)
```
frontend/src/hooks/useAgentFeed.ts           # API calls
frontend/src/hooks/usePacketStream.ts        # API calls
frontend/src/hooks/useAttackFeed.ts          # API calls
frontend/src/hooks/useEvaluation.ts          # API calls
frontend/src/components/panels/PacketMonitorPanel.tsx   # Error handling
frontend/src/components/panels/AgentFeedPanel.tsx       # Error handling
frontend/src/components/panels/AttackTimelinePanel.tsx  # Error handling
frontend/src/components/panels/MetricsPanelWrapper.tsx  # Error handling
frontend/vite.config.ts                      # API proxy
frontend/src/types/evaluation.ts             # Extended type definition
frontend/src/data/mockEvaluation.ts          # Updated mock format
backend/app.py                               # .env support, CORS config
```

## Frontend ↔ Backend API Mapping

### Status & Pipeline
- **GET /api/status** → Pipeline running status
- **GET /api/pipeline/checkpoints** → Checkpoint progress

### Agent Communication
- **GET /api/agent/messages** → useAgentFeed hook
- **GET /api/agent/nodes** → Agent workflow status

### Alerts & Detection
- **GET /api/alerts** → useAttackFeed hook
- **GET /api/alerts/<detector>** → Specific detector alerts

### ML Predictions
- **GET /api/predictions** → All predictions
- **GET /api/predictions/<detector>** → Specific predictions

### Ground Truth
- **GET /api/ground-truth** → Ground truth summary
- **GET /api/ground-truth/<type>** → Attack type data

### Metrics
- **GET /api/metrics** → useEvaluation hook
- **GET /api/metrics/chart/<name>** → Metric charts (PNG)

### Traffic
- **GET /api/traffic/summary** → Traffic statistics
- **GET /api/traffic/live** → usePacketStream hook

### Other Endpoints
- **GET /api/logs** → Log file listing
- **GET /api/logs/<name>** → Log content
- **GET /api/feedback/status** → Feedback system status
- **GET /api/feedback/missed-attacks** → Missed attacks
- **GET /api/lab/hosts** → Lab container status
- **GET /api/lab/topology** → Network topology
- **GET /api/dashboard** → Combined data (master endpoint)

## HTTPS Configuration

### Development
- Uses HTTP on localhost:8000
- No HTTPS setup needed
- Vite proxy simplifies CORS

### Production
1. Update `frontend/.env.production`:
   ```
   VITE_API_BASE_URL=https://api.YOUR_DOMAIN
   ```

2. Set up reverse proxy (Nginx or Apache) with SSL

3. Obtain certificate from Let's Encrypt (free):
   ```bash
   sudo certbot certonly --nginx -d api.YOUR_DOMAIN
   ```

4. Update backend CORS in `app.py` or via `.env`:
   ```
   ALLOWED_ORIGINS=https://YOUR_DOMAIN
   ```

## Running the Project

### Development
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python3 app.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

Frontend: http://localhost:5173
Backend: http://localhost:8000

### Production
```bash
# Frontend
cd frontend
npm run build
# Deploy dist/ to web server

# Backend
cd backend && gunicorn -w 4 -b 0.0.0.0:8000 app:app
# Or use supervisord for process management
```

## Environment Variables

### Frontend
| Variable | Development | Production |
|----------|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | `https://api.YOUR_DOMAIN` |

### Backend (Optional)
| Variable | Default |
|----------|---------|
| `FLASK_ENV` | `development` |
| `ALLOWED_ORIGINS` | `*` |

## Data Flow

```
User Interface
    ↓
Panel Component (e.g., AgentFeedPanel)
    ↓
Hook (e.g., useAgentFeed)
    ↓
API Service (src/services/api.ts)
    ↓
Fetch with environment URL
    ↓
Flask Backend API
    ↓
Backend Data Sources
(CSV files, logs, Docker, system calls)
```

## Type Safety

All API responses are fully typed:
- `AgentMessagesResponse`
- `TrafficLiveResponse`
- `AlertsResponse`
- `MetricsResponse`
- Custom transform functions ensure frontend types match

## Error Handling

1. **Network Errors**: Displayed in panel error messages
2. **HTTP Errors**: Status code validation with error details
3. **JSON Parsing**: Graceful fallback to generic error message
4. **Polling**: Continues on error, doesn't retry aggressively

## Polling Intervals

| Hook | Interval | Reason |
|------|----------|--------|
| Agents | 3s | Medium-priority status |
| Traffic | 2s | Real-time feel |
| Alerts | 4s | Attack detection |
| Metrics | 8s | Expensive computation |

## Testing Checklist

### Development
- [x] Backend running on localhost:8000
- [x] Frontend running on localhost:5173  
- [x] TypeScript build succeeds
- [x] No CORS errors in console
- [x] All panel components render
- [x] API calls visible in Network tab
- [x] Error handling works

### Production
- [ ] Frontend built with .env.production
- [ ] Backend CORS configured for domain
- [ ] SSL certificates installed
- [ ] HTTPS reverse proxy running
- [ ] Frontend deployed to web server
- [ ] No mixed-content errors
- [ ] API calls use HTTPS URLs

## Security Notes

### Current
- Development: No authentication (localhost only)
- Any origin allowed (CORS *)

### Recommended for Production
1. Enable HTTPS (required)
2. Restrict CORS to known domains
3. Add API authentication (JWT or keys)
4. Monitor logs for suspicious activity
5. Regular SSL certificate renewal

## Performance Considerations

- Polling keeps UI responsive without WebSocket overhead
- Intervals tuned for perceived real-time feel
- Frontend caching possible for static endpoints
- Vite build optimization results in ~784KB JS

## Known Limitations

1. RL Training uses mock data (no backend endpoint)
2. One-way data flow (read-only API)
3. No real-time WebSocket updates (polling only)
4. Backend runs on single thread (production: use Gunicorn workers)

## Future Enhancements

- [ ] Add POST/PUT/DELETE for system control
- [ ] Implement WebSocket for true real-time updates
- [ ] Add request/response interceptors for logging
- [ ] Cache API responses where appropriate
- [ ] Add API authentication (JWT tokens)
- [ ] Implement exponential backoff for retries
- [ ] Add GraphQL layer for flexible queries

## Support & Documentation

- **API Details**: See `frontend/API_INTEGRATION.md`
- **Backend Setup**: See `BACKEND_CONFIG.md`
- **Deployment**: See `DEPLOYMENT.md`
- **Browser DevTools**: Network tab shows all API requests
- **Backend Logs**: Check Flask output for errors

## Verification

To verify integration is working:

```bash
# Terminal
curl http://localhost:8000/api/status
curl http://localhost:8000/api/alerts

# Browser
1. Open http://localhost:5173
2. Open DevTools → Network tab
3. Filter by /api
4. Should see regular GET requests
5. Panels should show data (if available)
```

## Contact & Issues

If API integration has issues:
1. Verify backend is running on correct port
2. Check browser console for error messages
3. Inspect Network tab for failed requests
4. Check backend logs for 500 errors
5. Ensure .env.local has correct VITE_API_BASE_URL

---

**Status**: ✅ Integration Complete  
**Build**: ✅ Passes TypeScript + Vite  
**Documentation**: ✅ Comprehensive guides included  
**Ready for**: Development & Production Deployment
