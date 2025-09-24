from auth import get_gmail_service
from sender import create_message, send_email
from receiver import get_emails # <-- Import the new function

def main():
    """
    Provides a command-line interface to send or receive emails.
    """
    print("Authenticating with Gmail...")
    service = get_gmail_service()
    if not service:
        print("Could not connect to Gmail. Exiting.")
        return
    print("Authentication successful!")

    # This variable will store the token for the next page
    next_page_token = None

    while True:
        print("\n--- Gmail Python Client ---")
        print("1. Send a new email")
        print("2. Get first 10 unread emails")
        print("3. Get next 10 unread emails")
        print("4. Exit")
        choice = input("Please enter your choice: ")

        if choice == '1':
            recipient = input("Enter recipient's email: ")
            subject = input("Enter email subject: ")
            body = input("Enter email body: ")
            message = create_message('me', recipient, subject, body)
            send_email(service, 'me', message)

        elif choice == '2':
            print("\nFetching the first 10 unread emails...")
            # Reset page token to get the first page
            next_page_token = None 
            emails, next_page_token = get_emails(service, num_emails=10, page_token=next_page_token)
            
            if emails:
                for email in emails:
                    print("\n" + "="*40)
                    print(f"From: {email['sender']}")
                    print(f"Subject: {email['subject']}")
                    print("-" * 20)
                    # Print first 200 characters of the body
                    print(email['body'][:200] + "...")
                    print("="*40)
            
            if next_page_token:
                print("\nThere are more emails. Use option '3' to get the next page.")
            else:
                print("\n-- End of unread emails --")

        elif choice == '3':
            if not next_page_token:
                print("\nYou must get the first page (option 2) before getting the next one.")
                continue
            
            print("\nFetching the next 10 unread emails...")
            emails, next_page_token = get_emails(service, num_emails=10, page_token=next_page_token)
            
            if emails:
                for email in emails:
                    print("\n" + "="*40)
                    print(f"From: {email['sender']}")
                    print(f"Subject: {email['subject']}")
                    print("-" * 20)
                    print(email['body'][:200] + "...")
                    print("="*40)

            if not next_page_token:
                print("\n-- End of unread emails --")

        elif choice == '4':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()