import os
import json
import asyncio
from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.sse import sse_client

load_dotenv()

async def async_append_to_gdoc(payload: dict, doc_section_id: str = None) -> str:
    """Async client connection to Google Docs MCP server."""
    server_url = os.getenv("MCP_GDOC_SERVER_URL", "http://localhost:3001")
    if not server_url.endswith("/sse"):
        server_url = server_url.rstrip("/") + "/sse"
        
    document_id = os.getenv("GDOC_DOCUMENT_ID", "your_google_doc_id")
    iso_week = doc_section_id or payload.get("iso_week")
    
    # Serialize the payload
    content_json = json.dumps(payload)
    
    print(f"Connecting to Google Doc MCP server at {server_url}...")
    async with sse_client(server_url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Invoke the tool
            result = await session.call_tool(
                "append_to_google_doc",
                arguments={
                    "document_id": document_id,
                    "content_json": content_json,
                    "iso_week": iso_week
                }
            )
            
            if result.content and len(result.content) > 0:
                return result.content[0].text
            raise ValueError("No response content from Google Doc MCP tool.")

def append_to_gdoc(payload: dict, doc_section_id: str = None) -> str:
    """
    Sends MCP request to Google Docs MCP server.
    Returns: doc_section_id (str)
    """
    try:
        return asyncio.run(async_append_to_gdoc(payload, doc_section_id))
    except Exception as e:
        print(f"Failed to communicate with Google Doc MCP server: {e}")
        # Return a simulated failure ID so testing can proceed if desired
        raise e
