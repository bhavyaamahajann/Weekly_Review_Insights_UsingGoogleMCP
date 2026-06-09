import os
import sys
import json
import base64
import argparse
from email.message import EmailMessage
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Attempt to import Google API clients
try:
    from google.oauth2 import service_account
    from google.auth import default
    from googleapiclient.discovery import build
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False

# Global services references
docs_service = None
gmail_service = None

def get_google_services():
    """
    Attempts to authenticate with Google APIs and return (docs_service, gmail_service).
    Returns (None, None) if authentication fails, libraries are not available,
    or if forced to simulation mode via USE_MOCK_GOOGLE.
    """
    global docs_service, gmail_service
    
    # Write token from environment variable if present (e.g. for cloud deployments like Railway)
    token_env = os.getenv("GOOGLE_TOKEN_JSON_CONTENT")
    if token_env:
        try:
            os.makedirs("mcp_server", exist_ok=True)
            with open("mcp_server/token.json", "w") as f:
                f.write(token_env)
            print("Loaded Google token.json from environment variable GOOGLE_TOKEN_JSON_CONTENT.")
        except Exception as e:
            print(f"Failed to write token from environment variable: {e}")

    # 0. Check for forced simulation mode
    if os.getenv("USE_MOCK_GOOGLE") == "true":
        print("Forced to simulation mode via USE_MOCK_GOOGLE env var.")
        return None, None
        
    if not GOOGLE_LIBS_AVAILABLE:
        print("Google API client libraries are not installed or available.")
        return None, None

    creds = None
    # 1. Check env var for Service Account path
    sa_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if sa_path and os.path.exists(sa_path):
        try:
            creds = service_account.Credentials.from_service_account_file(
                sa_path,
                scopes=[
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/gmail.modify'
                ]
            )
            print(f"Authenticated using service account file from env: {sa_path}")
        except Exception as e:
            print(f"Failed to authenticate using env sa_path: {e}")

    # 2. Check local Service Account files in workspace
    if not creds:
        paths = ["google_credentials.json", "mcp_server/google_credentials.json", "credentials.json"]
        for path in paths:
            if os.path.exists(path):
                try:
                    creds = service_account.Credentials.from_service_account_file(
                        path,
                        scopes=[
                            'https://www.googleapis.com/auth/documents',
                            'https://www.googleapis.com/auth/gmail.modify'
                        ]
                    )
                    print(f"Authenticated using service account file: {path}")
                    break
                except Exception as e:
                    print(f"Failed to load service account from {path}: {e}")

    # 3. Check for OAuth 2.0 InstalledAppFlow (Client Secret JSON)
    if not creds:
        client_secret_path = None
        for folder in ["mcp_server", "."]:
            if os.path.exists(folder):
                # Try explicit filenames first
                for name in ["credentails.json", "credentials.json"]:
                    p = os.path.join(folder, name)
                    if os.path.exists(p):
                        client_secret_path = p
                        break
                if client_secret_path:
                    break
                # Try matching by prefix
                for filename in os.listdir(folder):
                    if filename.startswith("client_secret") and filename.endswith(".json"):
                        client_secret_path = os.path.join(folder, filename)
                        break
                if client_secret_path:
                    break
                    
        if client_secret_path:
            token_path = "mcp_server/token.json"
            # Try to load existing token
            if os.path.exists(token_path):
                try:
                    from google.oauth2.credentials import Credentials
                    creds = Credentials.from_authorized_user_file(token_path, [
                        'https://www.googleapis.com/auth/documents',
                        'https://www.googleapis.com/auth/gmail.modify'
                    ])
                    print(f"Loaded OAuth credentials from {token_path}")
                except Exception as e:
                    print(f"Failed to load OAuth credentials from {token_path}: {e}")
                    
            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                try:
                    from google.auth.transport.requests import Request
                    print("Refreshing expired OAuth token...")
                    creds.refresh(Request())
                    with open(token_path, "w") as token_file:
                        token_file.write(creds.to_json())
                    print("OAuth token refreshed and saved.")
                except Exception as e:
                    print(f"Failed to refresh OAuth token: {e}")
                    creds = None
                    
            # If still not authenticated, run local server flow (only if TTY or explicitly requested)
            if not creds:
                is_tty = False
                try:
                    is_tty = os.isatty(sys.stdin.fileno())
                except Exception:
                    pass
                    
                if is_tty or os.getenv("RUN_OAUTH_FLOW") == "true":
                    try:
                        from google_auth_oauthlib.flow import InstalledAppFlow
                        print(f"Starting InstalledAppFlow using {client_secret_path}...")
                        flow = InstalledAppFlow.from_client_secrets_file(
                            client_secret_path,
                            scopes=[
                                'https://www.googleapis.com/auth/documents',
                                'https://www.googleapis.com/auth/gmail.modify'
                            ]
                        )
                        creds = flow.run_local_server(port=0, open_browser=False)
                        with open(token_path, "w") as token_file:
                            token_file.write(creds.to_json())
                        print(f"OAuth authentication successful. Saved to {token_path}")
                    except Exception as e:
                        print(f"Failed to perform OAuth InstalledAppFlow: {e}")
                        creds = None
                else:
                    print("OAuth credentials need authorization, but standard input is not a TTY. Skipping blocking OAuth flow.")

    # 4. Check application default credentials
    if not creds:
        try:
            creds, project = default(scopes=[
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/gmail.modify'
            ])
            print("Authenticated using Application Default Credentials")
        except Exception as e:
            print(f"ADC authentication failed: {e}")

    if not creds:
        return None, None

    try:
        docs = build('docs', 'v1', credentials=creds)
        gmail = build('gmail', 'v1', credentials=creds)
        return docs, gmail
    except Exception as e:
        print(f"Failed to build google services: {e}")
        return None, None

