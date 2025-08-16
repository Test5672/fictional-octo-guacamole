from flask import Flask, request, Response, redirect
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# Simple in-memory session store for cookies per client
sessions = {}

@app.route("/", methods=["GET", "POST"])
def proxy():
    target_url = request.args.get("url")
    if not target_url:
        return "Provide a URL using ?url=...", 400

    session = sessions.setdefault(request.remote_addr, requests.Session())

    try:
        # Forward GET or POST
        if request.method == "POST":
            resp = session.post(target_url, data=request.form, headers={key: value for key, value in request.headers})
        else:
            resp = session.get(target_url, headers={key: value for key, value in request.headers})

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # Rewrite links, forms, scripts, images, and CSS
            for tag in soup.find_all(["a", "link", "script", "img", "form"]):
                attr = None
                if tag.name in ["a", "link"]:
                    attr = "href"
                elif tag.name in ["img", "script"]:
                    attr = "src"
                elif tag.name == "form":
                    attr = "action"

                if attr and tag.has_attr(attr):
                    tag[attr] = "/?url=" + urljoin(target_url, tag[attr])

            # Rewrite CSS url() references inside style tags and style attributes
            for style_tag in soup.find_all("style"):
                style_tag.string = style_tag.string.replace("url(", "/?url=") if style_tag.string else None

            for tag in soup.find_all(style=True):
                tag["style"] = tag["style"].replace("url(", "/?url=")

            return Response(str(soup), content_type="text/html")
        else:
            # For non-HTML content, just return it directly
            return Response(resp.content, content_type=content_type)

    except Exception as e:
        return f"Error fetching URL: {e}", 500

# Use Render's PORT environment variable
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
