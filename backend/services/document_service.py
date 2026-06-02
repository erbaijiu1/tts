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

def extract_text_with_llm(pdf_path: str, progress_callback=None) -> str:
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

    # Open PDF and convert pages to base64-encoded JPEGs
    doc = fitz.open(pdf_path)
    instruction = (
        "你是一个专业的 OCR 和适合「听书」的文本排版助手。请提取图片中的全部正文内容，自动忽略并去除所有斜向水印、背景文字以及页眉页脚。"
        "如果遇到被换行截断的句子，请拼接完整。"
        "【重要要求】：这份文本将被直接用于语音合成（TTS）朗读。如果图片中包含「表格、对比图、思维导图」等多维结构，"
        "请千万不要按字面生硬拼接，而是将其转化为适合听众理解的「自然语言叙述」或「线性陈述」。"
        "例如：不要输出“产品：股票50 | 收入方式 ： 前端”，而是转化为完整的陈述句：“产品股票50的收入方式为前端”。"
        "只需返回排版好的纯文本，无需加 Markdown 标记，无需解释。"
    )
    
    extracted_text_parts = []
    
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
            # Best-effort extraction of text from response
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
            
    return "\n\n".join(extracted_text_parts)


def inject_pauses(cleaned_text: str, sentence_pause_ms: int = 800, paragraph_pause_ms: int = 1500) -> str:
    # Normalize consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    # Just return the text. edge-tts relies on natural punctuation marks and line breaks for proper prosody.
    # We do not return SSML XML here because edge-tts doesn't parse it (it reads tags like `<break>` out loud literal).
    return text
