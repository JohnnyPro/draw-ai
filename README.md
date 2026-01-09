# DrawAI: AI-Powered Image Generation from Natural Language

DrawAI is a Python-based application that translates natural language prompts into images. It leverages a sophisticated agentic architecture to understand user requests, select the appropriate tools, and generate artwork using various drawing backends.

## Key Features

- **Natural Language to Image:** Describe what you want to see, and DrawAI will generate it.
- **Multiple Drawing Backends:** Supports different rendering engines, including Pillow (for raster images), SVG (for vector graphics), and Turtle (for procedural drawings).
- **Intelligent Strategy Selection:** Automatically chooses between a direct "one-go" generation for simple prompts and a more detailed "tool-calling" approach for complex scenes.
- **Human-in-the-Loop:** If a prompt is ambiguous, the system can ask for clarification to ensure the output matches the user's intent.

## Architecture and Technology

This project is built around a robust and observable agentic workflow, using cutting-edge tools to manage complexity and provide clear insights into the generation process.

### Orchestration with LangGraph

The core of DrawAI is an agentic state machine orchestrated by **LangGraph**. This allows for a highly modular and resilient workflow where each step of the image generation process is represented as a node in a graph. The state, including the prompt, intermediate analysis, and selected strategy, flows through the graph, enabling complex logic like conditional branching and loops.

The graph consists of several key nodes:
- **`analyze_prompt`**: Evaluates the user's prompt for clarity and determines if human feedback is needed.
- **`select_strategy`**: Decides whether to use a simple, direct generation method or a more intricate tool-based approach.
- **`route_backend`**: Selects the most suitable drawing library (`Pillow`, `SVG`, or `Turtle`) based on the prompt's requirements.
- **`one_go_executor` / `tool_call_executor`**: Executes the chosen strategy to produce the final image.

This graph-based architecture makes the system easy to extend and debug, as each logical step is isolated and independently testable.

### Observability with LangFuse

To ensure reliability and provide deep insights into the agent's behavior, the project is integrated with **LangFuse**. Every run of the LangGraph is traced, capturing detailed information about the inputs, outputs, and transitions between nodes. This allows for:
- **Debugging:** Visualizing the execution flow to pinpoint errors and inefficiencies.
- **Performance Monitoring:** Analyzing the latency and success rate of different strategies and backends.
- **Evaluation:** Tracking the quality of generated images and the accuracy of the agent's decisions over time.

This level of observability is crucial for understanding and improving the performance of a complex, multi-step AI system.

## How It Works

1.  **Prompt Input:** The user provides a natural language description of the desired image.
2.  **Graph Execution:** The `run_graph.py` script initializes the LangGraph state machine with the prompt.
3.  **Analysis and Clarification:** The `analyze_prompt` node processes the prompt. If it's ambiguous, it can pause and wait for user clarification.
4.  **Strategy and Backend Selection:** The graph dynamically selects the best strategy (`one-go` or `tool-call`) and the most appropriate backend (`Pillow`, `SVG`, or `Turtle`).
5.  **Image Generation:** The corresponding executor node is invoked.
    - In a **`one-go`** scenario, the model generates the image directly.
    - In a **`tool-call`** scenario, the model is given access to a set of primitive drawing functions (e.g., `draw_circle`, `draw_rectangle`) and orchestrates them to build the image step-by-step.
6.  **Output:** The final image is saved to the `outputs` directory.

## Project Structure

```
.
├── graph/                # LangGraph state, nodes, and graph definition
│   ├── nodes/            # Individual nodes for the graph
│   └── drawing_graph.py  # Graph construction
├── primitives/           # Drawing function definitions and implementations
│   ├── definitions.py    # Abstract drawing tool definitions
│   ├── pillow_impl.py    # Pillow backend implementation
│   └── ...
├── main.py               # Main application entry point
├── run_graph.py          # Script to execute the LangGraph workflow
├── observability.py      # LangFuse integration
└── requirements.txt      # Project dependencies
```

## Setup and Usage

### Prerequisites

- Python 3.8+
- An OpenAI API key (or another compatible LLM provider)
- LangFuse account (optional, for tracing)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/JohnnyPro/DrawAi.git
    cd DrawAi
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**
    Create a `.env` file in the root of the project and add your API keys:
    ```
    copy the .env.example file to .env and fill in the values
    `cp .env.example .env`
    ```

### Running the Application

To generate an image, run the `run_graph.py` script with a prompt:

```bash
python run_graph.py "A red house with a blue door and two windows"
```

The generated image will be saved in the `outputs/` directory.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
