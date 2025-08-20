import os
import httpx
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent
# Load environment variables from .env file in the same directory as main.py
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Initialize FastAPI app
app = FastAPI()

# CORS configuration
# It's better to be specific in production, but for development,
# allowing localhost ports is common.
origins = [
    "http://localhost:3000",  # Default create-react-app port
    "http://localhost:5173",  # Default Vite port
    "http://127.0.0.1:5173", # Another way to access Vite
    "http://localhost:7860", # Default Gradio port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for validating the request body
class GenerationRequest(BaseModel):
    model: str
    prompt: str

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.get("/")
def read_root():
    """A simple endpoint to confirm the backend is running."""
    return {"message": "AI Book Creator Backend is running"}

@app.post("/api/generate")
async def generate_text(request: GenerationRequest):
    """
    Receives a model and a prompt, sends it to OpenRouter,
    and streams the response back.
    """
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY environment variable not set."
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost", # Optional, but recommended by OpenRouter
        "X-Title": "AI Book Creator", # Optional, for identifying your app
    }

    data = {
        "model": request.model,
        "messages": [
            {"role": "user", "content": request.prompt}
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_API_URL, headers=headers, json=data, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as http_err:
        # Sanitize error message from OpenRouter before returning to client
        try:
            # Optionally log the full error detail for internal debugging
            logging.error(f"OpenRouter API error: {http_err.response.text}")
        except Exception:
            pass # Ignore logging errors

        sanitized_message = "An error occurred while communicating with the AI model provider."
        raise HTTPException(
            status_code=http_err.response.status_code, detail=sanitized_message
        ) from http_err

    except httpx.RequestError as e:
        # For network errors, timeouts, etc.
        logging.error(f"Network error calling OpenRouter API: {e}")
        raise HTTPException(
            status_code=500, detail="A network error occurred while communicating with the AI model provider."
        ) from e
