# Frontend Proxy Configuration

## ⚠️ IMPORTANT: Do Not Change Proxy Settings

The frontend uses a **Vite development proxy** to forward API requests to the backend. This configuration **must remain consistent** across all pages.

---

## How It Works

### Development Mode

**Frontend**: Runs on `http://localhost:3000` (Vite dev server)  
**Backend**: Runs on `http://localhost:8000` or `http://backend:8000` (Docker)

**Proxy Flow**:
1. Browser requests: `http://localhost:3000/api/something`
2. Vite proxy intercepts requests to `/api/*`
3. Vite forwards to: `http://backend:8000/api/something`
4. Backend responds
5. Vite returns response to browser

### Configuration Files

#### 1. `vite.config.ts`
```typescript
proxy: {
  '/api': {
    target: 'http://backend:8000',  // ⚠️ DO NOT CHANGE
    changeOrigin: true,
    secure: false,
  },
}
```

**Rule**: The `target` must **always** be `http://backend:8000`

#### 2. `src/api/client.ts`
```typescript
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || ''
```

**Rule**: The default `API_BASE_URL` must be an **empty string** so axios uses relative URLs.

When `baseURL` is empty:
- ✅ Axios makes requests to `/api/...` (relative)
- ✅ Vite proxy intercepts and forwards to backend:8000

When `baseURL` is `http://localhost:8000`:
- ❌ Axios makes requests to `http://localhost:8000/api/...` (absolute)
- ❌ Vite proxy is bypassed
- ❌ Requests fail or go to wrong port

---

## Environment Variables

### Development (.env.development)
```bash
# Leave empty to use Vite proxy
VITE_API_URL=
```

### Production (.env.production)
```bash
# Set to actual backend URL
VITE_API_URL=https://api.nex.ai
```

---

## Common Issues

### Issue: "Some pages use port 3000, others use port 8000"

**Cause**: `API_BASE_URL` was set to `http://localhost:8000`

**Fix**: 
1. Check `src/api/client.ts` - ensure default is empty string `''`
2. Check `.env.development` - ensure `VITE_API_URL` is empty or not set
3. Restart Vite dev server: `docker-compose restart frontend`

### Issue: "API requests fail with CORS errors"

**Cause**: Proxy not working, requests going directly to backend

**Fix**:
1. Verify Vite proxy is configured in `vite.config.ts`
2. Verify `API_BASE_URL` is empty (relative URLs)
3. Check Docker network - frontend and backend must be on same network

### Issue: "Proxy works in one branch but not another"

**Cause**: Someone changed the configuration

**Fix**:
1. Compare `src/api/client.ts` between branches
2. Ensure `API_BASE_URL` default is empty string
3. Ensure no hardcoded URLs in API calls

---

## Testing Proxy Configuration

### 1. Check Network Tab
Open browser DevTools → Network tab

**Correct** ✅:
- Request URL: `http://localhost:3000/api/v1/...`
- Status: 200
- No CORS errors

**Incorrect** ❌:
- Request URL: `http://localhost:8000/api/v1/...`
- Status: CORS error or connection refused

### 2. Check Console
No errors related to:
- "Failed to fetch"
- "CORS policy"
- "Network Error"

### 3. Test API Call
```javascript
// In browser console
fetch('/api/v1/health')
  .then(r => r.json())
  .then(console.log)
```

Should return backend health status without errors.

---

## Production Deployment

In production, the frontend and backend are typically on different domains:
- Frontend: `https://app.nex.ai`
- Backend: `https://api.nex.ai`

**Production Configuration**:

1. Set environment variable:
   ```bash
   VITE_API_URL=https://api.nex.ai
   ```

2. Build frontend:
   ```bash
   npm run build
   ```

3. Backend must have CORS configured to allow `app.nex.ai`

---

## Rules Summary

✅ **DO**:
- Keep `API_BASE_URL` default as empty string in `client.ts`
- Keep Vite proxy target as `http://backend:8000` in `vite.config.ts`
- Use relative URLs for all API calls (`/api/...`)
- Set `VITE_API_URL` only in production

❌ **DON'T**:
- Change the Vite proxy target
- Set `API_BASE_URL` to `http://localhost:8000` as default
- Use absolute URLs in API client functions
- Bypass the proxy in development

---

## Troubleshooting Checklist

If API calls are failing:

- [ ] Check `src/api/client.ts` - is `API_BASE_URL` default empty?
- [ ] Check `vite.config.ts` - is proxy target `http://backend:8000`?
- [ ] Check `.env.development` - is `VITE_API_URL` empty or unset?
- [ ] Restart frontend: `docker-compose restart frontend`
- [ ] Clear browser cache and hard reload
- [ ] Check browser console for errors
- [ ] Check browser network tab for request URLs
- [ ] Verify backend is running: `docker ps`
- [ ] Test backend directly: `curl http://localhost:8000/api/v1/health`

---

## Contact

If you need to change the proxy configuration, please:
1. Document the reason
2. Update this file
3. Test all pages (Data Dictionary, ML Development, Chat, etc.)
4. Verify no CORS errors
5. Commit changes with clear explanation

**Last Updated**: 2025-12-17  
**Configuration Status**: ✅ Fixed - All pages now use consistent proxy

