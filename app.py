# MY scripts
import content_extractor
# Everything else
from flask import Flask, request, render_template
from flask_restful import reqparse
import os
import json


app = Flask(__name__)
browser = content_extractor.chrome_session(local=False)
cfscrape_session = content_extractor.cfscrape_session

@app.route('/')
def index():
    if 'url' in request.args:
        try:
            url = request.args.get('url')  # set variable for url
            # Get html from url
            # Try using cfscrape first
            html = content_extractor.extract_html_from_url(url, cfscrape_session())
            print(html)
            if not html:
                # If cfscrape fails, use Chrome
                html = content_extractor.extract_html_from_url(url, browser)
                print(html)
            # Parse html to json
            result = content_extractor.html_to_json(html)
        except Exception as e:
            return str(e), 500, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            # return article text
            if request.args.get('format') == 'json':
                return json.dumps(result['article_content']), 200, {'Content-Type': 'application/json'}
            elif request.args.get('format') == 'text':
                return str(result['article_text']), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            elif request.args.get('format') == 'html':
                return str(result['article_html_content']), 200, {'Content-Type': 'text/html; charset=utf-8'}
            elif request.args.get('format') == 'links':
                return json.dumps(result['urls']), 200, {'Content-Type': 'application/json'}
            else:
                return json.dumps(result), 200, {'Content-Type': 'application/json'}
    else:
        # flask render form.html
        return render_template('form.html'), 200, {'Content-Type': 'text/html'}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
