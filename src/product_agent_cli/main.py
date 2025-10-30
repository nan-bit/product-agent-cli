import google.generativeai as genai
import os
import json
import re
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

# --- Constants (All Prompts Go Here) ---

SYSTEM_PROMPT = """
You are an expert "Product Architect" agent. Your job is to guide a user from a
high-level feature idea to a complete, actionable plan. You are a "full-stack"
architect, comfortable discussing product strategy, user experience (UX), and
engineering design (EDD) all in one fluid conversation.

Your goal is to gather all the information needed to create two documents:
1.  **The "Feature Plan"**: A human-readable document explaining the "why" and "what" of the feature.
2.  **The "Execution Spec"**: A machine-readable JSON file with EARS-style requirements for a coding agent.

**Your Conversation Flow:**
1.  **Acknowledge Context**: If context is provided, state it. (e.g., "Working on 'Project X' with a React stack...").
2.  **Start High (The "Why")**: Always start with the problem.
    * "What user problem are we solving?"
    * "Why does this matter for the user?"
    * "How will we measure success?"
3.  **Move to "What" (The "CUJ / User Stories")**:
    * "Walk me through the ideal user journey."
    * "What's the most critical step for the user?"
    * "Are there any edge cases? (e.g., error handling, empty states)"
4.  **Move to "How" (The "Implementation")**:
    * "What new UI components will we need?"
    * "Does this need a new API endpoint? What should it do?"
    * "How should this interact with existing systems?"
5.  **Signal Completion**: Once you have gathered all the necessary information for both the plan and the spec, you MUST instruct the user to end the conversation. Your final message should be something like:

    "Excellent. I have everything I need. To generate the final artifacts, please type 'done' or 'exit'."

You MUST NOT generate the plan or the spec in the conversation. Your only job is to gather the information and then instruct the user to end the session.

**Context Injection (if provided):**
This is a "brownfield" project. The user has provided context. You MUST adhere
to these constraints.
---
{context_json}
---
"""

SYNTHESIZE_PLAN_PROMPT = """
Based on our entire conversation, synthesize the human-readable "Feature Plan"
in Markdown. The plan MUST include:
1.  **Feature Name**: (e.g., "Auth: Forgot Password Flow")
2.  **Problem Statement**: (The "Why")
3.  **Success Metrics**: (How we know it works)
4.  **User Stories / Journey**: (The "What")
5.  **Implementation Notes**: (The "How", including high-level API needs or UI components)
6.  **Edge Cases & Security**: (e.g., "User is not found", "Rate limiting")

You MUST only output the Markdown content, with no other text or formatting.

**Adhere to this context (if provided):**
---
{context_json}
---

Here is our conversation history:
{history}

Generate the Markdown file now.
""" 

SYNTHESIZE_SPEC_PROMPT = """
Based on our entire conversation, synthesize the machine-readable "Execution Spec"
in **MARKDOWN**. The user expects the spec to be detailed and structured using Markdown headings and bullet points.

Example of the expected output:

```markdown
# Execution Specification

## Feature: Example Feature

### Requirements:
*   **REQ-001 [Type: SYSTEM]** The system shall do something.
*   **REQ-002 [Type: USER_STORY]** When the user does something, the system shall respond.
```

Here is the structure I expect:

# Execution Specification

## Feature: [Feature Name]

### Requirements:
*   **[ID] [Type: USER_STORY | SYSTEM | SECURITY | ACCESSIBILITY]** [A clear, testable, EARS-style requirement. (e.g., WHEN a user clicks 'Forgot Password', THE SYSTEM SHALL navigate to the 'Password Reset' view.)]


**Rules:**
* Create a requirement for EVERY actionable item, user story, and system behavior we discussed.
* IDs must be sequential (REQ-001, REQ-002, ...).
* The `requirement` text is CRITICAL. It must be a clear instruction for a coding agent.

**Adhere to this context (if provided):**
---
{context_json}
---

Here is our conversation history:
{history}

Generate the Markdown file now.
"""

