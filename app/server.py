"""HTTP layer: a single POST /upload endpoint over the upload core.

`create_app` takes an uploader so tests can inject a fake/simulated one and never
touch the network or need credentials. The real, env-backed wiring lives in
`app/wsgi.py` so importing this module for tests stays credential-free.
"""

from flask import Flask, jsonify, request


def create_app(uploader):
    """Build the Flask app around a given uploader.

    Change this when routes are added or the response shape changes. The uploader
    is injected (not built here) so the app is testable without B2 credentials.
    """
    app = Flask(__name__)

    @app.post("/upload")
    def upload():
        """Store the posted file in B2 and return its name, id, and URL.

        Change this when the request contract changes. Returns 400 for a missing
        file, 500 if the uploader fails, and never leaks a stack trace to the client.
        """
        uploaded = request.files.get("file")
        if uploaded is None or uploaded.filename == "":
            return jsonify(error="No file provided under field 'file'"), 400

        data = uploaded.read()
        content_type = uploaded.mimetype or "b2/x-auto"
        try:
            result = uploader.upload(uploaded.filename, data, content_type)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except Exception:
            return jsonify(error="Upload failed"), 500

        return jsonify(
            fileName=result.file_name,
            fileId=result.file_id,
            url=result.url,
        )

    return app
