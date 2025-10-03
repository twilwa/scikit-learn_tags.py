# Testing Folder Upload

## Quick Test

### Option 1: Using curl

```bash
# Create a test log file
echo '{"type":"test","data":"hello"}' > /tmp/test.jsonl

# Upload it
curl -X POST http://localhost:8000/api/sessions/folder \
  -F "files=@/tmp/test.jsonl" \
  -F "encryption_enabled=false" \
  -v
```

### Option 2: Using the UI

1. Start the backend:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

2. Open browser: http://localhost:8000/netlify-frontend/

3. Click orange "Folder" button

4. Select any .jsonl or .json file

5. Click "analyze folder"

6. Check terminal for debug output

## Common Issues

### "Failed to fetch"

**Possible causes**:
1. Backend not running
2. CORS issue
3. Port mismatch

**Check**:
```bash
# Is backend running?
curl http://localhost:8000/health

# Check CORS
curl -X OPTIONS http://localhost:8000/api/sessions/folder -v
```

### "405 Method Not Allowed"

**Cause**: Wrong HTTP method or endpoint not registered

**Check**:
```bash
# List all routes
curl http://localhost:8000/docs
# Should show /api/sessions/folder with POST
```

### "500 Internal Server Error"

**Check backend logs** - will show:
```
[FOLDER UPLOAD] Error: <actual error>
<traceback>
```

## Debug Checklist

- [ ] Backend running on port 8000
- [ ] Can access http://localhost:8000/docs
- [ ] Can see POST /api/sessions/folder in docs
- [ ] SUPABASE env vars set in .env
- [ ] FolderParser imports working
- [ ] Sessions table exists in database

## Manual Database Check

If you have database issues:

```python
from backend.database import get_supabase

supabase = get_supabase()

# Test insert
result = supabase.table("sessions").insert({
    "session_url": "test-123",
    "log_content": "test",
    "status": "uploading"
}).execute()

print(result)
```

## Expected Flow

1. Files uploaded via multipart/form-data
2. Backend logs: `[FOLDER UPLOAD] Received N files`
3. Files saved to temp directory
4. FolderParser processes files
5. Inserts into sessions table
6. Returns session_url + metadata
7. Frontend starts polling for results

## What To Look For In Logs

**Success**:
```
[FOLDER UPLOAD] Received 3 files
  - session1.jsonl
  - config.json
  - mcp.json
[FOLDER UPLOAD] Supabase client initialized
[FOLDER UPLOAD] Success! Session URL: abc-123-def
```

**Failure**:
```
[FOLDER UPLOAD] Received 1 files
  - test.jsonl
[FOLDER UPLOAD] Supabase client initialized
[FOLDER UPLOAD] Error: <error message>
<full traceback>
```

## Next Steps After Successful Upload

1. Session created in database
2. Background analysis starts
3. Frontend polls /api/sessions/{session_url}
4. Results appear in UI progressively
5. Insights generated
6. Visualizations rendered

## Browser Console Debugging

Open browser console and paste:

```javascript
// Test folder upload directly
const formData = new FormData();
const blob = new Blob([JSON.stringify({type: "test"})], {type: 'application/json'});
const file = new File([blob], "test.jsonl", {type: "application/json"});
formData.append('files', file);
formData.append('encryption_enabled', 'false');

fetch('http://localhost:8000/api/sessions/folder', {
    method: 'POST',
    body: formData
})
.then(r => r.json())
.then(d => console.log('Success:', d))
.catch(e => console.error('Error:', e));
```

Should see response with `session_url` and metadata.
