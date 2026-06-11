#!/bin/bash

# 1. Create the directories your code expects
mkdir -p src/Qukaydee_setup/alice_sender/
mkdir -p src/Qukaydee_setup/bob_receiver/
mkdir -p src/Qukaydee_setup/certs/

# 2. Copy the secrets from Render's secure folder to your project folders
cp /etc/secrets/sae-1.crt src/Qukaydee_setup/alice_sender/
cp /etc/secrets/sae-1.key src/Qukaydee_setup/alice_sender/
cp /etc/secrets/sae-2.crt src/Qukaydee_setup/bob_receiver/
cp /etc/secrets/sae-2.key src/Qukaydee_setup/bob_receiver/
cp /etc/secrets/account-3000-server-ca-qukaydee-com.crt src/Qukaydee_setup/certs/
cp /etc/secrets/token.json ./token.json

# 3. Start your application
python3 bridge.py