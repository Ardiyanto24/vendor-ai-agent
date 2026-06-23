import os
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import httpx

from routers.v1.agent import router as agent_router

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "")

# App initialization
app = FastAPI(
    title="Vendor AI Agent Service",
    description="FastAPI service for AI agent orchestration, TOPSIS scoring, and RAG search",
    version="1.0.0"
)

# Start time for uptime calculation
start_time = time.time()

# CORS Middleware Setup
if ALLOWED_ORIGINS:
    origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)

# Initialize Supabase client
supabase_client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")

# Service Token Verification Middleware
@app.middleware("http")
async def verify_service_token(request: Request, call_next):
    path = request.url.path
    # Exclude endpoints: /health, /v1/chat/stream, and api documentation
    if path == "/health" or path.startswith("/v1/chat/stream") or path in ("/docs", "/redoc", "/openapi.json"):
        return await call_next(request)
    
    # Check X-Service-Token header
    token = request.headers.get("X-Service-Token")
    if not token or token != SERVICE_TOKEN:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized: Invalid service token"}
        )
    
    return await call_next(request)

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify status of dependencies:
    - Supabase (database query)
    - OpenRouter API (ping test)
    - Google Gemini API (existence)
    - Tavily API (existence)
    """
    supabase_status = "failed"
    openrouter_status = "failed"
    google_status = "failed"
    tavily_status = "failed"
    
    # 1. Verify Supabase
    if supabase_client:
        try:
            # Attempt to query 1 row from user or konfigurasi_kriteria table to verify DB connectivity
            # If database table doesn't exist yet, we catch the exception.
            # We can also do a simple check like listing bucket metadata or getting schema
            # Let's try selecting from 'konfigurasi_kriteria' table (created in F-00)
            response = supabase_client.table("konfigurasi_kriteria").select("*").limit(1).execute()
            if response is not None:
                supabase_status = "ok"
        except Exception as e:
            print(f"Supabase connection test failed: {e}")
            # Fallback check: try query to user table
            try:
                response = supabase_client.table("user").select("*").limit(1).execute()
                if response is not None:
                    supabase_status = "ok"
            except Exception as e2:
                print(f"Supabase fallback connection test failed: {e2}")
                # If both fail but client exists, we set failed but it could be due to missing tables.
                # However, F-00 DB says 'user' and 'konfigurasi_kriteria' must be created, so it's a valid test.
                supabase_status = "failed"
    
    # 2. Verify OpenRouter API Key via simple ping
    if OPENROUTER_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            # Perform a light models list call to check API key validity
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    openrouter_status = "ok"
                else:
                    print(f"OpenRouter ping returned status code {resp.status_code}: {resp.text}")
                    openrouter_status = "failed"
        except Exception as e:
            print(f"OpenRouter ping failed: {e}")
            openrouter_status = "failed"
            
    # 3. Verify Google Gemini API Key presence
    if GOOGLE_API_KEY:
        google_status = "ok"
        
    # 4. Verify Tavily API Key presence
    if TAVILY_API_KEY:
        tavily_status = "ok"
        
    # Determine overall status
    overall_status = "ok"
    if any(status == "failed" for status in (supabase_status, openrouter_status, google_status, tavily_status)):
        overall_status = "degraded"
        
    uptime = time.time() - start_time
    
    return {
        "status": overall_status,
        "supabase": supabase_status,
        "openrouter": openrouter_status,
        "google": google_status,
        "tavily": tavily_status,
        "uptime_seconds": round(uptime, 2),
        "version": "1.0.0"
    }

# Stub route for SSE Chat Streaming so it bypasses auth middleware and is ready
@app.get("/v1/chat/stream")
async def chat_stream():
    raise HTTPException(status_code=501, detail="Not Implemented")
