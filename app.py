from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os

app = Flask(__name__)

# Thêm API Key Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-pro")

def extract_text_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            return f"❌ Lỗi truy cập URL (HTTP {res.status_code})"

        soup = BeautifulSoup(res.text, 'html.parser')

        # Ưu tiên lấy nội dung chính từ class text-content
        content_div = soup.find('div', class_='text-content')
        if content_div:
            return content_div.get_text(separator='\n', strip=True)

        # Nếu không có, fallback về tiêu đề + heading + <p>
        title = soup.title.string if soup.title else ""
        headings = ' '.join(h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3']))
        paragraphs = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))

        content = f"{title}\n{headings}\n{paragraphs}"
        return content.strip() if content.strip() else "⚠️ Không tìm thấy nội dung trong bài viết."
    except Exception as e:
        return f"❌ Lỗi khi truy cập bài viết: {str(e)}"
    
@app.route('/', methods=['GET', 'POST'])
def index():
    summary = ""
    if request.method == 'POST':
        url = request.form['url']
        article = extract_text_from_url(url)
        if article.startswith("❌"):
            summary = article
        elif not article:
            summary = "⚠️ Không tìm thấy nội dung trong bài viết."
        else:
            prompt = f"Tóm tắt nội dung sau bằng tiếng Việt:\n\n{article}"
            try:
                response = model.generate_content(prompt)
                summary = response.text
            except Exception as e:
                summary = f"❌ Lỗi khi gọi Gemini API: {str(e)}"
    return render_template('index.html', summary=summary)

if __name__ == '__main__':
#    app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
