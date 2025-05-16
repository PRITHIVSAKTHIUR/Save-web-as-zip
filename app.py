import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile
from io import BytesIO
import gradio as gr

def download_file(url, session):
    """Download a file and return its content."""
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

def save_webpage_as_zip(url):
    """Save a webpage and its assets as a ZIP file."""
    session = requests.Session()
    response = session.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    temp_dir = 'temp_webpage'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    main_html_path = os.path.join(temp_dir, 'index.html')
    with open(main_html_path, 'wb') as f:
        f.write(response.content)
        
    assets = []
    for tag in soup.find_all(['img', 'link', 'script']):
        if tag.name == 'img' and tag.get('src'):
            assets.append(tag['src'])
        elif tag.name == 'link' and tag.get('href'):
            assets.append(tag['href'])
        elif tag.name == 'script' and tag.get('src'):
            assets.append(tag['src'])
            
    for asset in assets:
        asset_url = urljoin(url, asset)
        asset_path = urlparse(asset_url).path.lstrip('/')
        asset_full_path = os.path.join(temp_dir, asset_path)

        if asset_path.endswith('/'):
            print(f"Skipping directory {asset_full_path}")
            continue

        os.makedirs(os.path.dirname(asset_full_path), exist_ok=True)

        content = download_file(asset_url, session)
        if content:
            if os.path.isdir(asset_full_path):
                print(f"Skipping directory {asset_full_path}")
                continue
            with open(asset_full_path, 'wb') as f:
                f.write(content)
                
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, 'w') as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, temp_dir))

    for root, _, files in os.walk(temp_dir, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        os.rmdir(root)
    zip_buffer.seek(0)
    return zip_buffer

def generate_zip_file(url):
    """Generate ZIP file from a webpage URL."""
    zip_buffer = save_webpage_as_zip(url)
    temp_zip_path = "webpage.zip"
    with open(temp_zip_path, 'wb') as f:
        f.write(zip_buffer.read())
    return temp_zip_path

examples = [
    "https://www.bmw.com/en/index.html",
    "https://www.ferrari.com/en-EN",
    "https://streamlit.io/"
]

DESCRIPTION = """

## Webpage to ZIP Downloader 🔗 
"""

with gr.Blocks(theme="bethecloud/storj_theme") as demo:
    gr.Markdown(DESCRIPTION)
    gr.Markdown("Enter a URL to download the webpage and its assets as a ZIP file.")

    url_input = gr.Textbox(label="Website URL", placeholder="Enter a URL (e.g., https://www.example.com)")

    download_button = gr.Button("Download as ZIP")
    output_file = gr.File(label="Download")

    def set_example_url(url):
        url_input.value = url

    download_button.click(fn=generate_zip_file, inputs=url_input, outputs=output_file)

    gr.Examples(
        examples=examples,
        inputs=url_input,
        outputs=output_file,
        fn=generate_zip_file
    )
demo.launch(ssr_mode=False)
