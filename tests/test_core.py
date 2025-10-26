"""
Unit tests for PurpleCrayon core functionality.

This module contains tests for the core.py module.
"""

import pytest
import asyncio
from purplecrayon.core import AgentConfig, PurpleCrayonAgent, create_agent, run_agent_async, run_agent_sync


class TestAgentConfig:
    """Test cases for AgentConfig dataclass."""
    
    def test_agent_config_creation(self):
        """Test creating an AgentConfig with required fields."""
        config = AgentConfig(
            name="test_agent",
            description="A test agent"
        )
        
        assert config.name == "test_agent"
        assert config.description == "A test agent"
        assert config.model == "gpt-4"  # default value
        assert config.temperature == 0.7  # default value
        assert config.tools == []  # default empty list
    
    def test_agent_config_with_custom_values(self):
        """Test creating an AgentConfig with custom values."""
        config = AgentConfig(
            name="custom_agent",
            description="A custom agent",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=2000,
            tools=["tool1", "tool2"]
        )
        
        assert config.name == "custom_agent"
        assert config.description == "A custom agent"
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.tools == ["tool1", "tool2"]


class TestPurpleCrayonAgent:
    """Test cases for PurpleCrayonAgent class."""
    
    def test_agent_creation(self):
        """Test creating a PurpleCrayonAgent."""
        config = AgentConfig(name="test", description="test agent")
        agent = PurpleCrayonAgent(config)
        
        assert agent.config == config
        assert agent.tools == []
        assert agent.memory == {}
    
    def test_add_tool(self):
        """Test adding a tool to an agent."""
        config = AgentConfig(name="test", description="test agent")
        agent = PurpleCrayonAgent(config)
        
        def test_tool():
            return "test result"
        
        agent.add_tool("test_tool", test_tool)
        
        assert len(agent.tools) == 1
        assert agent.tools[0]["name"] == "test_tool"
        assert agent.tools[0]["function"] == test_tool
    
    def test_memory_operations(self):
        """Test memory get/set operations."""
        config = AgentConfig(name="test", description="test agent")
        agent = PurpleCrayonAgent(config)
        
        # Test setting memory
        agent.set_memory("key1", "value1")
        assert agent.get_memory("key1") == "value1"
        
        # Test getting non-existent key
        assert agent.get_memory("nonexistent") is None
        
        # Test setting multiple values
        agent.set_memory("key2", {"nested": "data"})
        assert agent.get_memory("key2") == {"nested": "data"}
    
    @pytest.mark.asyncio
    async def test_process_async(self):
        """Test async processing."""
        config = AgentConfig(name="test", description="test agent")
        agent = PurpleCrayonAgent(config)
        
        result = await agent.process("test input")
        
        assert result["input"] == "test input"
        assert result["output"] == "Processed by test"
        assert result["status"] == "success"


class TestHelperFunctions:
    """Test cases for helper functions."""
    
    def test_create_agent(self):
        """Test create_agent helper function."""
        agent = create_agent("helper_agent", "A helper agent", model="gpt-3.5-turbo")
        
        assert isinstance(agent, PurpleCrayonAgent)
        assert agent.config.name == "helper_agent"
        assert agent.config.description == "A helper agent"
        assert agent.config.model == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_run_agent_async(self):
        """Test run_agent_async helper function."""
        config = AgentConfig(name="async_test", description="async test agent")
        agent = PurpleCrayonAgent(config)
        
        result = await run_agent_async(agent, "async input")
        
        assert result["input"] == "async input"
        assert result["output"] == "Processed by async_test"
        assert result["status"] == "success"
    
    def test_run_agent_sync(self):
        """Test run_agent_sync helper function."""
        config = AgentConfig(name="sync_test", description="sync test agent")
        agent = PurpleCrayonAgent(config)
        
        result = run_agent_sync(agent, "sync input")
        
        assert result["input"] == "sync input"
        assert result["output"] == "Processed by sync_test"
        assert result["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__])