from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import cloudscraper
import requests
import fitz  # PyMuPDF
import google.generativeai as genai
import os

app = Flask(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY")

def extract_text_from_url(url):
    try:
        scraper = cloudscraper.create_scraper()
        res = scraper.get(url, timeout=15)
        if res.status_code != 200:
            return f"❌ Lỗi truy cập URL (HTTP {res.status_code})"

        soup = BeautifulSoup(res.text, 'html.parser')
        content_div = soup.find('div', class_='text-content')
        if content_div:
            return content_div.get_text(separator='\n', strip=True)

        title = soup.title.string if soup.title else ""
        headings = ' '.join(h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3']))
        paragraphs = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))
        content = f"{title}\n{headings}\n{paragraphs}"
        return content.strip() if content.strip() else "⚠️ Không tìm thấy nội dung trong bài viết."
    except Exception as e:
        return f"❌ Lỗi khi truy cập bài viết: {str(e)}"

def extract_text_from_pdf_url(url):
    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            return f"❌ Lỗi tải PDF (HTTP {res.status_code})"
        with open("temp.pdf", "wb") as f:
            f.write(res.content)
        doc = fitz.open("temp.pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip() if text.strip() else "⚠️ PDF không có nội dung."
    except Exception as e:
        return f"❌ Lỗi khi đọc PDF: {str(e)}"

def summarize_with_gemini(text):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(f"Tóm tắt nội dung sau bằng tiếng Việt:\n\n{text}")
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi tóm tắt bằng Gemini: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = None
    content = None
    url = ""
    if request.method == 'POST':
        url = request.form['url']
        if url.lower().endswith('.pdf'):
            content = extract_text_from_pdf_url(url)
        else:
            content = extract_text_from_url(url)
        if content.startswith("❌") or content.startswith("⚠️"):
            summary = content
        else:
            summary = summarize_with_gemini(content)
    return render_template('index.html', summary=summary, url=url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
