"""Production entry point: `flask --app app.wsgi run`.

Loads credentials from .env, builds the real B2-backed uploader, and exposes the
Flask `app` object Flask's CLI looks for. Kept separate from server.py so test
imports of `create_app` never require B2 credentials.
"""

from dotenv import load_dotenv

from app.b2_client import build_uploader
from app.server import create_app

# Load .env then wire the real uploader. Change this when the default credential
# source or app configuration changes.
load_dotenv()
app = create_app(build_uploader())
