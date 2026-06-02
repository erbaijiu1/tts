import os
import uuid
import edge_tts
import re
from typing import Callable, Awaitable, Optional

async def synthesize_text_to_audio(
    text: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+0%",
    output_dir: str = "data/output_audio",
    progress_callback: Optional[Callable[[float], Awaitable[None]]] = None
) -> str:
    """
    Synthesizes text to MP3 using edge-tts. Supports chunking and progress reporting.
    
    Args:
        text (str): The cleaned text.
        voice (str): The voice model to use.
        rate (str): The speed rate, e.g., "+10%" or "-5%".
        output_dir (str): Relative directory to store the MP3 file.
        progress_callback: Optional async function to report progress.
        
    Returns:
        str: The filename of the generated MP3 file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Generate unique UUID filename
    filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_dir, filename)
    
    # Split text into chunks to report progress
    # edge-tts safely handles up to ~4096 bytes. We chunk by ~1000 characters 
    # to ensure safe boundaries and granular progress reporting.
    paragraphs = [p for p in re.split(r'(\n+)', text) if p]
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) > 1000 and current_chunk.strip():
            chunks.append(current_chunk)
            current_chunk = p
        else:
            current_chunk += p
    if current_chunk.strip():
        chunks.append(current_chunk)
        
    if not chunks:
        chunks = [" "] # Fallback for empty text

    with open(output_path, "wb") as f:
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            communicate = edge_tts.Communicate(text=chunk, voice=voice, rate=rate)
            async for message in communicate.stream():
                if message["type"] == "audio":
                    f.write(message["data"])
            
            if progress_callback:
                await progress_callback(((i + 1) / len(chunks)) * 100)
                
    return filename
