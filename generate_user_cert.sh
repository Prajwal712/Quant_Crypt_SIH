#!/bin/bash

# generate_user_cert.sh
# Usage: ./generate_user_cert.sh <username>

USERNAME=$1

if [ -z "$USERNAME" ]; then
    echo "Usage: $0 <username>"
    exit 1
fi

TARGET_DIR="src/Qukaydee_setup/$USERNAME"
ROOT_KEY="client-root-ca.key"
ROOT_CERT="client-root-ca.crt"

# Check if target directory already exists
if [ -d "$TARGET_DIR" ]; then
    echo "Directory $TARGET_DIR already exists. Skipping generation."
    exit 0
fi

# Ensure Root CA files exist
if [ ! -f "$ROOT_KEY" ]; then
    echo "Error: Root CA key ($ROOT_KEY) not found!"
    exit 1
fi

if [ ! -f "$ROOT_CERT" ]; then
    echo "Error: Root CA cert ($ROOT_CERT) not found!"
    exit 1
fi

echo "Generating certificate for user: $USERNAME"

# Create target directory
mkdir -p "$TARGET_DIR"

# Generate 2048-bit RSA private key
openssl genrsa -out "$TARGET_DIR/$USERNAME.key" 2048

# Generate CSR (Certificate Signing Request)
# Using -subj to avoid interactive prompt
openssl req -new -key "$TARGET_DIR/$USERNAME.key" \
    -out "$TARGET_DIR/$USERNAME.csr" \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=$USERNAME"

# Sign the CSR with Root CA to create the certificate
openssl x509 -req -in "$TARGET_DIR/$USERNAME.csr" \
    -CA "$ROOT_CERT" -CAkey "$ROOT_KEY" -CAcreateserial \
    -out "$TARGET_DIR/$USERNAME.crt" -days 365 -sha256

# Remove CSR as it's no longer needed
rm "$TARGET_DIR/$USERNAME.csr"

echo "Successfully created:"
echo "  - $TARGET_DIR/$USERNAME.key"
echo "  - $TARGET_DIR/$USERNAME.crt"
