"""processor_advanced.py

A pragmatic starter implementation that:
- Accepts PDF or image bytes
- Attempts to extract text and images and assemble a simple HTML
- Renders to PDF using Playwright if available, otherwise falls back to a reportlab PDF

This file includes placeholders and safe fallbacks so you can run it without the full heavy dependencies.
"""
import io
from PIL import Image
import fitz
import base64
import os

def process_bytes_to_pdf(file_bytes: bytes, filename: str = 'input'):
    # Try to detect PDF vs image by looking at PDF header
    try:
        if filename.lower().endswith('.pdf') or file_bytes[:4]==b'%PDF':
            return process_pdf_bytes(file_bytes)
        else:
            return process_image_bytes(file_bytes)
    except Exception as e:
        raise

def process_pdf_bytes(pdf_bytes: bytes):
    # Simple extraction: extract page text and inline images, build minimal HTML
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    pages_html = []
    for page in doc:
        text = page.get_text('text')
        imgs = []
        for img in page.get_images(full=True):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            img_bytes = pix.tobytes('png')
            b64 = base64.b64encode(img_bytes).decode('ascii')
            imgs.append(f'<img src="data:image/png;base64,{b64}" style="max-width:100%;"/>')
        page_html = "<div class='page'><div class='text'>%s</div>%s</div>" % (text.replace('\n','<br/>'), ''.join(imgs))
        pages_html.append(page_html)
    html = HTML_TEMPLATE.format(content=''.join(pages_html), title='Reconstructed PDF')
    pdf = render_html_to_pdf(html)
    return pdf

def process_image_bytes(img_bytes: bytes):
    # OCR fallback: include image and attempt to place text below (basic)
    b64 = base64.b64encode(img_bytes).decode('ascii')
    html = HTML_TEMPLATE.format(content=f"<div class='page'><img src='data:image/png;base64,{b64}' style='max-width:100%;'/></div>",
                               title='Reconstructed Image')
    pdf = render_html_to_pdf(html)
    return pdf

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; padding: 20px; background-color: #111; color: #eee; }}
.page {{ page-break-after: always; margin-bottom: 20px; }}
.text {{ white-space: pre-wrap; }}
img {{ display:block; margin-top:10px; }}
</style>
</head>
<body>
{content}
</body>
</html>
"""

def render_html_to_pdf(html: str):
    # Try to render using playwright if available
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html)
            pdf_bytes = page.pdf(format='A4')
            browser.close()
            return pdf_bytes
    except Exception:
        # fallback: create a very basic PDF using reportlab
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib.utils import ImageReader
            from bs4 import BeautifulSoup
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=20*mm,leftMargin=20*mm,topMargin=20*mm,bottomMargin=20*mm)
            styles = getSampleStyleSheet()
            story = []
            soup = BeautifulSoup(html, 'html.parser')
            for div in soup.find_all(class_='page'):
                text_div = div.find(class_='text')
                if text_div:
                    txt = text_div.get_text()
                    story.append(Paragraph(txt.replace('\n','<br/>'), styles['BodyText']))
                    story.append(Spacer(1,6))
                for img in div.find_all('img'):
                    src = img.get('src')
                    if src.startswith('data:image'):
                        header, b64 = src.split(',',1)
                        img_bytes = base64.b64decode(b64)
                        imgf = ImageReader(io.BytesIO(img_bytes))
                        story.append(RLImage(imgf, width=400))
                        story.append(Spacer(1,6))
                # page break
            doc.build(story)
            buf.seek(0)
            return buf.read()
        except Exception as e:
            raise RuntimeError('No PDF renderer available: '+str(e))
