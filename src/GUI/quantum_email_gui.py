"""
Quantum Email GUI
User interface for sending and receiving quantum-encrypted emails
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Optional

from ..qkd.qkd_simulator import QKDChannel
from ..key_management.key_manager import KeyManager
from ..cryptography.security_levels import EncryptionEngine, SecurityLevel, generate_rsa_keypair
from ..email_engine.quantum_email import QuantumEmailEngine
from ..email_engine.auth import get_gmail_service


class QuantumEmailGUI:
    """
    Main GUI application for quantum-encrypted email
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quantum Email Encryption System")
        self.root.geometry("900x700")

        # Initialize components
        self.gmail_service = None
        self.sender_key_manager = None
        self.receiver_key_manager = None
        self.qkd_channel = None
        self.encryption_engine = None
        self.quantum_email_engine = None
        self.private_key = None
        self.public_key = None

        # Setup GUI
        self._setup_gui()

    def _setup_gui(self):
        """
        Setup the main GUI layout
        """
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.setup_tab = ttk.Frame(self.notebook)
        self.sender_tab = ttk.Frame(self.notebook)
        self.receiver_tab = ttk.Frame(self.notebook)
        self.keys_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.setup_tab, text='Setup')
        self.notebook.add(self.sender_tab, text='Send Email')
        self.notebook.add(self.receiver_tab, text='Receive Email')
        self.notebook.add(self.keys_tab, text='Key Management')

        # Setup each tab
        self._setup_setup_tab()
        self._setup_sender_tab()
        self._setup_receiver_tab()
        self._setup_keys_tab()

    def _setup_setup_tab(self):
        """
        Setup tab for system initialization
        """
        frame = ttk.LabelFrame(self.setup_tab, text="System Initialization", padding=20)
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title = ttk.Label(frame, text="Quantum Email Encryption System",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)

        # Status
        self.status_label = ttk.Label(frame, text="Status: Not Initialized",
                                     font=('Arial', 10))
        self.status_label.pack(pady=5)

        # Manager IDs
        ttk.Label(frame, text="Sender Manager ID:").pack(pady=5)
        self.sender_id_entry = ttk.Entry(frame, width=30)
        self.sender_id_entry.insert(0, "sender_manager_1")
        self.sender_id_entry.pack(pady=5)

        ttk.Label(frame, text="Receiver Manager ID:").pack(pady=5)
        self.receiver_id_entry = ttk.Entry(frame, width=30)
        self.receiver_id_entry.insert(0, "receiver_manager_1")
        self.receiver_id_entry.pack(pady=5)

        # Initialize button
        self.init_button = ttk.Button(frame, text="Initialize System",
                                     command=self._initialize_system)
        self.init_button.pack(pady=20)

        # Info text
        info_text = """
        This system implements quantum-encrypted email with 4 security levels:

        Level 1: Basic (XOR with Quantum Key) - Fastest
        Level 2: Standard (AES-256-GCM) - Balanced
        Level 3: High (ChaCha20-Poly1305) - Enhanced Security
        Level 4: Maximum (Hybrid RSA+AES+Quantum) - Maximum Security

        Click 'Initialize System' to start.
        """
        info = ttk.Label(frame, text=info_text, justify='left')
        info.pack(pady=10)

    def _setup_sender_tab(self):
        """
        Setup tab for sending encrypted emails
        """
        frame = ttk.Frame(self.sender_tab, padding=20)
        frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(frame, text="Send Quantum-Encrypted Email",
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Sender email
        ttk.Label(frame, text="From (your email):").pack(anchor='w', pady=5)
        self.sender_email = ttk.Entry(frame, width=50)
        self.sender_email.pack(fill='x', pady=5)

        # Recipient email
        ttk.Label(frame, text="To (recipient email):").pack(anchor='w', pady=5)
        self.recipient_email = ttk.Entry(frame, width=50)
        self.recipient_email.pack(fill='x', pady=5)

        # Subject
        ttk.Label(frame, text="Subject:").pack(anchor='w', pady=5)
        self.subject_entry = ttk.Entry(frame, width=50)
        self.subject_entry.pack(fill='x', pady=5)

        # Security level
        ttk.Label(frame, text="Security Level:").pack(anchor='w', pady=5)
        self.security_level_var = tk.StringVar(value="Level 2: Standard (AES-256-GCM)")
        security_levels = [
            "Level 1: Basic (XOR)",
            "Level 2: Standard (AES-256-GCM)",
            "Level 3: High (ChaCha20-Poly1305)",
            "Level 4: Maximum (Hybrid)"
        ]
        self.security_combo = ttk.Combobox(frame, textvariable=self.security_level_var,
                                          values=security_levels, state='readonly', width=47)
        self.security_combo.pack(fill='x', pady=5)

        # Email content
        ttk.Label(frame, text="Email Content:").pack(anchor='w', pady=5)
        self.email_content = scrolledtext.ScrolledText(frame, height=10)
        self.email_content.pack(fill='both', expand=True, pady=5)

        # Send button
        self.send_button = ttk.Button(frame, text="Send Encrypted Email",
                                     command=self._send_email)
        self.send_button.pack(pady=10)

        # Status
        self.send_status = ttk.Label(frame, text="", foreground='green')
        self.send_status.pack(pady=5)

    def _setup_receiver_tab(self):
        """
        Setup tab for receiving encrypted emails
        """
        frame = ttk.Frame(self.receiver_tab, padding=20)
        frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(frame, text="Receive Quantum-Encrypted Email",
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', pady=10)

        self.fetch_button = ttk.Button(control_frame, text="Fetch Latest Email",
                                      command=self._fetch_latest_email)
        self.fetch_button.pack(side='left', padx=5)

        self.decrypt_button = ttk.Button(control_frame, text="Decrypt Email",
                                        command=self._decrypt_email, state='disabled')
        self.decrypt_button.pack(side='left', padx=5)

        # Email display
        ttk.Label(frame, text="Encrypted Email:").pack(anchor='w', pady=5)
        self.encrypted_display = scrolledtext.ScrolledText(frame, height=8)
        self.encrypted_display.pack(fill='both', expand=True, pady=5)

        ttk.Label(frame, text="Decrypted Content:").pack(anchor='w', pady=5)
        self.decrypted_display = scrolledtext.ScrolledText(frame, height=8)
        self.decrypted_display.pack(fill='both', expand=True, pady=5)

        # Status
        self.receive_status = ttk.Label(frame, text="", foreground='blue')
        self.receive_status.pack(pady=5)

        # Store current message
        self.current_message_id = None

    def _setup_keys_tab(self):
        """
        Setup tab for key management
        """
        frame = ttk.Frame(self.keys_tab, padding=20)
        frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(frame, text="Quantum Key Management",
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(btn_frame, text="Generate New Key Pair",
                  command=self._generate_key_pair).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="List Active Keys",
                  command=self._list_keys).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cleanup Expired Keys",
                  command=self._cleanup_keys).pack(side='left', padx=5)

        # Key display
        ttk.Label(frame, text="Active Quantum Keys:").pack(anchor='w', pady=5)
        self.keys_display = scrolledtext.ScrolledText(frame, height=20)
        self.keys_display.pack(fill='both', expand=True, pady=5)

    def _initialize_system(self):
        """
        Initialize the quantum email system
        """
        try:
            self.status_label.config(text="Status: Initializing...")
            self.init_button.config(state='disabled')

            # Get manager IDs
            sender_id = self.sender_id_entry.get()
            receiver_id = self.receiver_id_entry.get()

            # Initialize Gmail service
            self.gmail_service = get_gmail_service()

            # Initialize key managers
            self.sender_key_manager = KeyManager(sender_id)
            self.receiver_key_manager = KeyManager(receiver_id)

            # Initialize QKD channel
            self.qkd_channel = QKDChannel(key_length=256)

            # Initialize encryption engine
            self.encryption_engine = EncryptionEngine()

            # Generate RSA key pair for Level 4 encryption
            self.private_key, self.public_key = generate_rsa_keypair()

            # Initialize quantum email engine
            self.quantum_email_engine = QuantumEmailEngine(
                self.gmail_service,
                self.sender_key_manager,
                self.qkd_channel,
                self.encryption_engine
            )

            self.status_label.config(text="Status: Initialized ✓")
            messagebox.showinfo("Success", "System initialized successfully!")

        except Exception as e:
            self.status_label.config(text="Status: Initialization Failed")
            self.init_button.config(state='normal')
            messagebox.showerror("Error", f"Initialization failed: {str(e)}")

    def _send_email(self):
        """
        Send encrypted email
        """
        if not self.quantum_email_engine:
            messagebox.showerror("Error", "Please initialize the system first!")
            return

        try:
            # Get inputs
            sender = self.sender_email.get()
            recipient = self.recipient_email.get()
            subject = self.subject_entry.get()
            content = self.email_content.get('1.0', 'end-1c')

            # Get security level
            level_text = self.security_level_var.get()
            if "Level 1" in level_text:
                security_level = SecurityLevel.LEVEL_1_BASIC
            elif "Level 2" in level_text:
                security_level = SecurityLevel.LEVEL_2_STANDARD
            elif "Level 3" in level_text:
                security_level = SecurityLevel.LEVEL_3_HIGH
            else:
                security_level = SecurityLevel.LEVEL_4_MAXIMUM

            self.send_status.config(text="Encrypting and sending...", foreground='orange')
            self.send_button.config(state='disabled')

            # Send in background thread
            def send_thread():
                result = self.quantum_email_engine.send_encrypted_email(
                    sender=sender,
                    recipient=recipient,
                    subject=subject,
                    plaintext_content=content,
                    security_level=security_level,
                    recipient_key_manager=self.receiver_key_manager,
                    recipient_public_key=self.public_key if security_level == SecurityLevel.LEVEL_4_MAXIMUM else None
                )

                # Update UI in main thread
                self.root.after(0, lambda: self._send_complete(result))

            threading.Thread(target=send_thread, daemon=True).start()

        except Exception as e:
            self.send_status.config(text=f"Error: {str(e)}", foreground='red')
            self.send_button.config(state='normal')

    def _send_complete(self, result):
        """
        Handle send completion
        """
        self.send_button.config(state='normal')

        if result['status'] == 'success':
            msg = f"Email sent successfully!\n"
            msg += f"Message ID: {result['message_id']}\n"
            msg += f"Key ID: {result['key_id']}\n"
            msg += f"Security Level: {result['security_level']}"
            self.send_status.config(text=msg, foreground='green')
        else:
            self.send_status.config(text=f"Error: {result['error']}", foreground='red')

    def _fetch_latest_email(self):
        """
        Fetch latest unread email
        """
        if not self.gmail_service:
            messagebox.showerror("Error", "Please initialize the system first!")
            return

        try:
            results = self.gmail_service.users().messages().list(
                userId='me',
                q="is:unread",
                maxResults=1
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                self.receive_status.config(text="No new unread messages found.")
                return

            self.current_message_id = messages[0]['id']

            # Get message details
            msg = self.gmail_service.users().messages().get(
                userId='me',
                id=self.current_message_id
            ).execute()

            # Display encrypted content
            payload = msg['payload']
            headers = payload['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')

            self.encrypted_display.delete('1.0', 'end')
            self.encrypted_display.insert('1.0', f"Subject: {subject}\n\nEncrypted Package Retrieved")

            self.decrypt_button.config(state='normal')
            self.receive_status.config(text="Email fetched. Click 'Decrypt Email' to decrypt.",
                                     foreground='blue')

        except Exception as e:
            self.receive_status.config(text=f"Error: {str(e)}", foreground='red')

    def _decrypt_email(self):
        """
        Decrypt the fetched email
        """
        if not self.current_message_id:
            messagebox.showerror("Error", "No email to decrypt!")
            return

        try:
            self.receive_status.config(text="Decrypting...", foreground='orange')

            result = self.quantum_email_engine.receive_encrypted_email(
                self.current_message_id,
                self.receiver_key_manager,
                self.private_key
            )

            if result['status'] == 'success':
                decrypted_text = f"From: {result['sender']}\n"
                decrypted_text += f"Subject: {result['subject']}\n"
                decrypted_text += f"Security Level: {result['security_level']}\n"
                decrypted_text += f"Key ID: {result['key_id']}\n\n"
                decrypted_text += f"Content:\n{result['content']}"

                self.decrypted_display.delete('1.0', 'end')
                self.decrypted_display.insert('1.0', decrypted_text)

                self.receive_status.config(text="Email decrypted successfully! ✓",
                                         foreground='green')
            else:
                self.receive_status.config(text=f"Decryption failed: {result['error']}",
                                         foreground='red')

        except Exception as e:
            self.receive_status.config(text=f"Error: {str(e)}", foreground='red')

    def _generate_key_pair(self):
        """
        Generate a new quantum key pair
        """
        if not self.qkd_channel:
            messagebox.showerror("Error", "Please initialize the system first!")
            return

        try:
            quantum_key, key_id = self.qkd_channel.establish_key_pair(
                self.sender_key_manager.manager_id,
                self.receiver_key_manager.manager_id
            )

            # Store in both managers
            self.sender_key_manager.store_key(quantum_key, key_id,
                                             {'purpose': 'manual_generation'})
            self.receiver_key_manager.store_key(quantum_key, key_id,
                                               {'purpose': 'manual_generation'})

            self.keys_display.insert('end', f"\n✓ Generated new key pair: {key_id}\n")
            messagebox.showinfo("Success", f"Key pair generated!\nKey ID: {key_id}")

        except Exception as e:
            messagebox.showerror("Error", f"Key generation failed: {str(e)}")

    def _list_keys(self):
        """
        List all active keys
        """
        if not self.sender_key_manager:
            messagebox.showerror("Error", "Please initialize the system first!")
            return

        self.keys_display.delete('1.0', 'end')

        sender_keys = self.sender_key_manager.list_keys()
        receiver_keys = self.receiver_key_manager.list_keys()

        self.keys_display.insert('end', "=== SENDER KEYS ===\n")
        for key in sender_keys:
            self.keys_display.insert('end', f"\nKey ID: {key['key_id']}\n")
            self.keys_display.insert('end', f"Created: {key['created_at']}\n")
            self.keys_display.insert('end', f"Expires: {key['expires_at']}\n")
            self.keys_display.insert('end', f"Usage: {key['usage_count']}\n")

        self.keys_display.insert('end', "\n\n=== RECEIVER KEYS ===\n")
        for key in receiver_keys:
            self.keys_display.insert('end', f"\nKey ID: {key['key_id']}\n")
            self.keys_display.insert('end', f"Created: {key['created_at']}\n")
            self.keys_display.insert('end', f"Expires: {key['expires_at']}\n")
            self.keys_display.insert('end', f"Usage: {key['usage_count']}\n")

    def _cleanup_keys(self):
        """
        Cleanup expired keys
        """
        if not self.sender_key_manager:
            messagebox.showerror("Error", "Please initialize the system first!")
            return

        sender_count = self.sender_key_manager.cleanup_expired_keys()
        receiver_count = self.receiver_key_manager.cleanup_expired_keys()

        total = sender_count + receiver_count
        messagebox.showinfo("Cleanup Complete", f"Removed {total} expired keys")
        self._list_keys()

    def run(self):
        """
        Start the GUI application
        """
        self.root.mainloop()


def main():
    """
    Main entry point for the GUI application
    """
    app = QuantumEmailGUI()
    app.run()


if __name__ == '__main__':
    main()
