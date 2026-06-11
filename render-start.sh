#!/bin/bash

# Render Start Script
# With per-user OAuth, we no longer need a pre-baked token.json.
# Users authenticate via the Google OAuth flow in their browser.

# 1. Set Flask secret key (Render should set FLASK_SECRET_KEY as env var)
if [ -z "$FLASK_SECRET_KEY" ]; then
    echo "⚠️  FLASK_SECRET_KEY not set. Using default (UNSAFE for production)."
fi

# 2. Start the application with Gunicorn
exec gunicorn -w 2 -b 0.0.0.0:$PORT bridge:app