# Renamed from GEMINI_MD...
AGENT_INSTRUCTIONS_FILENAME = "AGENT_INSTRUCTIONS.md"
AGENT_INSTRUCTIONS_CONTENT = """
# Agent Instructions: "Code Executor Agent"

This file describes the expected behavior of an AI Code Executor Agent.

An Executor Agent is a tool that reads the generated `*.spec.md` and `*.plan.md`
files and performs the required coding tasks.

## 1. Load Context
The agent **must** always look for and read these two files:
1.  `project.context.json`: This defines the tech stack (e.g., React, FastAPI) and design system. All generated code must adhere to it.
2.  `*_plan.md`: This is the human-readable "why" for the feature. It must be used for context on the user's goals.

## 2. Receive a Work Order
The agent is activated by being given a path to a `*.spec.md` file. This file is its "Work Order."

## 3. Execute the Work Order
When given a spec, the agent's task is to:
1.  Load and parse the `.md` file.
2.  Initialize a "Build Report" to track the status of each requirement.
3.  Iterate through **every single requirement** in the `requirements` array.
4.  For each requirement, generate the complete, production-ready code to implement it, following the tech stack from `project.context.json`.
5.  The agent must clearly state which file paths the code should be saved to (e.g., `src/components/ResetPasswordView.jsx`).
6.  After code for a requirement is generated and confirmed, mark it as `"SUCCESS"` in the Build Report.
7.  If a problem is identified and the code is *not* implemented, mark it as `"FAILED"` and note the reason.

## 4. Report Build Status
After all requirements have been attempted:
1.  The agent **must** provide a final "Build Report".
2.  This report **must** clearly list:
    * **Successfully Built Requirements:** (e.g., `[SUCCESS] REQ-001: ...`, `[SUCCESS] REQ-002: ...`)
    * **Failed Requirements:** (e.g., `[FAILED] REQ-003: ... (Reason: API specification was incomplete.)`)
3.  Conclude with a summary of the feature's status (e.g., "The feature is **partially built**. 2 of 3 requirements are complete.")
"""

# --- Helper Functions ---

def sanitize_filename(text: str) -> str:
    """Converts a feature description into a safe filename."""
    text = text.lower().strip()
    # Replace spaces and hyphens with underscores
    text = re.sub(r'[\s-]', '_', text)
    # Remove any characters that are not alphanumeric or underscores
    text = re.sub(r'[^a-z0-9_]', '', text)
    # Remove leading/trailing underscores
    text = text.strip('_')
    if not text:
        text = "feature_plan"
    return text

def generate_feature_name(initial_idea: str, model) -> str:
    """Generates a short, 2-3 word feature name from the user's initial idea."""
    prompt = f"You are a naming expert. Given the following feature description, suggest a short, 2-3 word feature name that can be used as a filename.\n\nFeature Description: \"{initial_idea}\"\n\nSuggested Name:"
    response = model.generate_content(prompt)
    return response.text.strip()

def load_context(console: Console) -> (str, str):
    """Loads context from 'project.context.json' if it exists."""
    context_file = "project.context.json"
    if os.path.exists(context_file):
        try:
            with open(context_file, 'r') as f:
                context_data = json.load(f)
            context_json = json.dumps(context_data, indent=2)
            product_name = context_data.get('product', {}).get('name', 'this project')
            stack = context_data.get('engineering', {}).get('stack', 'defined')
            context_msg = f"Context loaded from ./{context_file}. I see we're working on '{product_name}' with a {stack} stack."
            return context_json, context_msg
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Found 'project.context.json' but couldn't read it: {e}")
            return "{}", ""
    else:
        return "{}", "Starting a new greenfield plan."

def format_history_for_prompt(history: list) -> str:
    """Converts the chat history into a simple text block."""
    return "\n".join(f"[{msg['role'].capitalize()}]: {msg['parts']}" for msg in history)

# --- Main Application Logic ---

