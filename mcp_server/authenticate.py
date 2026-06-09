import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

# Request access to view/edit Google Docs and manage Gmail drafts
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.modify'
]

def main():
    client_secret_path = None
    # Look in mcp_server and project root
    for folder in ["mcp_server", "."]:
        if os.path.exists(folder):
            for name in ["credentails.json", "credentials.json"]:
                p = os.path.join(folder, name)
                if os.path.exists(p):
                    client_secret_path = p
                    break
            if client_secret_path:
                break
            for filename in os.listdir(folder):
                if filename.startswith("client_secret") and filename.endswith(".json"):
                    client_secret_path = os.path.join(folder, filename)
                    break
            if client_secret_path:
                break
                
    if not client_secret_path:
        print("Error: Could not find credentials.json, credentails.json, or client_secret*.json in mcp_server/ or project root.")
        sys.exit(1)
        
    token_path = "mcp_server/token.json"
    print(f"Using client secrets file: {client_secret_path}")
    print("Starting Google OAuth flow...")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        # run_local_server will spin up a local server and try to launch the default browser
        creds = flow.run_local_server(port=0)
        
        # Save credentials for future runs
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
            
        print("\n========================================================")
        print(f"SUCCESS: OAuth token successfully saved to {token_path}")
        print("========================================================")
        
    except Exception as e:
        print(f"\nFailed to execute OAuth authentication: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
