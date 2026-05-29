import os
import shutil
import uuid
from fastapi import FastAPI, APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from database import engine, Base, get_db
from models import AudioTask
from services.document_service import extract_text_from_pdf, clean_and_format_text, inject_pauses
from services.tts_service import synthesize_text_to_audio

PROJECT_NAME = os.getenv("PROJECT_NAME", "tts")

app = FastAPI(
    title=f"{PROJECT_NAME} API"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
OUTPUT_AUDIO_DIR = os.path.join(DATA_DIR, "output_audio")

for d in [UPLOAD_DIR, OUTPUT_AUDIO_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Mount static files to serve the generated MP3s
app.mount(f"/{PROJECT_NAME}/static", StaticFiles(directory=OUTPUT_AUDIO_DIR), name="static")

# Database initialization
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create tables if they do not exist
        await conn.run_sync(Base.metadata.create_all)

# Pydantic schemas
class SynthesizeRequest(BaseModel):
    text: str
    filename: Optional[str] = "Direct Input"
    voice: Optional[str] = "zh-CN-XiaoxiaoNeural"
    rate: Optional[str] = "+0%"
    sentence_pause_ms: Optional[int] = 800
    paragraph_pause_ms: Optional[int] = 1500

# Create prefix router
router = APIRouter(prefix=f"/{PROJECT_NAME}/api")

@router.get("/health")
async def health_check():
    return {"status": "ok", "project": PROJECT_NAME}

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint to receive a PDF file, extract text, clean layout, and return it.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(UPLOAD_DIR, temp_filename)
    
    try:
        # Save file locally
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Parse PDF text
        raw_text = extract_text_from_pdf(temp_path)
        cleaned_text = clean_and_format_text(raw_text)
        
        return {
            "filename": file.filename,
            "raw_text_length": len(raw_text),
            "cleaned_text_length": len(cleaned_text),
            "cleaned_text": cleaned_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/synthesize")
async def synthesize_text(
    request: Request,
    payload: SynthesizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint to inject pauses and synthesize text asynchronously, returning the MP3 URL.
    """
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty.")
        
    try:
        # Inject SSML breaks
        ssml_text = inject_pauses(
            payload.text,
            sentence_pause_ms=payload.sentence_pause_ms,
            paragraph_pause_ms=payload.paragraph_pause_ms
        )
        
        # Async synthesize voice
        mp3_filename = await synthesize_text_to_audio(
            ssml_text=ssml_text,
            voice=payload.voice,
            rate=payload.rate,
            output_dir=OUTPUT_AUDIO_DIR
        )
        
        # Resolve request host for absolute URL
        host = request.headers.get("host", "localhost")
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        audio_url = f"{scheme}://{host}/{PROJECT_NAME}/static/{mp3_filename}"
        
        # Log task into database
        new_task = AudioTask(
            filename=payload.filename,
            text_snippet=payload.text[:100] + ("..." if len(payload.text) > 100 else ""),
            audio_url=audio_url,
            voice=payload.voice,
            rate=payload.rate
        )
        
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        
        return {
            "task_id": new_task.id,
            "filename": new_task.filename,
            "audio_url": audio_url,
            "created_at": new_task.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

@router.get("/tasks")
async def get_tasks_history(
    db: AsyncSession = Depends(get_db),
    limit: int = 20
):
    """
    Retrieves the history of voice synthesis tasks from PostgreSQL.
    """
    try:
        query = select(AudioTask).order_by(AudioTask.created_at.desc()).limit(limit)
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return [
            {
                "id": task.id,
                "filename": task.filename,
                "text_snippet": task.text_snippet,
                "audio_url": task.audio_url,
                "voice": task.voice,
                "rate": task.rate,
                "created_at": task.created_at
            }
            for task in tasks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks history: {str(e)}")

app.include_router(router)
