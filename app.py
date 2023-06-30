# MY scripts
import content_extractor

# Everything else
import time
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse, StreamingResponse, PlainTextResponse
import os
import json
import traceback
from datetime import datetime


file_path = os.path.dirname(os.path.abspath(__file__))


app = FastAPI(title="Content Extractor",
              description="Extrai conteúdo de sites",
              version="1.0.0",
              docs_url="/docs")

# Mount static files
app.mount("/static", StaticFiles(directory=f"{file_path}/static"), name="static")

# Mount templates
templates = Jinja2Templates(directory=f"{file_path}/templates")

@app.get('/')
async def index(request: Request, url: str=None, format: str=None, chrome: str=None, translate: str=None):
    cfscrape_session = content_extractor.cfscrape_session
    # Get url from request
    if url != None:
        # Get url from request
        format = format  # set variable for format
        always_use_chrome = chrome  # set variable for chrome usage
        translate = translate  # set variable for translation

        # Get html from url
        html = content_extractor.extract_html_from_url(url, cfscrape_session())

        # If cfscrape fails or always use Chrome is set yes, we use Chrome
        # Check if html is valid or always use Chrome is set to yes
        if not html or always_use_chrome == 'yes':
            with content_extractor.ChromeSession() as chrome_session:
                html = content_extractor.extract_html_from_url(url, chrome_session)       

        # Parse html to json
        result = content_extractor.html_to_json(html)

        # return article text
        if format == 'json':
            return result['article_content']
        elif format == 'text':# Translate if needed
            # Translate if needed
            if translate != 'no':
                # get redirect url
                redirect_url = f'https://contentextractor-yan-dev-br.translate.goog/?url={url}&format={format}&chrome={always_use_chrome}&translate=no&_x_tr_sl=auto&_x_tr_tl={translate}'
                # redirect to google translate
                return RedirectResponse(redirect_url)
            else:
                # adding source url to the text
                source_text = f'Original article: {url} \n\n'
                return HTMLResponse(content=source_text + result['article_text'], status_code=200, media_type='text/plain; charset=utf-8')
        elif format == 'html':
            # Translate if needed
            if translate != 'no':
                # get redirect url
                redirect_url = f'https://contentextractor-yan-dev-br.translate.goog/?url={url}&format={format}&chrome={always_use_chrome}&translate=no&_x_tr_sl=auto&_x_tr_tl={translate}'
                # redirect to google translate
                return RedirectResponse(redirect_url)
            else:
                # adding source to html content
                source_html = f'<p>Source: <a href="{url}">{url}</a></p>'
                return HTMLResponse(content=source_html + str(result['article_html_content']), status_code=200, media_type='text/html; charset=utf-8')
        elif format == 'links':
            return result['urls']
        elif format == 'full_html':
            return HTMLResponse(content=str(html), status_code=200, headers={'Content-Type': 'text/html; charset=utf-8'})
        else:
            return result
    else:
        # return template form.html
        return templates.TemplateResponse("form.html", {"request": request})
        


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5008))
    app.run(host='0.0.0.0', port=port, debug=True)
