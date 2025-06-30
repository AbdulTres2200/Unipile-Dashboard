from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

# Import routes
from routes.auth import router as auth_router
from routes.webhooks import router as webhook_router
from routes.simple_messages import router as message_router
from routes.messages import router as messages_people_router
from routes.linkedinsearch import router as linkedinsearch_router


# Create FastAPI app with Swagger enabled
app = FastAPI(
    title="Unified Timeline API",
    description="Real Gmail + LinkedIn message import via Unipile",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # Alternative docs
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(webhook_router, prefix="/api", tags=["Webhooks"])
app.include_router(message_router, prefix="/api/messages", tags=["Messages"])
app.include_router(messages_people_router, prefix="/api", tags=["People"])
app.include_router(linkedinsearch_router, prefix="/api", tags=["LinkedIn"])

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Unified Timeline API - Real Message Import",
        "docs": "Visit /docs for Swagger UI",
        "endpoints": {
            "auth": "/api/auth",
            "messages": "/api/messages"
        }
    }