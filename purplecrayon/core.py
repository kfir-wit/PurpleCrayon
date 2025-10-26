"""
Core functionality for PurpleCrayon.

This module contains the main logic and functions for the PurpleCrayon package.
"""

from typing import Any, Dict, List, Optional, Union
import asyncio
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for AI agents."""
    name: str
    description: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    tools: List[str] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []


class PurpleCrayonAgent:
    """Main agent class for PurpleCrayon."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.tools = []
        self.memory = {}
    
    async def process(self, input_data: str) -> Dict[str, Any]:
        """Process input data through the agent."""
        # Placeholder for main processing logic
        return {
            "input": input_data,
            "output": f"Processed by {self.config.name}",
            "status": "success"
        }
    
    def add_tool(self, tool_name: str, tool_func: callable) -> None:
        """Add a tool to the agent."""
        self.tools.append({"name": tool_name, "function": tool_func})
    
    def get_memory(self, key: str) -> Optional[Any]:
        """Retrieve data from agent memory."""
        return self.memory.get(key)
    
    def set_memory(self, key: str, value: Any) -> None:
        """Store data in agent memory."""
        self.memory[key] = value


def create_agent(name: str, description: str, **kwargs) -> PurpleCrayonAgent:
    """Create a new PurpleCrayon agent with the given configuration."""
    config = AgentConfig(name=name, description=description, **kwargs)
    return PurpleCrayonAgent(config)


async def run_agent_async(agent: PurpleCrayonAgent, input_data: str) -> Dict[str, Any]:
    """Run an agent asynchronously."""
    return await agent.process(input_data)


def run_agent_sync(agent: PurpleCrayonAgent, input_data: str) -> Dict[str, Any]:
    """Run an agent synchronously."""
    return asyncio.run(agent.process(input_data))