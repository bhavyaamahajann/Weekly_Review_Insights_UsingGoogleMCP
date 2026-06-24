import os
import asyncio
from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.sse import sse_client

load_dotenv()

async def async_create_gmail_draft(pulse_summary: str, fee_summary: str, doc_link: str, iso_week: str = "unknown") -> str:
    """Async client connection to Gmail MCP server."""
    server_url = os.getenv("MCP_GMAIL_SERVER_URL", "http://localhost:3002")
    if not server_url.endswith("/sse"):
        server_url = server_url.rstrip("/") + "/sse"
        
    recipient = os.getenv("GMAIL_RECIPIENT", "team@groww.in")
    subject = f"Weekly Pulse + Fee Explainer — Groww ({iso_week})"
    
    # Construct the body
    body = f"Hi Team,\n\n"
    body += f"Here is the Weekly Product Review Pulse and Fee Explainer for Groww ({iso_week}).\n\n"
    body += "WEEKLY PULSE SUMMARY:\n"
    body += f"{pulse_summary}\n\n"
    body += "FEE EXPLAINER: Mutual Fund Exit Load\n"
    body += f"{fee_summary}\n\n"
    body += f"The full report and historical logs have been appended to the Google Doc:\n{doc_link}\n\n"
    body += "Best regards,\n"
    body += "Product Review Pulse Automator\n"
    
    # Check for secret key
    api_key = os.getenv("API_SECRET_KEY")
    headers = {"X-API-Key": api_key} if api_key else None
    
    print(f"Connecting to Gmail MCP server at {server_url}...")
    async with sse_client(server_url, headers=headers) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Invoke the tool
            result = await session.call_tool(
                "create_gmail_draft",
                arguments={
                    "recipient": recipient,
                    "subject": subject,
                    "body": body,
                    "iso_week": iso_week
                }
            )
            
            if result.content and len(result.content) > 0:
                return result.content[0].text
            raise ValueError("No response content from Gmail MCP tool.")

def write_gmail_simulation_locally(pulse_summary: str, fee_summary: str, doc_link: str, iso_week: str) -> str:
    """Writes or updates Gmail draft simulation outputs in local workspace."""
    recipient = os.getenv("GMAIL_RECIPIENT", "team@groww.in")
    subject = f"Weekly Pulse + Fee Explainer — Groww ({iso_week})"
    
    # Construct the body
    body = f"Hi Team,\n\n"
    body += f"Here is the Weekly Product Review Pulse and Fee Explainer for Groww ({iso_week}).\n\n"
    body += "WEEKLY PULSE SUMMARY:\n"
    body += f"{pulse_summary}\n\n"
    body += "FEE EXPLAINER: Mutual Fund Exit Load\n"
    body += f"{fee_summary}\n\n"
    body += f"The full report and historical logs have been appended to the Google Doc:\n{doc_link}\n\n"
    body += "Best regards,\n"
    body += "Product Review Pulse Automator\n"

    start_marker = f"[Start Draft: {iso_week}]"
    end_marker = f"[End Draft: {iso_week}]"
    
    formatted_draft = f"{start_marker}\n"
    formatted_draft += f"To: {recipient}\n"
    formatted_draft += f"Subject: {subject}\n"
    formatted_draft += "Body:\n"
    formatted_draft += f"{body}\n"
    formatted_draft += f"{end_marker}\n"

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    outputs_dir = os.path.join(project_root, "data/outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    simulation_file = os.path.join(outputs_dir, "gmail_simulation.txt")

    file_content = ""
    if os.path.exists(simulation_file):
        with open(simulation_file, "r") as f:
            file_content = f.read()

    if start_marker in file_content and end_marker in file_content:
        start_pos = file_content.find(start_marker)
        end_pos = file_content.find(end_marker) + len(end_marker)
        new_file_content = file_content[:start_pos] + formatted_draft + file_content[end_pos:]
        print(f"[Client Local Gmail] Updated existing draft for {iso_week}")
    else:
        new_file_content = file_content
        if file_content and not file_content.endswith("\n"):
            new_file_content += "\n"
        new_file_content += "\n" + formatted_draft
        print(f"[Client Local Gmail] Created new draft for {iso_week}")

    with open(simulation_file, "w") as f:
        f.write(new_file_content)

    return f"mock_draft_{iso_week}"

def create_gmail_draft(pulse_summary: str, fee_summary: str, doc_link: str, iso_week: str = "unknown") -> str:
    """
    Sends MCP request to Gmail MCP server.
    Returns: email_draft_id (str)
    """
    server_url = os.getenv("MCP_GMAIL_SERVER_URL", "")
    is_remote = "bhavyamcpserver.up.railway.app" in server_url or not server_url
    if os.getenv("USE_MOCK_GOOGLE") == "true" and is_remote:
        print("USE_MOCK_GOOGLE is true and pointing to remote/default server. Writing Gmail draft locally.")
        return write_gmail_simulation_locally(pulse_summary, fee_summary, doc_link, iso_week)

    try:
        return asyncio.run(async_create_gmail_draft(pulse_summary, fee_summary, doc_link, iso_week))
    except Exception as e:
        print(f"Failed to communicate with Gmail MCP server: {e}")
        if os.getenv("USE_MOCK_GOOGLE") == "true":
            print("USE_MOCK_GOOGLE is true. Falling back to local simulation.")
            return write_gmail_simulation_locally(pulse_summary, fee_summary, doc_link, iso_week)
        raise e
