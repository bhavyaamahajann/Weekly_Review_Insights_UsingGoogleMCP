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

def create_gmail_draft(pulse_summary: str, fee_summary: str, doc_link: str, iso_week: str = "unknown") -> str:
    """
    Sends MCP request to Gmail MCP server.
    Returns: email_draft_id (str)
    """
    try:
        return asyncio.run(async_create_gmail_draft(pulse_summary, fee_summary, doc_link, iso_week))
    except Exception as e:
        print(f"Failed to communicate with Gmail MCP server: {e}")
        raise e
