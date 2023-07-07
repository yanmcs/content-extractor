# MY scripts
import content_extractor

# Everything else
import time
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import os


file_path = os.path.dirname(os.path.abspath(__file__))


app = FastAPI(title="Content Extractor",
              description="Extrai conteúdo de sites",
              version="1.0.0",
              docs_url="/docs")

# Mount static files
app.mount("/static", StaticFiles(directory=f"{file_path}/static"), name="static")

# Mount templates
templates = Jinja2Templates(directory=f"{file_path}/templates")

def extract_html(url, always_use_chrome):
    cfscrape_session = content_extractor.cfscrape_session
    # Get html from url
    html = content_extractor.extract_html_from_url(url, cfscrape_session())

    # If cfscrape fails or always use Chrome is set yes, we use Chrome
    # Check if html is valid or always use Chrome is set to yes
    if not html or always_use_chrome:
        with content_extractor.ChromeSession() as chrome_session:
            html = content_extractor.extract_html_from_url(url, chrome_session)       

    return html

def translate_url(url, format, always_use_chrome, translate):
    # get redirect url
    redirect_url = f'https://contentextractor-yan-dev-br.translate.goog/?url={url}&format={format}&chrome={always_use_chrome}&translate=no&_x_tr_sl=auto&_x_tr_tl={translate}'
    # redirect to google translate
    return RedirectResponse(redirect_url)

def add_source_to_text(url, result):
    # adding source url to the text
    source_text = f'Original article: {url} \n\n'
    return HTMLResponse(content=source_text + result['article_text'], status_code=200, media_type='text/plain; charset=utf-8')

def add_source_to_html(url, result):
    # adding source to html content
    source_html = f'<p>Source: <a href="{url}">{url}</a></p>\n'
    return HTMLResponse(content=source_html + str(result['article_html_content']), status_code=200, media_type='text/html; charset=utf-8')

def add_source_to_markdown(url, result):
    # adding source to html content
    source_html = f'Source: [{url}]({url})\n\n'
    return HTMLResponse(content=source_html + str(result['article_markdown_content']), status_code=200, media_type='text/plain; charset=utf-8')

@app.get('/')
async def index(request: Request, url: str=None, format: str=None, chrome: str=None, translate: str=None):
    # Get url from request
    if url != None:
        # Get url from request
        format = format  # set variable for format
        always_use_chrome = True if chrome == 'yes' else False  # set variable for chrome usage
        translate = translate  # set variable for translation

        # Get html from url
        html = extract_html(url, always_use_chrome)

        # Parse html to json
        result = content_extractor.html_to_json(html)

        # return article text
        if format == 'json':
            return result['article_content']
        elif format == 'text':# Translate if needed
            # Translate if needed
            if translate != 'no':
                return translate_url(url, format, always_use_chrome, translate)
            else:
                return add_source_to_text(url, result)
        elif format == 'html':
            # Translate if needed
            if translate != 'no':
                return translate_url(url, format, always_use_chrome, translate)
            else:
                return add_source_to_html(url, result)
        elif format == 'markdown':
            # Translate if needed
            if translate != 'no':
                return translate_url(url, format, always_use_chrome, translate)
            else:
                return add_source_to_markdown(url, result)
        elif format == 'links':
            return result['urls']
        elif format == 'full_html':
            return HTMLResponse(content=str(html), status_code=200, headers={'Content-Type': 'text/html; charset=utf-8'})
        else:
            return result
    else:
        # return template form.html
        return templates.TemplateResponse("form.html", {"request": request})