# Initialize services
docs_service, gmail_service = get_google_services()
is_simulation = (docs_service is None or gmail_service is None)

if is_simulation:
    print("----------------------------------------------------------------")
    print("WARNING: Google API credentials not found or initialization failed.")
    print("MCP server is running in SIMULATION MODE.")
    print("Google Doc writes will save to data/outputs/gdoc_simulation.md")
    print("Gmail drafts will save to data/outputs/gmail_simulation.txt")
    print("----------------------------------------------------------------")
else:
    print("----------------------------------------------------------------")
    print("SUCCESS: Google API credentials authenticated successfully.")
    print("MCP server is running in PRODUCTION MODE.")
    print("----------------------------------------------------------------")

# Instantiate FastMCP server
mcp = FastMCP("Groww Workspace Integration Server")

# Helper functions for Google Docs API
def read_doc_text_and_ranges(doc_content):
    """
    Extracts text runs and their actual document start/end indices.
    """
    text = ""
    ranges_map = []
    
    def read_structural_elements(elements):
        nonlocal text
        for element in elements:
            if 'paragraph' in element:
                for run in element['paragraph']['elements']:
                    if 'textRun' in run:
                        run_text = run['textRun']['content']
                        doc_start = run['startIndex']
                        doc_end = run['endIndex']
                        
                        text_start = len(text)
                        text += run_text
                        text_end = len(text)
                        
                        ranges_map.append({
                            'start': text_start,
                            'end': text_end,
                            'doc_start': doc_start,
                            'doc_end': doc_end
                        })
            elif 'table' in element:
                for row in element['table']['tableRows']:
                    for cell in row['tableCells']:
                        read_structural_elements(cell['content'])
            elif 'tableOfContents' in element:
                read_structural_elements(element['tableOfContents']['content'])
                
    read_structural_elements(doc_content.get('body', {}).get('content', []))
    return text, ranges_map

def map_text_offset_to_doc_offset(offset, ranges_map):
    for r in ranges_map:
        if r['start'] <= offset <= r['end']:
            diff = offset - r['start']
            return r['doc_start'] + diff
    return None

