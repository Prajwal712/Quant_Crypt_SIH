from .auth import get_gmail_service
from .receiver import get_latest_email

from src.email_engine.quantum_email import QuantumEmailEngine
from src.key_management.key_manager import KeyManager
from src.cryptography.security_levels import EncryptionEngine, SecurityLevel
from src.qkd.qukaydee_provider import QuKayDeeProvider
from config.qukaydee_config import QUKAYDEE_CONFIG







def main():
    """
    Command-line Quantum Email Client (QuKayDee-backed)
    """

    # =========================
    # Gmail Authentication
    # =========================
    print("Authenticating with Gmail...")
    service = get_gmail_service()
    if not service:
        print("❌ Could not connect to Gmail. Exiting.")
        return
    print("✅ Gmail authentication successful!")

    # =========================
    # Quantum + QKD Setup (ONCE)
    # =========================

    print("\nInitializing QuKayDee QKD provider...")

    try:
        qkd_provider = QuKayDeeProvider(QUKAYDEE_CONFIG)
    except Exception as e:
        print("❌ Failed to initialize QuKayDee QKD provider")
        print(e)
        return

    # Alice = sender SAE
    alice_km = KeyManager(
        manager_id=QUKAYDEE_CONFIG.sae_id,  # usually "sae-1"
        qkd_provider=qkd_provider,
    )

    # Bob = receiver SAE (logical peer)
    bob_km = KeyManager(
        manager_id="sae-2",  # must match QuKayDee peer SAE
        qkd_provider=qkd_provider,
    )

    crypto_engine = EncryptionEngine()

    quantum_engine = QuantumEmailEngine(
        gmail_service=service,
        sender_key_manager=alice_km,
        encryption_engine=crypto_engine,
    )

    print("✅ Quantum Email Engine ready (ETSI GS QKD 014)\n")

    # =========================
    # CLI Loop
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
            else:
                print("❌ Quantum send failed!")

        # -------------------------------------------------
        # RECEIVE (Plain read for now)
        # -------------------------------------------------
        elif choice == "2":
            print("\n📥 Checking for new mail...")
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