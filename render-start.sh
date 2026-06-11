#!/bin/bash

# Render Start Script
# With per-user OAuth, we no longer need a pre-baked token.json.
# Users authenticate via the Google OAuth flow in their browser.

# 1. Set Flask secret key (Render should set FLASK_SECRET_KEY as env var)
if [ -z "$FLASK_SECRET_KEY" ]; then
    echo "⚠️  FLASK_SECRET_KEY not set. Using default (UNSAFE for production)."
fi

# 2. Start the application with Gunicorn
#    IMPORTANT: Must use -w 1 (single worker) because user_sessions
#    is an in-memory dict. Multiple workers = separate memory = sessions
#    created in one worker are invisible to the others.
#    For multi-worker support, migrate to Redis session storage.
exec gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT bridge:app
