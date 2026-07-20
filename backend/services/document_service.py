import re
import html
import pdfplumber

def is_cjk(char: str) -> bool:
    if not char:
        return False
    code = ord(char)
    # Range for CJK Unified Ideographs, Symbols, and Fullwidth punctuation
    return (0x4E00 <= code <= 0x9FFF or 
            0x3000 <= code <= 0x303F or 
            0xFF00 <= code <= 0xFFEF or
            0x3400 <= code <= 0x4DBF)

def is_list_marker(line: str) -> bool:
    # Matches list indicators like "1.", "2. ", "一、", "二、", "- ", "* ", "• "
    return bool(re.match(r'^(\d+[\.\、]|\w+[\.\、]|[-*•●])\s*', line))

def join_paragraph_lines(lines: list[str]) -> str:
    merged = ""
    for i, line in enumerate(lines):
        if i == 0:
            merged = line
            continue
        
        if not merged:
            merged = line
            continue
            
        prev_char = merged[-1]
        curr_char = line[0] if line else ""
        
        # If either character is CJK, merge directly without space
        if is_cjk(prev_char) or is_cjk(curr_char):
            merged += line
        else:
            # English text: add space separator
            merged += " " + line
    return merged

def clean_and_format_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    
    # Split text into lines
    lines = raw_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            cleaned_lines.append("")
            continue
        
        # Filter page numbers (e.g., "- 1 -", "Page 2", "第 3 页")
        if re.match(r'^[-—\s]*\d+[-—\s]*$', line_str):
            continue
        if re.match(r'^(page|Page)\s*\d+$', line_str):
            continue
        if re.match(r'^第\s*\d+\s*页$', line_str):
            continue
            
        cleaned_lines.append(line_str)
        
    # Merge lines, respecting paragraph double newlines and list indicators
    merged_text = ""
    current_paragraph = []
    
    for line in cleaned_lines:
        if line == "":
            if current_paragraph:
                merged_text += join_paragraph_lines(current_paragraph) + "\n\n"
                current_paragraph = []
        elif is_list_marker(line):
            if current_paragraph:
                merged_text += join_paragraph_lines(current_paragraph) + "\n\n"
                current_paragraph = []
            current_paragraph.append(line)
        else:
            current_paragraph.append(line)
            
    if current_paragraph:
        merged_text += join_paragraph_lines(current_paragraph)
        
    return merged_text.strip()

def extract_text_from_pdf(pdf_path: str) -> str:
    raw_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"
    return raw_text

def slice_long_image(image_path: str, max_height: int = 1000) -> list[bytes]:
    try:
        from PIL import Image
        import io
    except ImportError:
        # Fallback if Pillow is not available, just return the whole image bytes
        with open(image_path, "rb") as f:
            return [f.read()]

    try:
        img = Image.open(image_path)
        # Ensure RGB to avoid issues with alpha channels when saving as JPEG
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert('RGB')
            
        width, height = img.size
        
        # If the image is not that tall, just return it as a single piece
        if height <= max_height or height <= width * 1.2:
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=95)
            return [buf.getvalue()]
            
        # It's a long image, we need to slice it smartly.
        # Convert to grayscale and resize to 1 pixel width to get average row brightness
        gray = img.convert('L')
        row_averages = gray.resize((1, height))
        pixels = row_averages.load()
        
        pieces = []
        current_y = 0
        
        while current_y < height:
            # We want to find a cut point between current_y + max_height*0.7 and current_y + max_height
            target_y = min(current_y + max_height, height)
            
            if target_y == height:
                box = (0, current_y, width, target_y)
                cropped = img.crop(box)
                buf = io.BytesIO()
                cropped.save(buf, format='JPEG', quality=95)
                pieces.append(buf.getvalue())
                break
                
            # Search for a good cut point (white space) in a window before target_y
            search_start = int(current_y + max_height * 0.7)
            search_end = target_y
            
            best_cut_y = target_y
            best_white_score = 0
            
            for y in range(search_end, search_start, -1):
                # We check a small band of pixels (e.g. 5 pixels high) if possible, but 1 row is ok for simple cases
                brightness = pixels[0, y]
                if brightness > best_white_score:
                    best_white_score = brightness
                    best_cut_y = y
                if best_white_score >= 253:  # Found a very white row, cut here!
                    best_cut_y = y
                    break
                    
            box = (0, current_y, width, best_cut_y)
            cropped = img.crop(box)
            buf = io.BytesIO()
            cropped.save(buf, format='JPEG', quality=95)
            pieces.append(buf.getvalue())
            
            current_y = best_cut_y
            
        return pieces
    except Exception as e:
        # Fallback to reading the raw bytes if anything goes wrong
        from logger import logger
        logger.error(f"Image slicing failed, falling back to raw image: {str(e)}")
        with open(image_path, "rb") as f:
            return [f.read()]

