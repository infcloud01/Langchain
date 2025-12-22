This is a simple **Quick Start Guide** designed for a non-technical TPM who just wants to get the bot running.

# 🤖 JiraBot: Quick Start Guide

Welcome to JiraBot! This is your AI assistant that talks directly to Jira so you don't have to click through endless menus. It can list tickets, update statuses, change dates, and create new tasks just by chatting with it.

Follow these 3 steps to get started.

### 1. Get Your "Keys" 🔑
Before you run the bot, you need two passwords (API Keys) to allow the bot to talk to the services.

1.  **OpenAI Key (The Brain):**
    *   Go to [OpenAI API Keys](https://platform.openai.com/api-keys).
    *   Click **"Create new secret key."**
    *   Copy the code starting with `sk-...` and save it purely for a moment.
2.  **Jira Cloud Token (The Hands):**
    *   Go to [Atlassian Security](https://id.atlassian.com/manage-profile/security/api-tokens).
    *   Click **"Create API token."**
    *   Label it "JiraBot" and copy the code.

### 2. One-Time Setup ⚙️
*If you haven't installed Python yet, download it here: [python.org](https://www.python.org/downloads/).*

1.  Download the `jirabot.py` file to your computer (e.g., inside a folder called `JiraBot` on your Desktop).
2.  Open your computer's terminal:
    *   **Mac:** Press `Cmd + Space`, type "Terminal", and hit Enter.
    *   **Windows:** Press `Start`, type "cmd", and hit Enter.
3.  Copy and paste this line into the terminal and hit **Enter** to install the required "brain power":
```bash
    pip install langchain langchain-openai langgraph atlassian-python-api
```
    
### 3. Run the Bot 🚀
Every time you want to use the bot, just do this:

1.  Open your Terminal (Mac) or Command Prompt (Windows).
2.  Type `cd` followed by the location of your folder. For example:
    *   `cd Desktop/JiraBot`
3.  Type this command and hit Enter:
```bash
    python jirabot_v1.py
```
    
5.  The bot will ask for your **OpenAI Key** and **Jira Token**. Paste them in (Note: *You won't see the letters appear on screen as you type them—this is for security! Just paste and hit Enter*).

### 🗣️ How to talk to JiraBot
Once you see **"🤖 JiraBot is ready!"**, just type like you are talking to a human assistant.

**Try these commands:**
*   "List my projects."
*   "Show me all the high priority bugs in the KAN project."
*   "What is the status of ticket KAN-123?"
*   "Update KAN-123 to Done."
*   "Create a new task called 'Update Q3 Roadmap' and describe it as 'Prepare slides for leadership review'."
*   "Change the due date for KAN-123 to next Friday."

**Type `quit` when you are done.**
