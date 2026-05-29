import os
import uuid
import edge_tts

async def synthesize_text_to_audio(
    ssml_text: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+0%",
    output_dir: str = "data/output_audio"
) -> str:
    """
    Synthesizes SSML text to MP3 using edge-tts.
    
    Args:
        ssml_text (str): The cleaned text with SSML break tags.
        voice (str): The voice model to use.
        rate (str): The speed rate, e.g., "+10%" or "-5%".
        output_dir (str): Relative directory to store the MP3 file.
        
    Returns:
        str: The filename of the generated MP3 file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Generate unique UUID filename
    filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_dir, filename)
    
    # Wrap text in Microsoft TTS SSML with prosody rate
    ssml_content = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
<voice name="{voice}">
<prosody rate="{rate}">
{ssml_text}
</prosody>
</voice>
</speak>"""

    communicate = edge_tts.Communicate(text=ssml_content)
    await communicate.save(output_path)
    
    return filename
