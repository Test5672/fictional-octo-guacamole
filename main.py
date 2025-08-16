from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

app = Flask(__name__)

@app.route("/", methods=["GET"])
def proxy():
    target_url = request.args.get("url")
    if not target_url:
        return "Provide a URL using ?url=...", 400

    try:
        # Fetch the target page
        resp = requests.get(target_url, timeout=10)
        html = resp.text

        # Parse HTML and rewrite links and sources
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["a", "link", "script", "img"]):
            attr = "href" if tag.name in ["a", "link"] else "src"
            if tag.has_attr(attr):
                tag[attr] = "/?url=" + urljoin(target_url, tag[attr])

        return Response(str(soup), content_type="text/html")

    except Exception as e:
        return f"Error fetching URL: {e}", 500

# Use the PORT environment variable set by Render
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
