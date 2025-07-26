import functions_framework
from vertexai.preview import reasoning_engines
import vertexai
from vertexai import agent_engines
import uuid
import json
import re

PROJECT_ID = "sahayakai-466115"
LOCATION = "us-east4"
STAGING_BUCKET = "gs://sahayak-agents-bucket"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

def extract_json_from_markdown(text):
    match = re.search(r"⁠  json\s*(\{.*?\})\s*  ⁠", text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print("Invalid JSON found.")
    return None

@functions_framework.http
def answer_from_textbook(request):
    # For more information about CORS and CORS preflight requests, see:
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request

    # Set CORS headers for the preflight request
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }

        return ("", 204, headers)

    # Set CORS headers for the main request
    headers = {"Access-Control-Allow-Origin": "*"}
    prompt = None
    try:
        request_json = request.get_json(silent=True)
        print(f"Request JSON: {request_json}")
        user_query = request_json.get("user_query", "")
        language = request_json.get("language", "")
        prompt = f"{user_query}\n**Answer must be in {language}**"
    except Exception as e:
        return (f"Invalid request body: {e}", 400, headers)
    agent = agent_engines.get('projects/522049177242/locations/us-east4/reasoningEngines/6527263972431757312')    
    print(agent.operation_schemas())
    print(f"Using agent: {agent.name}")
    app = reasoning_engines.AdkApp(
        agent=agent,
        enable_tracing=True,
    )
    user_id = str(uuid.uuid4())
    session = agent.create_session(user_id=user_id)
    events = []
    for event in agent.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=prompt,
    ): events.append(event)

    response_event = events[-1]
    response_text = response_event['content']['parts'][0]['text']
    response_json = extract_json_from_markdown(response_text)

    return (json.dumps(response_json), 200, headers)