"""Example 03 — Integrate into an existing Flask application."""

from flask import Flask

from chatbot import Chatbot
from chatbot.integrations.flask import create_blueprint

app = Flask(__name__)
bot = Chatbot(default_provider="mock", storage="memory")


def get_user_context():
    return {"user_id": "flask_user_1"}


bp = create_blueprint(bot, user_context=get_user_context)
app.register_blueprint(bp, url_prefix="/api/chat")


@app.route("/")
def index():
    return {"message": "Flask app. POST /api/chat/chat for SSE."}


if __name__ == "__main__":
    # Dev only — use gunicorn -k gevent for SSE in production
    app.run(host="0.0.0.0", port=5000, debug=True)
