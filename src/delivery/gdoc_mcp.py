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
    iso_week = payload.get("iso_week")
    
    # Serialize the payload
    content_json = json.dumps(payload)
    
    # Check for secret key
    api_key = os.getenv("API_SECRET_KEY")
    headers = {"X-API-Key": api_key} if api_key else None
    
    print(f"Connecting to Google Doc MCP server at {server_url}...")
    async with sse_client(server_url, headers=headers) as (read_stream, write_stream):
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

def write_gdoc_simulation_locally(payload: dict, iso_week: str) -> str:
    """Writes or updates Google Doc simulation outputs in local workspace."""
    date_str = payload.get("date", "")
    pulse_data = payload.get("weekly_pulse", {})
    summary = pulse_data.get("weekly_summary", "")
    sentiment = pulse_data.get("sentiment", {})
    pos = sentiment.get("positive", 0)
    neg = sentiment.get("negative", 0)
    neu = sentiment.get("neutral", 0)
    action_ideas = pulse_data.get("action_ideas", [])
    
    fee_scenario = payload.get("fee_scenario", "Mutual Fund Exit Load")
    explanation_bullets = payload.get("explanation_bullets", [])
    source_links = payload.get("source_links", [])
    last_checked = payload.get("last_checked", "")

    formatted_content = f"[Start Week: {iso_week}]\n"
    formatted_content += "=================================================================\n"
    formatted_content += f"Groww Weekly Review Pulse — {iso_week}\n"
    formatted_content += "=================================================================\n"
    formatted_content += f"Date: {date_str}\n\n"
    formatted_content += "WEEKLY PULSE SUMMARY:\n"
    formatted_content += f"{summary}\n\n"
    formatted_content += "CUSTOMER SENTIMENT:\n"
    formatted_content += f"- Positive: {pos}%\n- Negative: {neg}%\n- Neutral: {neu}%\n\n"
    formatted_content += "ACTION IDEAS:\n"
    for idx, idea in enumerate(action_ideas, start=1):
        formatted_content += f"  {idx}. {idea}\n"
    formatted_content += "\n"
    formatted_content += f"FEE EXPLAINER SCENARIO: {fee_scenario}\n"
    formatted_content += "-----------------------------------------------------------------\n"
    for bullet in explanation_bullets:
        formatted_content += f"- {bullet}\n"
    formatted_content += "\n"
    formatted_content += "SOURCES:\n"
    for src in source_links:
        if isinstance(src, dict):
            src_str = f"{src.get('name', '')} ({src.get('url', '')})"
        else:
            src_str = str(src)
        formatted_content += f"- {src_str}\n"
    formatted_content += f"Last Checked: {last_checked}\n"
    formatted_content += "=================================================================\n"
    formatted_content += f"[End Week: {iso_week}]\n"

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    outputs_dir = os.path.join(project_root, "data/outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    simulation_file = os.path.join(outputs_dir, "gdoc_simulation.md")

    start_marker = f"[Start Week: {iso_week}]"
    end_marker = f"[End Week: {iso_week}]"

    file_content = ""
    if os.path.exists(simulation_file):
        with open(simulation_file, "r") as f:
            file_content = f.read()

    if start_marker in file_content and end_marker in file_content:
        start_pos = file_content.find(start_marker)
        end_pos = file_content.find(end_marker) + len(end_marker)
        new_file_content = file_content[:start_pos] + formatted_content + file_content[end_pos:]
        print(f"[Client Local Doc] Updated existing section for {iso_week}")
    else:
        new_file_content = file_content
        if file_content and not file_content.endswith("\n"):
            new_file_content += "\n"
        new_file_content += "\n" + formatted_content
        print(f"[Client Local Doc] Appended new section for {iso_week}")

    with open(simulation_file, "w") as f:
        f.write(new_file_content)

    return f"mock_sec_{iso_week}"

def append_to_gdoc(payload: dict, doc_section_id: str = None) -> str:
    """
    Sends MCP request to Google Docs MCP server.
    Returns: doc_section_id (str)
    """
    iso_week = payload.get("iso_week")
    if not iso_week:
        from src.analysis.pulse_generator import get_iso_week_key
        iso_week = get_iso_week_key()

    server_url = os.getenv("MCP_GDOC_SERVER_URL", "")
    is_remote = "bhavyamcpserver.up.railway.app" in server_url or not server_url
    if os.getenv("USE_MOCK_GOOGLE") == "true" and is_remote:
        print("USE_MOCK_GOOGLE is true and pointing to remote/default server. Writing Google Doc locally.")
        return write_gdoc_simulation_locally(payload, iso_week)

    try:
        return asyncio.run(async_append_to_gdoc(payload, doc_section_id))
    except Exception as e:
        print(f"Failed to communicate with Google Doc MCP server: {e}")
        if os.getenv("USE_MOCK_GOOGLE") == "true":
            print("USE_MOCK_GOOGLE is true. Falling back to local simulation.")
            return write_gdoc_simulation_locally(payload, iso_week)
        raise e
