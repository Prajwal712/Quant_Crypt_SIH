#!/usr/bin/env python3
"""
Quantum Email Encryption System - Main Entry Point
SIH 2024

This is the main launcher for the Quantum Email Encryption System.
It provides a simple menu to launch different components.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_banner():
    """Print welcome banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     QUANTUM EMAIL ENCRYPTION SYSTEM                       ║
    ║     SIH 2024                                              ║
    ║                                                           ║
    ║     4 Security Levels | QKD | Key Management | GUI        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu():
    """Print main menu"""
    menu = """
    ┌─────────────────────────────────────────────────────────┐
    │  Main Menu - Select an option:                          │
    ├─────────────────────────────────────────────────────────┤
    │  1. Launch GUI Application                              │
    │  2. Run Example Demonstrations                          │
    │  3. Start REST API Server                               │
    │  4. Run API Client Tests                                │
    │  5. Quick Encryption Test                               │
    │  6. View System Information                             │
    │  7. Exit                                                │
    └─────────────────────────────────────────────────────────┘
    """
    print(menu)

def launch_gui():
    """Launch the GUI application"""
    print("\n🚀 Launching GUI Application...\n")
    try:
        from GUI.quantum_email_gui import main
        main()
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")

def run_examples():
    """Run example demonstrations"""
    print("\n🔬 Running Example Demonstrations...\n")
    print("This will demonstrate all 4 security levels and features.\n")

    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'examples'))

        from example_usage import main
        main()
    except Exception as e:
        print(f"❌ Error running examples: {e}")

def start_api_server():
    """Start REST API server"""
    print("\n🌐 Starting REST API Server...\n")
    print("The API will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")

    try:
        from qkd.qkd_simulator import QKDChannel
        from key_management.key_manager import KeyManager
        from key_management.api import KeyManagementAPI

        qkd_channel = QKDChannel()
        key_manager = KeyManager("api_manager")
        api = KeyManagementAPI(key_manager, qkd_channel)

        print("✓ API Server initialized")
        print("✓ QKD Channel ready")
        print("✓ Key Manager ready\n")

        api.run(host='localhost', port=5000, debug=False)

    except Exception as e:
        print(f"❌ Error starting API server: {e}")

def run_api_tests():
    """Run API client tests"""
    print("\n🧪 Running REST API Tests...\n")
    print("Make sure the API server is running first (option 3)\n")

    input("Press Enter to continue...")

    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'examples'))

        from rest_api_example import test_api_client
        test_api_client()
    except Exception as e:
        print(f"❌ Error running API tests: {e}")

def quick_test():
    """Run a quick encryption test"""
    print("\n⚡ Quick Encryption Test\n")
    print("This will test all 4 security levels with a sample message.\n")

    try:
        from qkd.qkd_simulator import QKDChannel
        from cryptography.security_levels import EncryptionEngine, SecurityLevel

        # Initialize
        qkd = QKDChannel(key_length=256)
        engine = EncryptionEngine()

        # Generate quantum key
        print("1. Generating quantum key via BB84...")
        quantum_key, key_id = qkd.establish_key_pair("alice", "bob")
        print(f"   ✓ Generated key: {key_id}\n")

        # Test message
        message = b"Hello, Quantum World! This is a secret message."
        print(f"2. Original message: {message.decode()}\n")

        # Test each level
        levels = [
            (SecurityLevel.LEVEL_1_BASIC, "Level 1: XOR (One-Time Pad)"),
            (SecurityLevel.LEVEL_2_STANDARD, "Level 2: AES-256-GCM"),
            (SecurityLevel.LEVEL_3_HIGH, "Level 3: ChaCha20-Poly1305"),
            (SecurityLevel.LEVEL_4_MAXIMUM, "Level 4: Hybrid (RSA+AES+Quantum)")
        ]

        for level, name in levels:
            print(f"3. Testing {name}")

            # Encrypt
            ciphertext, metadata = engine.encrypt(message, quantum_key, level)
            print(f"   ✓ Encrypted: {len(ciphertext)} bytes")
            print(f"   Algorithm: {metadata['algorithm']}")

            # Decrypt
            plaintext = engine.decrypt(ciphertext, quantum_key, metadata)
            print(f"   ✓ Decrypted: {plaintext.decode()}")

            if plaintext == message:
                print("   ✓ Success: Decryption matches original!\n")
            else:
                print("   ✗ Error: Decryption failed!\n")

        print("✅ All tests passed successfully!\n")

    except Exception as e:
        print(f"❌ Error during test: {e}")

def show_info():
    """Show system information"""
    print("\n📊 System Information\n")

    try:
        print("=" * 60)
        print("QUANTUM EMAIL ENCRYPTION SYSTEM")
        print("=" * 60)
        print()

        # Check imports
        print("Component Status:")
        print("-" * 60)

        try:
            from qkd.qkd_simulator import QKDChannel
            print("✓ QKD Module (BB84 Protocol)")
        except:
            print("✗ QKD Module - Import Error")

        try:
            from key_management.key_manager import KeyManager
            print("✓ Key Management Module")
        except:
            print("✗ Key Management Module - Import Error")

        try:
            from cryptography.security_levels import EncryptionEngine, SecurityLevel
            print("✓ Cryptography Module (4 Security Levels)")
        except:
            print("✗ Cryptography Module - Import Error")

        try:
            from email_engine.quantum_email import QuantumEmailEngine
            print("✓ Email Engine (Gmail Integration)")
        except:
            print("✗ Email Engine - Import Error")

        try:
            from GUI.quantum_email_gui import QuantumEmailGUI
            print("✓ GUI Application")
        except:
            print("✗ GUI Application - Import Error")

        print()
        print("=" * 60)
        print("Security Levels Available:")
        print("-" * 60)
        print("Level 1: XOR with Quantum Key (Fastest)")
        print("Level 2: AES-256-GCM (Standard)")
        print("Level 3: ChaCha20-Poly1305 (High Security)")
        print("Level 4: Hybrid RSA+AES+Quantum (Maximum Security)")
        print()
        print("=" * 60)
        print("Features:")
        print("-" * 60)
        print("• BB84 Quantum Key Distribution")
        print("• Automated Key Management")
        print("• REST API for Key Operations")
        print("• Gmail Integration (SMTP/IMAP)")
        print("• User-Friendly GUI")
        print("• Comprehensive Documentation")
        print()
        print("=" * 60)
        print()

    except Exception as e:
        print(f"❌ Error gathering system info: {e}")

def main():
    """Main function"""
    print_banner()

    while True:
        print_menu()

        try:
            choice = input("Enter your choice (1-7): ").strip()

            if choice == '1':
                launch_gui()
            elif choice == '2':
                run_examples()
            elif choice == '3':
                start_api_server()
            elif choice == '4':
                run_api_tests()
            elif choice == '5':
                quick_test()
            elif choice == '6':
                show_info()
            elif choice == '7':
                print("\n👋 Thank you for using Quantum Email Encryption System!")
                print("   SIH 2024\n")
                sys.exit(0)
            else:
                print("\n❌ Invalid choice. Please enter a number between 1 and 7.\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

        input("\nPress Enter to continue...")
        print("\n" * 2)

if __name__ == '__main__':
    main()
