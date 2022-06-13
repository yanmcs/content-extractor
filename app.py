# MY scripts
import content_extractor
# Everything else
from flask import Flask, request, render_template
from flask_restful import reqparse
import os
import json


app = Flask(__name__)

@app.route('/')
def index():
    browser = content_extractor.chrome_session(local=False)
    cfscrape_session = content_extractor.cfscrape_session
    if 'url' in request.args:
        try:
            url = request.args.get('url')  # set variable for url
            format = request.args.get('format')  # set variable for format
            always_use_chrome = request.args.get('chrome')  # set variable for chrome usage

            # Get html from url
            html = content_extractor.extract_html_from_url(url, cfscrape_session())

            # If cfscrape fails or chrome is set yes, we use Chrome
            # Check if html is valid or always use Chrome is set to yes
            if not html or always_use_chrome == 'yes':
                html = content_extractor.extract_html_from_url(url, browser)
                # Check if chrome has worked
                if 'invalid session id' in html or 'Console Locked' in html:
                    print("Chrome failed to open session")
                    # Restart chrome
                    # Close old chrome session
                    try:
                        browser.quit()
                        browser.close
                    except:
                        pass
                    # Start new chrome session
                    browser = content_extractor.chrome_session(local=False)
                    # Try again
                    html = content_extractor.extract_html_from_url(url, browser)
                
            # Parse html to json
            result = content_extractor.html_to_json(html)
        except Exception as e:
            return str(e), 500, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            # return article text
            if format == 'json':
                return json.dumps(result['article_content']), 200, {'Content-Type': 'application/json'}
            elif format == 'text':
                return str(result['article_text']), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            elif format == 'html':
                return str(result['article_html_content']), 200, {'Content-Type': 'text/html; charset=utf-8'}
            elif format == 'links':
                return json.dumps(result['urls']), 200, {'Content-Type': 'application/json'}
            else:
                return json.dumps(result), 200, {'Content-Type': 'application/json'}
    else:
        # flask render form.html
        return render_template('form.html'), 200, {'Content-Type': 'text/html'}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
