import os
import sys

# Ensure module pathing works if running from src root
sys.path.append(os.getcwd())

from src.email_engine.auth import get_gmail_service
from src.email_engine.receiver import get_latest_email
from src.email_engine.quantum_email import QuantumEmailEngine
from src.key_management.key_manager import KeyManager
from src.cryptography.security_levels import EncryptionEngine, SecurityLevel
from src.qkd.qukaydee_provider import QuKayDeeProvider

def main():
    """
    Command-line Quantum Email Client (QuKayDee-backed)
    """

    # =========================
    # 1. Gmail Authentication
    # =========================
    print("Authenticating with Gmail...")
    service = get_gmail_service()
    if not service:
        print("❌ Could not connect to Gmail. Exiting.")
        return
    print("✅ Gmail authentication successful!")

    # =========================
    # 2. Configure QKD Providers (Alice & Bob)
    # =========================
    print("\nInitializing QuKayDee QKD providers...")

    # --- PATH CONFIGURATION ---
    # Automatically find the certs based on where the script is running
    # Assumes structure: src/qkd/Qukaydee_setup/{alice_sender, bob_receiver, certs}
    
    BASE_QKD_DIR = os.path.join(os.getcwd(), "src", "Qukaydee_setup")

    # Define Paths
    ALICE_DIR = os.path.join(BASE_QKD_DIR, "alice_sender")
    BOB_DIR = os.path.join(BASE_QKD_DIR, "bob_receiver")
    CERTS_DIR = os.path.join(BASE_QKD_DIR, "certs")
    
    # Path to the Shared CA File (Server trust)
    CA_FILE = os.path.join(CERTS_DIR, "account-3000-server-ca-qukaydee-com.crt")

    # Check if files exist before proceeding
    if not os.path.exists(CA_FILE):
        print(f"❌ Error: CA File not found at: {CA_FILE}")
        return

    try:
        # --- ALICE PROVIDER (Sender) ---
        # Connects to KME-1
        alice_provider = QuKayDeeProvider(
            host="https://kme-1.acct-3000.etsi-qkd-api.qukaydee.com",
            cert_path=os.path.join(ALICE_DIR, "sae-1.crt"),
            key_path=os.path.join(ALICE_DIR, "sae-1.key"),
            ca_path=CA_FILE
        )

        # --- BOB PROVIDER (Receiver) ---
        # Connects to KME-2
        bob_provider = QuKayDeeProvider(
            host="https://kme-2.acct-3000.etsi-qkd-api.qukaydee.com",
            cert_path=os.path.join(BOB_DIR, "sae-2.crt"),
            key_path=os.path.join(BOB_DIR, "sae-2.key"),
            ca_path=CA_FILE
        )
        
        print("✅ Connected to KME-1 (Alice) and KME-2 (Bob) successfully.")

    except Exception as e:
        print("❌ Failed to initialize QKD providers.")
        print(f"Details: {e}")
        return

    # =========================
    # 3. Initialize Key Managers
    # =========================
    
    # Alice: The local user sending emails
    alice_km = KeyManager(
        manager_id="sae-1",
        qkd_provider=alice_provider,
        storage_path="./key_store/alice"
    )

    # Bob: The recipient (Simulated peer)
    bob_km = KeyManager(
        manager_id="sae-2",
        qkd_provider=bob_provider,
        storage_path="./key_store/bob"
    )

    # Initialize Crypto Engine
    crypto_engine = EncryptionEngine()

    # Initialize Main Engine
    quantum_engine = QuantumEmailEngine(
        gmail_service=service,
        sender_key_manager=alice_km,
        encryption_engine=crypto_engine,
    )

    print("✅ Quantum Email Engine ready (ETSI GS QKD 014)\n")

    # =========================
    # 4. CLI Loop
    # =========================

    while True:
        print("\n--- Quantum Gmail Client ---")
        print("1. Send QUANTUM-ENCRYPTED email")
        print("2. Read latest unread email")
        print("3. Exit")

        choice = input("Enter choice (1 / 2 / 3): ").strip()

        # -------------------------------------------------
        # SEND (Quantum)
        # -------------------------------------------------
        if choice == "1":
            recipient = input("Recipient email: ").strip()
            subject = input("Subject: ").strip()

            print("Enter email body (end with empty line):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            body = "\n".join(lines)

            print("\n🔐 Sending quantum-encrypted email...")

            # We pass 'bob_km' here so the engine knows who to ask for keys
            result = quantum_engine.send_encrypted_email(
                sender="me",
                recipient=recipient,
                subject=subject,
                plaintext_content=body,
                security_level=SecurityLevel.LEVEL_2_STANDARD,
                recipient_key_manager=bob_km,
            )

            print("\nRESULT:")
            print(result)

            if result.get("status") == "success":
                print("✅ Quantum email sent successfully!")
                print(f"   Key ID: {result.get('key_id')}")
            else:
                print("❌ Quantum send failed!")

        # -------------------------------------------------
        # RECEIVE (Plain read for now)
        # -------------------------------------------------
        elif choice == "2":
            print("\n📥 Checking for new mail...")
            # Note: Real decryption would need logic to detect the sender ID
            # and pick the right KeyManager. For this demo, we assume Bob is reading.
            
            # Since 'get_latest_email' in your original code was basic, 
            # we rely on the logic inside QuantumEmailEngine if integrated fully.
            # For this CLI, we just call the basic fetcher:
            get_latest_email(service)

        # -------------------------------------------------
        # EXIT
        # -------------------------------------------------
        elif choice == "3":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    main()