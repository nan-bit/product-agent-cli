# Feature Planner CLI (plan)

This is a standalone Python CLI tool that acts as an expert "Product Architect." It guides you through an interactive chat session with Google's generative AI to transform a high-level feature idea into a complete, actionable development plan. The tool automates the initial planning phase of software projects, allowing you to quickly define the "why," "what," and "how" of a new feature.

## Features

*   **Interactive Chat**: Engages you in a stateful, terminal-based conversation to deeply explore and define your feature.
*   **Context-Aware**: Automatically detects a `project.context.json` file in your project directory to understand your existing tech stack and design system, integrating these constraints into the planning process.
*   **Generates Key Artifacts**: At the end of the planning session, the tool synthesizes the conversation into two crucial files:
    *   `[feature].plan.md`: A human-readable Markdown document detailing the "why" and "what" of your feature, perfect for stakeholders and product managers.
    *   `[feature].spec.md`: A machine-readable Markdown document with EARS-style requirements, designed for execution by an AI coding agent or a human developer.
    *   `AGENT_INSTRUCTIONS.md`: A generic specification for an "Executor Agent," created once to guide automated development.

## Setup & Installation

To get started with the Feature Planner CLI, follow these steps:

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd product-agent-cli
    ```

2.  **Create and Activate a Virtual Environment**:
    It's highly recommended to use a virtual environment to manage project dependencies and avoid conflicts with your system's Python installation.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *(Note: If you're on a Python version older than 3.10 and encounter any errors, please consider upgrading your Python to 3.10 or newer for better compatibility with modern libraries.)*

3.  **Install the Tool**:
    This command reads the `pyproject.toml` file and installs the tool (along with its dependencies) in "editable" mode (`-e`). This means any changes you make to the source code (e.g., in `src/product_agent_cli/main.py`) will automatically be reflected when you run the `plan` command.
    ```bash
    pip install -e .
    ```

4.  **Create your Google AI API Key file**:
    The tool requires access to Google's generative AI.
    *   Obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Copy the example environment file and add your API key to it:
        ```bash
        cp .env.example .env
        nano .env  # Or use any text editor to add your key: GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```

## How to Use

**Important Note:** This tool generates new files (`.plan.md`, `.spec.md`, and `AGENT_INSTRUCTIONS.md`) in the directory where it's executed. To keep your projects organized and avoid clutter, it's highly recommended to navigate to an empty directory or a dedicated planning sub-directory before running the `plan` command.

Once installed and configured, you can run the `plan` command from any directory (as long as your virtual environment is active).

**Step 1: Start a Planning Session**

Initiate a new planning session by providing your high-level feature idea to the `plan` command. Remember to enclose your idea in quotes if it contains spaces.

```bash
# Example for a new project (greenfield)
plan "Build a new login page"

# Example for an existing project (brownfield) with project context
# (Make sure you have a project.context.json file in your CWD)
plan "Add 2-factor authentication"
```

**Step 2: Have an Interactive Conversation with the Architect Agent**

The tool will start an interactive chat session. The AI "Product Architect" agent will guide you through a structured conversation to define the "what," "why," and "how" of your feature. Engage with the agent, answer its questions, and provide details as needed.

When the agent has gathered all the necessary information, it will instruct you to end the conversation.

**Step 3: Generate Your Artifacts**

When instructed by the agent, type `done` (or `exit`, `save`, `finish`, `quit`, `q`) and press Enter to conclude the interactive session. The tool will then synthesize the conversation and generate the planning artifacts.

```
...
Agent: Excellent. I have everything I need. To generate the final artifacts, please type 'done' or 'exit'.
You: done

Generating artifacts...
✅ Created: ./your_generated_feature_name.plan.md
✅ Created: ./your_generated_feature_name.spec.md
✅ Created: ./AGENT_INSTRUCTIONS.md (Executor instructions)

All files generated successfully!
Your artifacts are ready for an execution agent.
```

**Step 4: Use the Artifacts**

The generated `.plan.md` and `.spec.md` files are now ready to be used. The `.plan.md` provides a human-readable summary, while the `.spec.md` offers a detailed, structured specification for an AI "Executor Agent" (which you could build) or a human developer. The `AGENT_INSTRUCTIONS.md` file outlines how such an agent should behave.

## Development

### Running Tests

To ensure the project's quality and correctness, you can run the unit tests. Make sure `pytest` is installed in your virtual environment:

```bash
pip install pytest
```

Then, run the tests from the root of the project:

```bash
pytest
```
