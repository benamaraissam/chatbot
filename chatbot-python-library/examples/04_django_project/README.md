# Example 04 — Django integration

Minimal Django project wiring `chatbot_urls`.

```bash
pip install chatbot[django]
cd examples/04_django_project
django-admin startproject config .  # if starting fresh
# Add to config/urls.py:
#   path("api/chat/", include(chatbot_urls(bot, user_context=get_user_context))),
```

See `urls_snippet.py` for the integration pattern.
