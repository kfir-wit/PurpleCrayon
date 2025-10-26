# PurpleCrayon

A Python package for AI agent development with LangChain and LangGraph, built with modern Python patterns and async-first design.

## Features

- 🤖 **AI Agent Framework**: Build sophisticated AI agents with ease
- 🔗 **LangChain Integration**: Seamless integration with LangChain tools and chains
- 📊 **LangGraph Support**: Create complex agent workflows with LangGraph
- ⚡ **Async-First Design**: Built for modern Python with async/await patterns
- 🛠️ **Rich Tool Ecosystem**: Decorators and utilities for tool creation
- 🧪 **Comprehensive Testing**: Full test suite with pytest and async support
- 📦 **Modern Packaging**: Uses pyproject.toml and follows Python packaging best practices

## Installation

### From Source

```bash
git clone https://github.com/purplecrayon/purplecrayon.git
cd purplecrayon
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/purplecrayon/purplecrayon.git
cd purplecrayon
pip install -e ".[dev,test]"
```

## Quick Start

### Creating Your First Agent

```python
from purplecrayon import create_agent, run_agent_async

# Create an agent
agent = create_agent(
    name="my_agent",
    description="A helpful AI agent",
    model="gpt-4",
    temperature=0.7
)

# Run the agent
result = await run_agent_async(agent, "Hello, world!")
print(result)
```

### Using Decorators for LangChain Tools

```python
from purplecrayon.decorators import langchain_tool, async_tool

@langchain_tool(
    name="weather_tool",
    description="Get current weather information"
)
@async_tool
async def get_weather(location: str) -> str:
    """Get weather for a specific location."""
    # Your weather API logic here
    return f"Weather in {location}: Sunny, 72°F"

# Add the tool to your agent
agent.add_tool("weather", get_weather)
```

### Creating Agent Workflows

```python
from purplecrayon.utils import create_agent_workflow

# Define workflow steps
workflow_steps = [
    {
        "name": "analyze_input",
        "function": analyze_user_input,
        "description": "Analyze the user's input",
        "next": "generate_response"
    },
    {
        "name": "generate_response",
        "function": generate_ai_response,
        "description": "Generate AI response"
    }
]

workflow = create_agent_workflow(workflow_steps)
```

## Project Structure

```
purplecrayon/
├── purplecrayon/                 # Main package folder
│   ├── __init__.py               # Package initialization
│   ├── core.py                   # Core agent functionality
│   ├── decorators.py             # LangChain tool decorators
│   └── utils.py                  # Helper functions
├── tests/                        # Unit tests
│   ├── __init__.py
│   └── test_core.py
├── pyproject.toml               # Modern build system metadata
├── README.md
├── LICENSE
└── .gitignore
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=purplecrayon

# Run specific test file
pytest tests/test_core.py
```

### Code Formatting

```bash
# Format code with black
black purplecrayon tests

# Sort imports with isort
isort purplecrayon tests

# Type checking with mypy
mypy purplecrayon
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the amazing AI framework
- [LangGraph](https://github.com/langchain-ai/langgraph) for workflow management
- The Python community for excellent tooling and libraries

## Support

- 📖 [Documentation](https://purplecrayon.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/purplecrayon/purplecrayon/issues)
- 💬 [Discussions](https://github.com/purplecrayon/purplecrayon/discussions)

---

Made with ❤️ by the PurpleCrayon Team