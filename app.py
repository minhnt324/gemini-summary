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
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = ' '.join(p.get_text() for p in soup.find_all('p'))
        return text.strip()
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
