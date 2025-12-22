import os
import getpass
from datetime import datetime
from typing import Annotated, TypedDict

# Third-party libraries
from atlassian import Jira
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# ==========================================
# 1. AUTHENTICATION & CONFIGURATION
# ==========================================
print("--- JIRA BOT SETUP ---")

# A. OpenAI Setup
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter OpenAI API Key: ")

# B. Jira Cloud Setup
# Replace these with your actual details or leave as is to be prompted
JIRA_URL = "https://yourdomain.atlassian.net/" # <--- UPDATE THIS WITH YOUR CLOUD URL
JIRA_EMAIL = "email@email.com"          # <--- UPDATE THIS WITH THE EMAIL YOU LOG INTO JIRA CLOUD WITH

if "your-domain" in JIRA_URL:
    JIRA_URL = input("Enter Jira Cloud URL (e.g., https://xyz.atlassian.net): ").strip()
if "your-email" in JIRA_EMAIL:
    JIRA_EMAIL = input("Enter Jira Login Email: ").strip()

JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")
if not JIRA_API_TOKEN:
    print("Note: Generate Token at https://id.atlassian.com/manage-profile/security/api-tokens")
    JIRA_API_TOKEN = getpass.getpass("Enter Jira Cloud API Token: ").strip()

# Initialize Jira Client (CLOUD VERSION)
try:
    jira = Jira(
        url=JIRA_URL,
        username=JIRA_EMAIL,
        password=JIRA_API_TOKEN,
        cloud=True  # Required for Cloud
    )
    # Quick connectivity check
    user = jira.myself()
    print(f"✅ Connected to Jira as: {user['displayName']}")
except Exception as e:
    print(f"❌ Jira Connection Failed: {e}")
    exit(1)

# ==========================================
# 2. DEFINE TOOLS
# ==========================================

@tool
def list_projects():
    """
    Retrieves a list of all Jira projects visible to the user.
    Use this to find Project Keys.
    """
    try:
        projects = jira.projects()
        simplified = [f"{p['name']} (Key: {p['key']})" for p in projects]
        return "\n".join(simplified) if simplified else "No projects found."
    except Exception as e:
        return f"Error listing projects: {str(e)}"

@tool
def list_jiras(jql_query: str):
    """
    Searches for tickets using JQL (Jira Query Language).
    Examples:
    - "project = KAN AND priority = High"
    - "assignee = currentUser() AND resolution = Unresolved"
    """
    try:
        results = jira.jql(jql_query, limit=10)
        issues = results.get("issues", [])
        if not issues:
            return "No tickets found matching that query."
        
        summary_list = []
        for issue in issues:
            fields = issue['fields']
            summary_list.append(
                f"[{issue['key']}] {fields['summary']} "
                f"(Status: {fields['status']['name']}, Priority: {fields['priority']['name']})"
            )
        return "\n".join(summary_list)
    except Exception as e:
        return f"JQL Error: {str(e)}"

@tool
def get_ticket_details(ticket_id: str):
    """Retrieves full details for a specific ticket (e.g., KAN-123)."""
    try:
        issue = jira.issue(ticket_id)
        f = issue['fields']
        return (
            f"Key: {issue['key']}\n"
            f"Summary: {f['summary']}\n"
            f"Status: {f['status']['name']}\n"
            f"Priority: {f['priority']['name']}\n"
            f"Assignee: {f['assignee']['displayName'] if f['assignee'] else 'Unassigned'}\n"
            f"Due Date: {f['duedate']}\n"
            f"Description: {f['description']}"
        )
    except Exception as e:
        return f"Error getting ticket {ticket_id}: {str(e)}"

@tool
def update_ticket_status(ticket_id: str, new_status: str):
    """Updates the status of a ticket (e.g., 'Done', 'In Progress')."""
    try:
        jira.set_issue_status(ticket_id, new_status)
        return f"Successfully updated {ticket_id} to {new_status}."
    except Exception as e:
        return f"Error updating status: {str(e)}"

@tool
def update_due_date(ticket_id: str, date_str: str):
    """Updates due date. date_str must be 'YYYY-MM-DD'."""
    try:
        jira.update_issue_field(ticket_id, {'duedate': date_str})
        return f"Successfully updated due date of {ticket_id} to {date_str}."
    except Exception as e:
        return f"Error updating date: {str(e)}"

@tool
def create_ticket(summary: str, issue_type: str = "Task", description: str = ""):
    """
    Creates a new ticket in the KAN project.
    """
    try:
        issue_dict = {
            'project': {'key': 'KAN'}, # <--- HARDCODED FOR YOUR WORKFLOW
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type},
        }
        new_issue = jira.create_issue(fields=issue_dict)
        return f"Created ticket {new_issue['key']}: {summary}"
    except Exception as e:
        return f"Error creating ticket: {str(e)}"

# List of tools provided to the LLM
tools = [list_projects, list_jiras, get_ticket_details, update_ticket_status, update_due_date, create_ticket]

# ==========================================
# 3. AGENT SETUP (LLM & GRAPH)
# ==========================================

# Initialize LLM with longer timeout
llm = ChatOpenAI(model="gpt-4o", temperature=0, request_timeout=120)
llm_with_tools = llm.bind_tools(tools)

# Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# System Prompt
def get_system_message():
    date_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""You are an expert Technical Program Manager (TPM) assistant for the 'Jirabot' project.

CONTEXT:
- **Project Key:** KAN
- **Current Date:** {date_str}

RULES:
1. Unless asked otherwise, scope all JQL searches to 'project = KAN'.
2. If the user gives a relative date (e.g., "next Friday"), calculate the YYYY-MM-DD format.
3. Be concise and professional.
"""
    return SystemMessage(content=prompt)

# Node: Agent (The Brain)
def agent_node(state: AgentState):
    sys_msg = get_system_message()
    # Prepend system message to history
    messages = [sys_msg] + state["messages"]
    result = llm_with_tools.invoke(messages)
    return {"messages": [result]}

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

react_graph = builder.compile()

# ==========================================
# 4. MAIN CHAT LOOP
# ==========================================

def chat():
    print("\n🤖 JiraBot is ready! (Type 'quit' to exit)")
    print("Example: 'List my high priority tickets' or 'Create a task to update docs'")
    
    # Simple memory for this session
    conversation_history = []

    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["quit", "exit"]:
                break
            
            # Prepare state
            conversation_history.append(HumanMessage(content=user_input))
            
            # Stream response
            events = react_graph.stream(
                {"messages": conversation_history},
                stream_mode="values"
            )
            
            for event in events:
                if "messages" in event:
                    msg = event["messages"][-1]
                    if msg.type == "ai":
                        # Only print final AI response, not tool calls (keeps it clean)
                        if not msg.tool_calls:
                            print(f"Agent: {msg.content}")
                            conversation_history.append(msg)
                    elif msg.type == "tool":
                        # Optional: Print tool output for debugging
                        # print(f"[System] Tool Output: {msg.content}")
                        pass
                        
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    chat()