# Formatter helper
def format_pulse_and_fee_content(payload: dict) -> str:
    """Formats the JSON payload into structured plain text for Google Docs."""
    date_str = payload.get("date", "")
    iso_week = payload.get("iso_week", "")
    
    # Pulse
    pulse_data = payload.get("weekly_pulse", {})
    summary = pulse_data.get("weekly_summary", "")
    sentiment = pulse_data.get("sentiment", {})
    pos = sentiment.get("positive", 0)
    neg = sentiment.get("negative", 0)
    neu = sentiment.get("neutral", 0)
    action_ideas = pulse_data.get("action_ideas", [])
    
    # Fee Explainer
    fee_scenario = payload.get("fee_scenario", "Mutual Fund Exit Load")
    explanation_bullets = payload.get("explanation_bullets", [])
    source_links = payload.get("source_links", [])
    last_checked = payload.get("last_checked", "")

    # Format
    content = f"[Start Week: {iso_week}]\n"
    content += "=================================================================\n"
    content += f"Groww Weekly Review Pulse — {iso_week}\n"
    content += "=================================================================\n"
    content += f"Date: {date_str}\n\n"
    content += "WEEKLY PULSE SUMMARY:\n"
    content += f"{summary}\n\n"
    content += "CUSTOMER SENTIMENT:\n"
    content += f"- Positive: {pos}%\n- Negative: {neg}%\n- Neutral: {neu}%\n\n"
    content += "ACTION IDEAS:\n"
    for idx, idea in enumerate(action_ideas, start=1):
        content += f"  {idx}. {idea}\n"
    content += "\n"
    content += f"FEE EXPLAINER SCENARIO: {fee_scenario}\n"
    content += "-----------------------------------------------------------------\n"
    for bullet in explanation_bullets:
        content += f"- {bullet}\n"
    content += "\n"
    content += "SOURCES:\n"
    for src in source_links:
        content += f"- {src}\n"
    content += f"Last Checked: {last_checked}\n"
    content += "=================================================================\n"
    content += f"[End Week: {iso_week}]\n"
    return content

# MCP Tools
@mcp.tool()
def append_to_google_doc(document_id: str, content_json: str, iso_week: str = None) -> str:
    """
    Append or update a weekly review pulse entry in a Google Doc.
    
    Args:
        document_id: The ID of the Google Doc to write to.
        content_json: A JSON string containing the pulse and fee explainer payload.
        iso_week: The ISO week (e.g. 2026-W23) to update if it already exists (idempotency).
    """
    payload = json.loads(content_json)
    if not iso_week:
        iso_week = payload.get("iso_week", "unknown-week")
        
    formatted_content = format_pulse_and_fee_content(payload)
    
    # Check if simulation
    if is_simulation:
        os.makedirs("data/outputs", exist_ok=True)
        simulation_file = "data/outputs/gdoc_simulation.md"
        
        # Implement mock update logic for simulation file
        start_marker = f"[Start Week: {iso_week}]"
        end_marker = f"[End Week: {iso_week}]"
        
        file_content = ""
        if os.path.exists(simulation_file):
            with open(simulation_file, "r") as f:
                file_content = f.read()
                
        if start_marker in file_content and end_marker in file_content:
            # Replace existing section
            start_pos = file_content.find(start_marker)
            end_pos = file_content.find(end_marker) + len(end_marker)
            new_file_content = file_content[:start_pos] + formatted_content + file_content[end_pos:]
            print(f"[Simulated Doc] Updated existing section for {iso_week}")
        else:
            # Append new section
            new_file_content = file_content
            if file_content and not file_content.endswith("\n"):
                new_file_content += "\n"
            new_file_content += "\n" + formatted_content
            print(f"[Simulated Doc] Appended new section for {iso_week}")
            
        with open(simulation_file, "w") as f:
            f.write(new_file_content)
            
        return f"mock_sec_{iso_week}"
        
    try:
        # Real Google Doc Update/Append
        doc = docs_service.documents().get(documentId=document_id).execute()
        
        start_marker = f"[Start Week: {iso_week}]"
        end_marker = f"[End Week: {iso_week}]"
        
        full_text, ranges_map = read_doc_text_and_ranges(doc)
        
        start_idx = full_text.find(start_marker)
        end_idx = full_text.find(end_marker)
        
        requests = []
        
        if start_idx != -1 and end_idx != -1:
            doc_start = map_text_offset_to_doc_offset(start_idx, ranges_map)
            doc_end = map_text_offset_to_doc_offset(end_idx + len(end_marker), ranges_map)
            
            if doc_start is not None and doc_end is not None:
                # Delete old content
                requests.append({
                    'deleteContentRange': {
                        'range': {
                            'startIndex': doc_start,
                            'endIndex': doc_end
                        }
                    }
                })
                # Insert new content
                requests.append({
                    'insertText': {
                        'location': {
                            'index': doc_start
                        },
                        'text': formatted_content
                    }
                })
                print(f"[Google Doc] Updating existing section for {iso_week} at doc index {doc_start}")
                
        if not requests:
            # Append at the end of the document
            body_content = doc.get('body', {}).get('content', [])
            insert_pos = 1
            if body_content:
                insert_pos = body_content[-1]['endIndex'] - 1
                
            requests.append({
                'insertText': {
                    'location': {
                        'index': insert_pos
                    },
                    'text': "\n" + formatted_content
                }
            })
            print(f"[Google Doc] Appending new section for {iso_week} at doc index {insert_pos}")
            
        docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        return f"sec_{iso_week}"
        
    except Exception as e:
        print(f"Error executing real google doc append/update: {e}")
        # Fall back to simulation on API error
        return f"failed_real_gdoc_sec_{iso_week}"


