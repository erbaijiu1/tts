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

def extract_text_with_llm(pdf_path: str) -> str:
    import fitz
    import base64
    import os
    from openai import OpenAI
    
    API_KEY = os.environ.get("LLM_API_KEY", "")
    BASE_URL = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "hunyuan-vision")
    HUNYUAN_API_KEY = os.environ.get("HUNYUAN_API_KEY", "")
    
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
    
    doc = fitz.open(pdf_path)
    content = [{"type": "text", "text": "你是一个专业的 OCR 和文本排版助手。请提取图片中的全部正文内容，自动忽略并去除所有斜向水印、背景文字以及页眉页脚。如果遇到被换行截断的句子，请拼接完整。只需返回纯文本，无需解释。"}]
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        mat = fitz.Matrix(4.0, 4.0)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("jpeg")
        base64_img = base64.b64encode(img_bytes).decode('utf-8')
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_img}"
            }
        })
        
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": content}],
            temperature=0.01
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        import traceback
        with open("/app/data/llm_error.log", "w") as f:
            f.write(traceback.format_exc())
        raise e


def inject_pauses(cleaned_text: str, sentence_pause_ms: int = 800, paragraph_pause_ms: int = 1500) -> str:
    # Normalize consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    paragraphs = text.split('\n\n')
    processed_paragraphs = []
    
    for para in paragraphs:
        # Chinese sentence endings
        p = re.sub(r'([。！？；])', r'\1[SENT_BREAK]', para)
        
        # English sentence endings
        p = re.sub(r'([\.!\?])(\s+|$)', r'\1[SENT_BREAK]\2', p)
        
        # Handle line-based items (such as list items)
        lines = p.split('\n')
        processed_lines = []
        for line in lines:
            if is_list_marker(line):
                # Prepend list pause placeholder
                processed_lines.append(f"[LIST_BREAK]{line}")
            else:
                processed_lines.append(line)
        
        p = "\n".join(processed_lines)
        processed_paragraphs.append(p)
        
    # Combine paragraphs with paragraph break placeholder
    full_text = "[PARA_BREAK]".join(processed_paragraphs)
    
    # Escape HTML to make text XML/SSML safe
    escaped_text = html.escape(full_text)
    
    # Replace placeholders with raw SSML tags
    escaped_text = escaped_text.replace('[SENT_BREAK]', f'<break time="{sentence_pause_ms}ms" />')
    escaped_text = escaped_text.replace('[PARA_BREAK]', f'<break time="{paragraph_pause_ms}ms" />')
    escaped_text = escaped_text.replace('[LIST_BREAK]', f'<break time="{paragraph_pause_ms}ms" />')
    
    return escaped_text
