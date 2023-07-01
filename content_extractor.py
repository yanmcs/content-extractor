"""
We will build a content extractor that will return a json with all the text, headings and paragraphs from a given url
result = {
    "html": "<html>Full website HTML</html>",
    "article_text": "Full body text with all headings and text",
    "article_headings": ["1", "2"],  # Array with all headings found in the text
    "article_paragraphs": [],  # Array with all paragraphs from the text
    "urls": [],  # Array with all urls in the text
    "article_content": [{"heading": "", "paragraphs": ""}, {"heading": "", "paragraphs": ""}]  # Array with all headings and paragraphs below
}
"""
# import modules
from selenium import webdriver
import os
from bs4 import BeautifulSoup as Bs
import cfscrape
import time
from string import punctuation
import markdownify

class ChromeSession:
    """
    Class to manage a Chrome session
    """        

    def __init__(self, headless=True):
        self.options = webdriver.ChromeOptions() 
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument("start-maximized")
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-browser-side-navigation')
        self.options.add_argument('--disable-infobars')
        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=self.options)

    def __enter__(self):
        return self.driver

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()
        

def cfscrape_session():
    """
    Returns a request session with cloudflare bypassing
    """
    session = cfscrape.create_scraper()
    return session


def extract_html_from_url(url, session):
    """
    Extracts html from given url using either a Chrome session or a request session
    """
    # Check if url is valid
    if not url.startswith("http"):
        url = "http://" + url

    # Check if session is chrome or request
    if isinstance(session, webdriver.chrome.webdriver.WebDriver): 
        with session as chrome_session:
            chrome_session.get(url)
            # Waiting page load
            i = 0
            while i < 5:
                time.sleep(1)
                if chrome_session.execute_script("return document.readyState") == "complete":
                    # scroll page a little to simulate a human user
                    chrome_session.execute_script("window.scrollBy(0, 100)")
                    time.sleep(1)
                    html = chrome_session.page_source
                    i = 5
                i += 1
    else:
        response = session.get(url)
        if response.status_code == 200:
            html = response.text
        else:
            html = None
    return html


