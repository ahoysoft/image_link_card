from flask import Flask, redirect, request, send_from_directory
import os

app = Flask(__name__)

# Get the base URL from environment or use default
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8080')

BOT_USER_AGENTS = [
    'twitterbot',
    'facebookexternalhit',
    'linkedinbot',
    'slackbot',
    'telegrambot',
    'whatsapp',
    'discordbot',
]

def is_bot(user_agent):
    """Check if the request is from a social media crawler."""
    if not user_agent:
        return False
    ua_lower = user_agent.lower()
    return any(bot in ua_lower for bot in BOT_USER_AGENTS)

@app.route('/')
def index():
    """
    Serve Twitter/X card meta tags for crawlers.
    When a user clicks the link, they get redirected to python.org.
    """
    user_agent = request.headers.get('User-Agent', '')

    # If it's a bot, serve meta tags without redirect
    if is_bot(user_agent):
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Python">
    <meta name="twitter:description" content="The official home of the Python Programming Language">
    <meta name="twitter:image" content="{BASE_URL}/images/python-card.png">

    <meta property="og:title" content="Python">
    <meta property="og:description" content="The official home of the Python Programming Language">
    <meta property="og:image" content="{BASE_URL}/images/python-card.png">
    <meta property="og:url" content="{BASE_URL}">
    <meta property="og:type" content="website">

    <title>Python</title>
</head>
<body>
    <p>Python - The official home of the Python Programming Language</p>
</body>
</html>'''
        return html

    # For regular users, redirect to python.org
    return redirect('https://www.python.org', code=302)

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the images directory."""
    return send_from_directory('images', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
