from auth import get_gmail_service
from sender import create_message, send_email
from receiver import get_latest_email

def main():
    """
    Provides a command-line interface to send or receive emails.
    """
    # Authenticate and get the service object. This is done once.
    print("Authenticating with Gmail...")
    service = get_gmail_service()
    if not service:
        print("Could not connect to Gmail. Exiting.")
        return
    print("Authentication successful!")

    while True:
        print("\n--- Gmail Python Client ---")
        print("1. Send a new email")
        print("2. Read the latest unread email")
        print("3. Exit")
        choice = input("Please enter your choice (1, 2, or 3): ")

        if choice == '1':
            # Logic for sending an email
            recipient = input("Enter recipient's email: ")
            subject = input("Enter email subject: ")
            print("Enter email body (end with an empty line):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            body = "\n".join(lines)

            
            # 'me' is a special value indicating the authenticated user
            sender = 'me'
            
            # Create and send the message
            message = create_message(sender, recipient, subject, body)
            send_email(service, sender, message)

        elif choice == '2':
            # Logic for receiving the latest email
            print("\nChecking for new mail...")
            get_latest_email(service)

        elif choice == '3':
            # Exit the loop and the program
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == '__main__':
    main()
