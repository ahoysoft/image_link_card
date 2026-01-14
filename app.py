from flask import Flask, redirect, request, send_from_directory
import os

app = Flask(__name__)

# Get the base URL from environment or use default
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8080')

@app.route('/')
def index():
    """
    Serve Twitter/X card meta tags for crawlers.
    When a user clicks the link, they get redirected to python.org.
    """
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Python">
    <meta name="twitter:description" content="The official home of the Python Programming Language">
    <meta name="twitter:image" content="{BASE_URL}/images/python-logo.png">

    <meta property="og:title" content="Python">
    <meta property="og:description" content="The official home of the Python Programming Language">
    <meta property="og:image" content="{BASE_URL}/images/python-logo.png">
    <meta property="og:url" content="https://www.python.org">
    <meta property="og:type" content="website">

    <meta http-equiv="refresh" content="0;url=https://www.python.org">
    <title>Redirecting to Python.org...</title>
</head>
<body>
    <p>Redirecting to <a href="https://www.python.org">python.org</a>...</p>
    <script>
        window.location.href = "https://www.python.org";
    </script>
</body>
</html>'''
    return html

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the images directory."""
    return send_from_directory('images', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
