import datetime
import json
import re
import sys
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool, request_input
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from google.adk.workflow import Workflow, Edge, START, node
from google.genai import types
from mcp import StdioServerParameters

from app.config import config

# Initialize MCP Toolset connection parameters
mcp_params = StdioServerParameters(
    command=sys.executable,
    args=["-m", "app.mcp_server"],
    env={}
)
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(server_params=mcp_params)
)

# 1. Specialized Sub-agents
carbon_advisor = LlmAgent(
    name="carbon_advisor",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are an expert carbon footprint advisor.
Analyze the user's consumption or queries to calculate carbon emissions or suggest energy efficiency measures.
State the carbon impact in kg CO2 where possible. Use calculate_carbon_footprint or search_eco_products if relevant. Be concise.""",
    tools=[mcp_toolset]
)

recycling_advisor = LlmAgent(
    name="recycling_advisor",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are an expert recycling advisor.
Provide clear guidance on waste sorting, recycling, composting, and disposing of specific materials.
Advise on local disposal regulations. Use get_recycling_rules or get_composting_guideline if relevant. Be concise.""",
    tools=[mcp_toolset]
)

# 2. Orchestrator Agent
def get_orchestrator_instruction(ctx) -> str:
    cleaned_text = ctx.state.get("cleaned_text", "")
    base_prompt = """You are the lead Eco-Advisor orchestrator.
Your job is to route user queries to the appropriate advisor:
- For carbon footprints, energy use, or travel impact, delegate to carbon_advisor.
- For waste sorting, recycling, composting, or material disposal, delegate to recycling_advisor.
If the request is ambiguous or you need more info (like location or quantity) to make an accurate suggestion, use the request_input tool to ask the user.
Summarize the advisor's response. Do not call sub-agents if the user query is general conversation."""
    if cleaned_text:
        return f"{base_prompt}\n\nThe cleaned user query is: {cleaned_text}"
    return base_prompt

orchestrator = LlmAgent(
    name="orchestrator",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=get_orchestrator_instruction,
    tools=[
        AgentTool(agent=carbon_advisor),
        AgentTool(agent=recycling_advisor),
        request_input
    ]
)

# 3. Security and Utility Nodes
@node
def security_checkpoint(ctx) -> str:
    user_text = ""
    if ctx.user_content and ctx.user_content.parts:
        user_text = " ".join([part.text for part in ctx.user_content.parts if part.text])

    # PII scrubbing
    cleaned_text = user_text
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    if re.search(email_pattern, cleaned_text):
        cleaned_text = re.sub(email_pattern, "[REDACTED_EMAIL]", cleaned_text)

    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    if re.search(phone_pattern, cleaned_text):
        cleaned_text = re.sub(phone_pattern, "[REDACTED_PHONE]", cleaned_text)

    ctx.state["cleaned_text"] = cleaned_text

    # Prompt injection detection
    injection_keywords = ["ignore previous instructions", "system prompt", "override instructions", "bypass security"]
    is_injection = any(keyword in user_text.lower() for keyword in injection_keywords)

    # Domain specific rule: Block requests containing dangerous or malicious keywords
    unsafe_keywords = ["bomb", "hack", "illegal", "exploit"]
    is_unsafe = any(keyword in user_text.lower() for keyword in unsafe_keywords)

    audit_log = {
        "timestamp": str(datetime.datetime.now()),
        "pii_detected": cleaned_text != user_text,
        "injection_detected": is_injection,
        "unsafe_detected": is_unsafe,
        "action": "clear" if (not is_injection and not is_unsafe) else "block"
    }
    severity = "INFO"
    if cleaned_text != user_text:
        severity = "WARNING"
    if is_injection or is_unsafe:
        severity = "CRITICAL"

    print(json.dumps({"audit_event": audit_log, "severity": severity}))

    if is_injection or is_unsafe:
        ctx.route = "security_event"
        return "security_event"

    ctx.route = "clear"
    return cleaned_text

@node
def security_event(ctx) -> str:
    return "Security Checkpoint Flagged: Input contains potential security risks. Request aborted."

# 4. Workflow Graph
root_agent = Workflow(
    name="eco_advisor_workflow",
    edges=[
        Edge(from_node=START, to_node=security_checkpoint),
        Edge(from_node=security_checkpoint, to_node=orchestrator, route="clear"),
        Edge(from_node=security_checkpoint, to_node=security_event, route="security_event")
    ]
)

app = App(
    root_agent=root_agent,
    name="app"
)
