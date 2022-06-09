# MY scripts
import content_extractor
# Everything else
from flask import Flask
from flask_restful import reqparse
import os
import json


app = Flask(__name__)
browser = content_extractor.chrome_session(local=True)
cfscrape_session = content_extractor.cfscrape_session


@app.route("/")
def form():
    # Set html form
    form_html =  '''
    <form method="post" action="/article-extractor">

        <p>Enter URL for article text:</p>
        <input type="text" name="url">

        <select name="format">
            <option value="html">HTML</option>
            <option value="text">Text</option>
            <option value="json">JSON</option>
            <option value="links">Links</option>
        </select>

        <input type="submit" value="Submit">
        <input type="reset" value="Reset">
    </form>
    '''
    return form_html, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route("/article-extractor", methods=['GET', 'POST'])
def text():
    # Get url from request
    parser = reqparse.RequestParser()
    parser.add_argument("url", type=str, required=True, help="Url cannot be blank!")
    parser.add_argument("format", type=str, required=True, help="set format")
    data = parser.parse_args()
    # Check if there is a URL
    if data['url']:
        try:
            url = data['url']  # set variable for url
            # Get html from url
            # Try using cfscrape first
            html = content_extractor.extract_html_from_url(url, cfscrape_session())
            if not html:
                # If cfscrape fails, use Chrome
                html = content_extractor.extract_html_from_url(url, browser)
            # Parse html to json
            result = content_extractor.html_to_json(html)
        except Exception as e:
            return str(e), 500, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            # return article text
            if data['format'] == 'json':
                return json.dumps(result['article_content']), 200, {'Content-Type': 'application/json'}
            elif data['format'] == 'text':
                return str(result['article_text']), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            elif data['format'] == 'html':
                return str(result['article_html_content']), 200, {'Content-Type': 'text/html; charset=utf-8'}
            elif data['format'] == 'links':
                return json.dumps(result['urls']), 200, {'Content-Type': 'application/json'}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
