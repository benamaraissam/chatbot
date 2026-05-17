"""Django urls.py snippet — copy into your project."""

from django.urls import include, path

from chatbot import Chatbot
from chatbot.integrations.django import chatbot_urls

bot = Chatbot(default_provider="mock", storage="memory")


def get_user_context(request):
    return {"user_id": str(request.user.id), "email": getattr(request.user, "email", None)}


urlpatterns = [
    path("api/chat/", include(chatbot_urls(bot, user_context=get_user_context))),
]
