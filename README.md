# Product Agent CLI

Product Agent CLI is a command-line tool built on a simple, powerful principle: **plan before you write code**. It automates the critical planning phase of software development, turning a high-level feature idea into a clear, actionable, and developer-ready specification.

## Plan Before You Code

The fastest way to build great software is to get the plan right *first*. Jumping directly into code without a clear specification often leads to wasted effort, misaligned expectations, and expensive rework. This tool helps you build a solid foundation before implementation begins.

By using Product Agent CLI to create a plan, you can:

-   **Solidify the Scope:** Interactively breaks down a feature into detailed user stories and technical requirements, ensuring the "what" and "why" are crystal clear.
-   **Prevent Unplanned Work:** Generates a specific list of files and components to be created or modified, minimizing scope creep and unforeseen complications.
-   **Align the Entire Team:** Produces a clear, shareable plan that gets product, design, and engineering on the same page, creating a single source of truth for the work ahead.

## Designed for the Enterprise

While many modern development tools excel at creating greenfield MVPs, they often fall short in complex enterprise environments. Building a feature that can actually make it to production requires navigating existing infrastructure, adhering to established technical standards, and respecting security protocols. This is the core challenge of "brownfield" development.

Product Agent CLI solves this with a privacy-first, context-aware approach. Instead of requiring risky, broad access to your codebase, our tool empowers you to provide targeted context through a simple `project.context.json` file.

This approach ensures:

-   **A Frictionless Path to Production:** The generated plan is grounded in your technical reality. By specifying the stack, design systems, and testing frameworks, the output is immediately relevant and actionable for your developers.
-   **Privacy and Security:** Maintain full control over your intellectual property. There is no need to expose your proprietary codebase to a third-party service, addressing a primary concern for enterprise security.
-   **Developer Efficiency:** The planning is done right the first time. Developers receive a specification that’s already aligned with their environment, reducing the gap between planning and execution.

## Getting Started

### Prerequisites

-   Python 3.9 or higher
-   A Google API Key with the "Generative Language API" enabled.

### Installation & Setup

To get started, run the following commands in your terminal:

```bash
# Clone the repository and navigate into the directory
git clone https://github.com/nan-bit/product-agent-cli
cd product-agent-cli

# Create a virtual environment and activate it
python3 -m venv venv
source venv/bin/activate

# Install the package in editable mode
pip install -e .

# Create your environment file from the example
cp .env.example .env
```

Next, open the `.env` file and add your Google API key:

```ini
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

## How to Run It

Once set up, you can start the feature planning flow with a single command.

1.  **(Optional) Add Project Context:**
    Before running, you can add technical details to the `project.context.json` file. This helps the agent generate more accurate specifications for your project's tech stack.

    *Example `project.context.json`:*
    ```json
    {
      "tech_stack": "React, FastAPI, PostgreSQL",
      "design_system": "Material UI",
      "testing_framework": "Jest for frontend, Pytest for backend"
    }
    ```

2.  **Run the Agent:**
    Start the interactive session by running:
    ```bash
    product-agent
    ```
    The agent will ask for the feature you want to build and guide you through the rest of the process.

3.  **Review the Output:**
    After the session, you will find the generated user stories, technical specifications, and file lists in the `output` directory.

## Contributing

Contributions are welcome! If you have ideas for improvements or find a bug, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.