@mcp.tool()
def create_gmail_draft(recipient: str, subject: str, body: str, iso_week: str = "unknown") -> str:
    """
    Create a draft email in Gmail.
    
    Args:
        recipient: The email address of the recipient.
        subject: The subject of the email.
        body: The plain text body of the email.
        iso_week: The ISO week (e.g. 2026-W23) to update if mock simulation is used.
    """
    if is_simulation:
        os.makedirs("data/outputs", exist_ok=True)
        simulation_file = "data/outputs/gmail_simulation.txt"
        
        start_marker = f"[Start Draft: {iso_week}]"
        end_marker = f"[End Draft: {iso_week}]"
        
        formatted_draft = f"{start_marker}\n"
        formatted_draft += f"To: {recipient}\n"
        formatted_draft += f"Subject: {subject}\n"
        formatted_draft += "Body:\n"
        formatted_draft += f"{body}\n"
        formatted_draft += f"{end_marker}\n"
        
        file_content = ""
        if os.path.exists(simulation_file):
            with open(simulation_file, "r") as f:
                file_content = f.read()
                
        if start_marker in file_content and end_marker in file_content:
            start_pos = file_content.find(start_marker)
            end_pos = file_content.find(end_marker) + len(end_marker)
            new_file_content = file_content[:start_pos] + formatted_draft + file_content[end_pos:]
            print(f"[Simulated Gmail] Updated existing draft for {iso_week}")
        else:
            new_file_content = file_content
            if file_content and not file_content.endswith("\n"):
                new_file_content += "\n"
            new_file_content += "\n" + formatted_draft
            print(f"[Simulated Gmail] Created new draft for {iso_week}")
            
        with open(simulation_file, "w") as f:
            f.write(new_file_content)
            
        return f"mock_draft_{iso_week}"
        
    try:
        # Real Gmail API Draft Creation
        message = EmailMessage()
        message.set_content(body)
        message['To'] = recipient
        message['Subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        draft_body = {
            'message': {
                'raw': raw_message
            }
        }
        
        draft = gmail_service.users().drafts().create(userId='me', body=draft_body).execute()
        print(f"[Gmail API] Created draft with ID: {draft['id']}")
        return draft['id']
    except Exception as e:
        print(f"Error executing real gmail draft creation: {e}")
        return f"failed_real_gmail_draft_{iso_week}"

if __name__ == "__main__":
    default_port = int(os.getenv("PORT", 3001))
    default_host = os.getenv("HOST", "127.0.0.1" if os.getenv("PORT") is None else "0.0.0.0")

    parser = argparse.ArgumentParser(description="Groww Workspace MCP Server")
    parser.add_argument("--port", type=int, default=default_port, help="Port to run the SSE server on")
    parser.add_argument("--host", type=str, default=default_host, help="Host to run the SSE server on")
    parser.add_argument("--transport", type=str, choices=["stdio", "sse"], default="sse", help="Transport to use")
    args = parser.parse_args()
    
    mcp.settings.port = args.port
    mcp.settings.host = args.host
    
    # Add custom root route to return status 200 on / for health checks/pings
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    
    async def root_endpoint(request):
        return JSONResponse({
            "status": "ok", 
            "mode": "simulation" if is_simulation else "production",
            "server": "Groww Workspace MCP Server",
            "port": args.port
        })
        
    mcp._custom_starlette_routes.append(Route("/", endpoint=root_endpoint))
    
    print(f"Starting MCP server on {args.host}:{args.port} using {args.transport} transport...")
    mcp.run(transport=args.transport)
