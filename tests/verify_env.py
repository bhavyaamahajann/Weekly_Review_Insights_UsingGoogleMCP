import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_embeddings():
    print("=== Checking Embeddings ===")
    try:
        from sentence_transformers import SentenceTransformer
        print("Loading BAAI/bge-large-en-v1.5 model...")
        model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        print("Model loaded successfully!")
        
        # Test encode
        sentences = ["This is a test review of Groww.", "Great UI, but fees are high."]
        embeddings = model.encode(sentences)
        print(f"Generated embeddings of shape: {embeddings.shape}")
        return True
    except Exception as e:
        print(f"FAILED to load BAAI/bge-large-en-v1.5: {e}")
        return False

def verify_groq():
    print("\n=== Checking Groq API ===")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        print("WARNING: GROQ_API_KEY is not set or still set to placeholder.")
        return False
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        print("Sending test request to Groq...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Hello, is your API working?",
                }
            ],
            model="llama-3.3-70b-versatile",  # standard Groq model
        )
        print(f"Groq API Response: {chat_completion.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"FAILED to call Groq API: {e}")
        return False

def verify_mcp():
    print("\n=== Checking MCP Servers ===")
    gdoc_url = os.getenv("MCP_GDOC_SERVER_URL")
    gmail_url = os.getenv("MCP_GMAIL_SERVER_URL")
    print(f"Configured Google Doc MCP URL: {gdoc_url}")
    print(f"Configured Gmail MCP URL: {gmail_url}")
    
    import urllib.request
    
    mcp_ok = True
    for name, url in [("Google Doc MCP", gdoc_url), ("Gmail MCP", gmail_url)]:
        if not url:
            print(f"WARNING: {name} URL is not configured.")
            mcp_ok = False
            continue
        try:
            print(f"Pinging {name} at {url}...")
            # Simple HTTP ping
            with urllib.request.urlopen(url, timeout=5) as response:
                status = response.getcode()
                print(f"{name} responded with status: {status}")
        except Exception as e:
            print(f"Could not connect to {name} at {url}: {e} (This is expected if the server is not running yet)")
            mcp_ok = False
            
    return mcp_ok

if __name__ == "__main__":
    emb = verify_embeddings()
    groq_ok = verify_groq()
    mcp_ok = verify_mcp()
    
    print("\n=== Summary ===")
    print(f"1. Embeddings: {'PASSED' if emb else 'FAILED'}")
    print(f"2. Groq API:  {'PASSED' if groq_ok else 'FAILED'}")
    print(f"3. MCP Servs:  {'PASSED' if mcp_ok else 'FAILED (Expected if servers are not running)'}")
    
    # Exit with 0 if embeddings passed (since Groq and MCP depend on keys/servers that user has to run/provide)
    if emb:
        print("\nScaffolding verification complete. Embeddings are ready!")
        sys.exit(0)
    else:
        sys.exit(1)