def main(console: Console = None):
    if console is None:
        console = Console()
    console.print("[bold cyan]Welcome to the Feature Planner CLI[/bold cyan]")

    # 1. Load API Key
    load_dotenv()
    # Use GOOGLE_API_KEY, which is the standard for the `google-generativeai` library
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] `GOOGLE_API_KEY` not found.")
        console.print("Please create a `.env` file and add your API key.")
        console.print("Example: `GOOGLE_API_KEY=\"your_api_key_here\"`")
        sys.exit(1)
    
    genai.configure(api_key=api_key)

    # 2. Get initial idea from command line arguments
    initial_idea = " ".join(sys.argv[1:]).strip()
    if not initial_idea:
        console.print("[bold red]Error:[/bold red] Please provide an initial feature idea.")
        console.print("Example: `plan \"Build a new settings page\"`")
        sys.exit(1)

    # Generate a short feature name
    try:
        feature_name = generate_feature_name(initial_idea, genai.GenerativeModel('gemini-pro-latest'))
        console.print(f"[bold]Generated Feature Name:[/bold] {feature_name}\n")
    except Exception as e:
        console.print(f"[bold red]Error generating feature name:[/bold red] {e}")
        # Fallback to the original idea if name generation fails
        feature_name = initial_idea

    console.print(f"[bold]Planning feature:[/bold] {initial_idea}\n")

    # 3. Load project context
    context_json, context_msg = load_context(console)
    console.print(f"[italic]{context_msg}[/italic]\n")

    # 4. Set up the generative model and stateful chat
    try:
        # We still use the Gemini API, just not the CLI
        model = genai.GenerativeModel('gemini-pro-latest')
        system_prompt = SYSTEM_PROMPT.format(context_json=context_json)
        chat = model.start_chat(history=[
            {'role': 'user', 'parts': [system_prompt]},
            {'role': 'model', 'parts': ["OK, I am the 'Product Architect' agent. Let's get started. What is the high-level goal or problem you're trying to solve with this feature?"]}
        ])
        
        # Send the user's first idea (from the CLI arg)
        first_prompt = f"My initial idea is: \"{initial_idea}\". Let's start from there."
        response = chat.send_message(first_prompt)
        console.print(Markdown(f"**Agent:** {response.text}"))

    except Exception as e:
        console.print(f"[bold red]Error starting chat:[/bold red] {e}")
        sys.exit(1)

    # 5. Start the interactive chat loop
    try:
        while True:
            user_input = console.input("[bold green]You:[/bold green] ").strip()

            if user_input.lower() in ["done", "save", "finish", "exit", "quit", "q"]:
                console.print("\n[bold cyan]Great. I'll synthesize our conversation and generate the artifacts...[/bold cyan]")
                break
            
            if not user_input:
                continue

            response = chat.send_message(user_input)
            console.print(Markdown(f"**Agent:** {response.text}"))

    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold cyan]Session ended. Synthesizing files...[/bold cyan]")
    
    # 6. Final Synthesis
    try:
        # We need to format the history for the *synthesis* prompts
        simple_history = []
        for msg in chat.history:
            # We skip the long system prompt
            if msg.parts[0].text == system_prompt:
                continue
            simple_history.append({'role': msg.role, 'parts': msg.parts[0].text})

        history_str = format_history_for_prompt(simple_history)
        base_filename = sanitize_filename(feature_name)
        
        console.print("\n[bold]Generating artifacts...[/bold]")

        # --- Generate .plan.md (Human-Readable) ---
        plan_prompt = SYNTHESIZE_PLAN_PROMPT.format(history=history_str, context_json=context_json)
        plan_response = model.generate_content(plan_prompt)
        plan_md_file = f"{base_filename}.plan.md"
        with open(plan_md_file, "w") as f:
            f.write(plan_response.text)
        console.print(f"✅ Created: ./{plan_md_file}")

        # --- Generate .spec.md (Machine-Readable) ---
        spec_prompt = SYNTHESIZE_SPEC_PROMPT.format(history=history_str, context_json=context_json)
        spec_response = model.generate_content(spec_prompt)
        
        if not spec_response.text.strip():
            console.print("\n[bold red]Error:[/bold red] The model did not generate any content for the spec file.")
            sys.exit(1)
        
        spec_md_file = f"{base_filename}.spec.md"
        with open(spec_md_file, "w") as f:
            f.write(spec_response.text)
        console.print(f"✅ Created: ./{spec_md_file}")
        
        # --- Generate AGENT_INSTRUCTIONS.md (Executor Instructions) ---
        if not os.path.exists(AGENT_INSTRUCTIONS_FILENAME):
            with open(AGENT_INSTRUCTIONS_FILENAME, "w") as f:
                f.write(AGENT_INSTRUCTIONS_CONTENT)
            console.print(f"✅ Created: ./{AGENT_INSTRUCTIONS_FILENAME} (Executor instructions)")
        else:
            console.print(f"ℹ️ Found:   ./{AGENT_INSTRUCTIONS_FILENAME} (already exists, skipping)")

        console.print("\n[bold green]All files generated successfully![/bold green]")
        console.print("Your artifacts are ready for an execution agent.")

    except Exception as e:
        console.print(f"\n[bold red]Error during synthesis:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
