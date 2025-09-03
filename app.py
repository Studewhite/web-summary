from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
except Exception as e:
    logger.error(f"Failed to download NLTK data: {e}")

app = Flask(__name__)

HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
    <title>Website Summarizer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        input[type="text"] { width: 100%; max-width: 600px; padding: 10px; }
        input[type="submit"] { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        input[type="submit"]:hover { background: #0056b3; }
        .summary, .error { margin-top: 20px; padding: 15px; border-radius: 5px; }
        .summary { background: #e9f7ef; }
        .error { background: #f8d7da; }
    </style>
</head>
<body>
    <h1>Website Summarizer</h1>
    <form method="post">
        <label for="url">Enter Website URL:</label><br>
        <input type="text" id="url" name="url" size="50" placeholder="https://example.com"><br><br>
        <input type="submit" value="Summarize">
    </form>
    {% if summary %}
    <h2>Summary:</h2>
    <div class="summary">{{ summary }}</div>
    {% endif %}
    {% if error %}
    <h2>Error:</h2>
    <div class="error">{{ error }}</div>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = None
    error = None
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            error = "Please provide a URL"
        else:
            try:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                logger.info(f"Attempting to scrape URL: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                content_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'article'])
                content = ' '.join([tag.get_text(strip=True) for tag in content_tags if tag.get_text(strip=True)])
                if not content or len(content) < 100:
                    raise ValueError("Not enough textual content found on the page")
                logger.info("Content extracted successfully")
                parser = HtmlParser.from_string(content, url, Tokenizer("english"))
                summarizer = LsaSummarizer()
                summary_sentences = summarizer(parser.document, 5)
                summary = ' '.join([str(sentence) for sentence in summary_sentences])
                if not summary:
                    raise ValueError("Failed to generate a summary")
                logger.info("Summary generated successfully")
            except requests.exceptions.RequestException as e:
                error = f"Failed to fetch website: {str(e)}"
                logger.error(error)
            except Exception as e:
                error = f"Error processing website: {str(e)}"
                logger.error(error)
    return render_template_string(HTML_TEMPLATE, summary=summary, error=error)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)