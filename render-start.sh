#!/bin/bash

# Render Start Script
# Since bridge.py now auto-detects Render via the RENDER env var
# and reads certs from /etc/secrets/, this script only needs to
# handle the token file and start gunicorn.

# 1. Copy token from /etc/secrets/ to working directory
#    (bridge.py reads it via TOKEN_FILE env var)
cp /etc/secrets/token.json ./token.json 2>/dev/null || echo "⚠️  No token.json in /etc/secrets/"

# 2. Start the application with Gunicorn
exec gunicorn -w 2 -b 0.0.0.0:$PORT bridge:app