def extract_text_with_llm(file_path: str, progress_callback=None) -> str:
    import fitz
    import base64
    import os
    import traceback
    from openai import OpenAI
    from logger import logger

    # Read configuration from environment
    API_KEY = os.environ.get("LLM_API_KEY", "")
    BASE_URL = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "hunyuan-vision")
    HUNYUAN_API_KEY = os.environ.get("HUNYUAN_API_KEY", "")

    # Validate required keys early and provide helpful error messages
    if MODEL_NAME.startswith("hunyuan") and not HUNYUAN_API_KEY:
        raise Exception("HUNYUAN_API_KEY is not set. Please set this environment variable to use hunyuan models.")
    if not MODEL_NAME.startswith("hunyuan") and not API_KEY:
        raise Exception("LLM_API_KEY is not set. Please set this environment variable to use the configured LLM model.")

    # Initialize client
    if MODEL_NAME.startswith("hunyuan"):
        client = OpenAI(
            api_key=HUNYUAN_API_KEY,
            base_url="https://api.hunyuan.cloud.tencent.com/v1"
        )
    else:
        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL if BASE_URL else None
        )

    instruction = (
        "【绝对指令】你是一个极其严格的 OCR 文本提取机器人。你的唯一任务是逐字逐句地识别并提取图片中的「正文文本」，并且不要对内容做任何主观概括或总结！\n"
        "1. 严禁概括：禁止使用“由于图片文字密集...”、“根据图表显示...”等概括性、描述性的废话。必须输出原文！\n"
        "2. 严禁解释：不要输出任何抱歉的话语，即使文字模糊，也要尽你最大可能去识别。\n"
        "3. 图表处理：遇到纯图表可以跳过里面的数据，但【必须】提取图表上方、下方和周围的段落文字、分析说明！\n"
        "4. 格式清洗：自动忽略斜向水印、背景文字以及页眉页脚；遇到被换行截断的句子，请拼接完整。\n"
        "只需返回排版好的纯文本，无需加 Markdown 标记，不要回答任何与原文无关的话。"
    )
    
    extracted_text_parts = []
    
    is_pdf = file_path.lower().endswith('.pdf')
    
    if is_pdf:
        # Open PDF and convert pages to base64-encoded JPEGs
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            mat = fitz.Matrix(4.0, 4.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("jpeg")
            base64_img = base64.b64encode(img_bytes).decode('utf-8')
            
            content = [
                {"type": "text", "text": instruction},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                }
            ]
            
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": content}],
                    temperature=0.01
                )
                try:
                    page_text = response.choices[0].message.content.strip()
                except Exception:
                    try:
                        page_text = response.choices[0].text.strip()
                    except Exception:
                        page_text = str(response).strip()
                
                extracted_text_parts.append(page_text)
                logger.info(f"Successfully extracted text for page {page_num + 1}/{len(doc)}")
                
                if progress_callback:
                    progress_callback(((page_num + 1) / len(doc)) * 100)
            except Exception as e:
                logger.error(f"LLM extraction failed on page {page_num + 1}: {str(e)}", exc_info=True)
                raise Exception(f"LLM extraction failed on page {page_num + 1}: {str(e)}")
    else:
        # Native Image Process with Smart Slicing
        image_pieces = slice_long_image(file_path, max_height=1000)
        
        # DEBUG: 将切片图片临时保存到 backend/temp_slices 目录供本地查看 (默认关闭)
        DEBUG_SAVE_SLICES = False
        
        if DEBUG_SAVE_SLICES:
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_slices")
            os.makedirs(debug_dir, exist_ok=True)
            try:
                # 清理旧的切片
                for f in os.listdir(debug_dir):
                    if f.endswith('.jpg') or f.endswith('.png'):
                        os.remove(os.path.join(debug_dir, f))
            except Exception as e:
                logger.warning(f"Failed to clear old slices: {e}")
                
            for i, img_bytes in enumerate(image_pieces):
                with open(os.path.join(debug_dir, f"slice_{i}.jpg"), "wb") as f:
                    f.write(img_bytes)
                
        for i, img_bytes in enumerate(image_pieces):
            mime_type = "image/jpeg" # slice_long_image returns JPEG bytes by default
            
            # If it returned raw bytes because of fallback and it's png/webp
            if len(image_pieces) == 1:
                if file_path.lower().endswith(".png"):
                    mime_type = "image/png"
                elif file_path.lower().endswith(".webp"):
                    mime_type = "image/webp"
                
            base64_img = base64.b64encode(img_bytes).decode('utf-8')
            
            content = [
                {"type": "text", "text": instruction},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_img}"
                    }
                }
            ]
            
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": content}],
                    temperature=0.01
                )
                try:
                    page_text = response.choices[0].message.content.strip()
                except Exception:
                    try:
                        page_text = response.choices[0].text.strip()
                    except Exception:
                        page_text = str(response).strip()
                
                extracted_text_parts.append(page_text)
                logger.info(f"Successfully extracted text from image slice {i + 1}/{len(image_pieces)}.")
                
                if progress_callback:
                    progress_callback(((i + 1) / len(image_pieces)) * 100)
            except Exception as e:
                logger.error(f"LLM extraction failed for image slice {i + 1}: {str(e)}", exc_info=True)
                raise Exception(f"LLM extraction failed for image slice {i + 1}: {str(e)}")
            
    return "\n\n".join(extracted_text_parts)


def inject_pauses(cleaned_text: str, sentence_pause_ms: int = 800, paragraph_pause_ms: int = 1500) -> str:
    # Normalize consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    # Just return the text. edge-tts relies on natural punctuation marks and line breaks for proper prosody.
    # We do not return SSML XML here because edge-tts doesn't parse it (it reads tags like `<break>` out loud literal).
    return text