def html_to_json(html):
    """
    Parse HTML to create JSON with all the article information
    """
    # start json
    result = {
        "html": html,
        "article_text": "",
        "article_headings": [],
        "article_paragraphs": [],
        "urls": [],
        "article_content": [],
        "article_html_content": "",
        "article_url": ""
        }

    # Parse HTML
    soup = Bs(html, "html.parser")

    # Get canonical url
    canonical_url = soup.find("link", {"rel": "canonical"})
    if canonical_url:
        result["article_url"] = canonical_url["href"]
    
    
    # Find div with most paragraphs
    # Usually the div with the most paragraphs is the one with the article content
    div_with_most_paragraphs = ''
    # Check if there is an article tag
    # If there is, we will use that div
    article_tag = soup.find("article")
    if article_tag:
        div_with_most_paragraphs = article_tag
    else:
        divs = soup.find_all(['div', 'article', 'section', 'main'])
        for div in divs:
            if div.select('p'):
                number_of_paragraphs = len(div.select('p'))
                if number_of_paragraphs > len(div_with_most_paragraphs):
                    div_with_most_paragraphs = div

    # If div_with_most_paragraphs has less than 3 paragraphs, we will use body
    if len(div_with_most_paragraphs.find_all('p')) < 3:
        div_with_most_paragraphs = soup.find('body')
    
    # Setting urls
    # Find all urls inside the div with most paragraphs
    for a in div_with_most_paragraphs.find_all('a'):
        if a.has_attr('href'):
            result["urls"].append(a['href'])

    # Setting article_html_content
    h1 = soup.find_all('h1')[-1]
    result['article_html_content'] = "<h1>" + h1.text + "</h1>\n"
    # iterate through all tags inside div if nested
    for tag in div_with_most_paragraphs.find_all(True):
        if tag.name == 'h2':
            result["article_html_content"] += "<h2>" + tag.text + "</h2>\n"
        elif tag.name == 'h3':
            result["article_html_content"] += "<h3>" + tag.text + "</h3>\n"
        elif tag.name == 'h4':
            result["article_html_content"] += "<h4>" + tag.text + "</h4>\n"
        elif tag.name == 'p':
            # We check if paragraph has at least one space (" ")
            # At least any punctuation anywhere in the paragraph text
            # To avoid empty paragraphs that make no sense
            if tag.text and " " in tag.text.strip() and any(p in tag.text for p in punctuation):
                result["article_html_content"] += "<p>" + tag.text.strip() + "</p>\n"
        elif tag.name == 'ol' or tag.name == 'ul':
            # We check if there is more than 1 li in the ol/ul
            # If there is, we will iterate through all li
            list = ""
            list += '<' + tag.name + '>\n'
            for li in tag.find_all('li'):
                if li.text and " " in li.text.strip():
                    list += "<li>" + li.text.strip() + "</li>\n"
            list += '</' + tag.name + '>\n'
            if len(list.split("</li>")) > 2:
                result["article_html_content"] += list

    # Now we soup the article_html_content
    soup = Bs(result['article_html_content'], "html.parser")

    # Find all headings inside the div with most paragraphs
    # We will go up to H4
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
    for heading in headings:
        result["article_headings"].append(heading.text)

    # Setting article_paragraphs
    # Find all paragraphs inside the div with most paragraphs
    paragraphs = soup.find_all('p')
    for paragraph in paragraphs:
        # Remove extra space and line breaks
        paragraph_text = paragraph.text.strip()
        paragraph_text = paragraph_text.replace("\n", " ")
        paragraph_text = paragraph_text.replace("\r", " ")
        # Remove double spaces
        while "  " in paragraph_text:
            paragraph_text = paragraph_text.replace("  ", "")
        result["article_paragraphs"].append(paragraph_text)
    
    # Setting article_content
    # Find all headings and paragraphs below the div with most paragraphs
    # We will go up to H4
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
    for heading in headings:
        # Check if heading has text
        if heading.text:
            # Create a dictionary with heading and paragraphs
            # Check if heading is h1, h2... to add #, ##...
            if heading.name == 'h1':
                heading_dict = {"heading": '# ' + heading.text, "paragraphs": []}
            elif heading.name == 'h2':
                heading_dict = {"heading": '## ' + heading.text, "paragraphs": []}
            elif heading.name == 'h3':
                heading_dict = {"heading": '### ' + heading.text, "paragraphs": []}
            elif heading.name == 'h4':
                heading_dict = {"heading": '#### ' + heading.text, "paragraphs": []}
            # Find all paragraphs below the heading before the next heading
            paragraphs = heading.find_next_siblings()
            for paragraph in paragraphs:
                # Stop if finds next header
                if paragraph.name and paragraph.name.startswith('h'):
                    break
                # check if is ol
                if paragraph.name == 'ol' or paragraph.name == 'ul':
                    # Find all li inside the ol
                    for li in paragraph.find_all('li'):
                        # Check if li has text
                        if li.text:
                            # Check if li has ponctuation
                            if li.text.strip()[-1] in ['.', '?', '!',';']:
                                # Add text to heading
                                heading_dict["paragraphs"].append("- " + li.text)
                            else:
                                # Add text to heading
                                heading_dict["paragraphs"].append("- " + li.text + ".")
                else:
                    # Remove extra space and line breaks
                    paragraph_text = paragraph.text.strip()
                    paragraph_text = paragraph_text.replace("\n", " ")
                    paragraph_text = paragraph_text.replace("\r", " ")
                    # Remove double spaces
                    while "  " in paragraph_text:
                        paragraph_text = paragraph_text.replace("  ", "")
                    # Add text to heading if it has enough text
                    if len(str(paragraph_text)) > 5:
                        heading_dict["paragraphs"].append(paragraph_text)
            # Add heading and paragraphs to the result
            result["article_content"].append(heading_dict)

    # Setting article_text
    # Find all headings and paragraphs to create article text
    # We will go up to H4
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
    for heading in headings:
        # Check if heading has text
        if heading.text:
            # Add heading to article text
            result["article_text"] += heading.text + "\n\n"
        # Find all paragraphs below the heading
        paragraphs = heading.find_next_siblings()
        for paragraph in paragraphs:
            # Stop if finds next header
            if paragraph.name and paragraph.name.startswith('h'):
                break
            # check if is ol
            if paragraph.name == 'ol' or paragraph.name == 'ul':
                # Find all li inside the ol
                for li in paragraph.find_all('li'):
                    # Add text to article text
                    result["article_text"] += li.text + "\n"
            else:
                # Remove extra space and line breaks
                paragraph_text = paragraph.text.strip()
                paragraph_text = paragraph_text.replace("\n", " ")
                paragraph_text = paragraph_text.replace("\r", " ")
                # Remove double spaces
                while "  " in paragraph_text:
                    paragraph_text = paragraph_text.replace("  ", "")
                # Add paragraph to article text
                result["article_text"] += paragraph_text + "\n\n"

    # Remove extra line breaks
    while '\n\n\n' in result["article_text"]:
        result["article_text"] = result["article_text"].replace('\n\n\n', '\n\n')

    # Convert html to markdown
    result["article_markdown_content"] = markdownify.markdownify(result["article_html_content"], heading_style="ATX")

    return result


