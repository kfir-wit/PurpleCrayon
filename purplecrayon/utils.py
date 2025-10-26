"""
Utility functions for PurpleCrayon.

This module contains helper functions and utilities used throughout the package.
"""

import json
import logging
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
import yaml


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration for PurpleCrayon.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a JSON or YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)


def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """
    Save configuration to a JSON or YAML file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the configuration
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            yaml.dump(config, f, default_flow_style=False)
        else:
            json.dump(config, f, indent=2)


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields are present in a dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValueError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a nested dictionary using dot notation.
    
    Args:
        data: Dictionary to search in
        key: Dot-separated key path (e.g., 'user.profile.name')
        default: Default value if key is not found
        
    Returns:
        Value at the key path or default value
    """
    keys = key.split('.')
    current = data
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def run_concurrent(tasks: List[Callable], max_concurrent: int = 5) -> List[Any]:
    """
    Run multiple async tasks concurrently with a limit.
    
    Args:
        tasks: List of async callables to execute
        max_concurrent: Maximum number of concurrent tasks
        
    Returns:
        List of results from all tasks
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_with_semaphore(task):
        async with semaphore:
            if asyncio.iscoroutinefunction(task):
                return await task()
            else:
                return task()
    
    return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])


def format_prompt(template: str, **kwargs) -> str:
    """
    Format a prompt template with provided variables.
    
    Args:
        template: Prompt template string with {variable} placeholders
        **kwargs: Variables to substitute in the template
        
    Returns:
        Formatted prompt string
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required variable in prompt template: {e}")


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON data from text that may contain other content.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Parsed JSON dictionary or None if no valid JSON found
    """
    import re
    
    # Look for JSON-like patterns in the text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    return None


def create_agent_workflow(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a workflow definition for LangGraph-style agent execution.
    
    Args:
        steps: List of step definitions with 'name', 'function', and 'next' keys
        
    Returns:
        Workflow definition dictionary
    """
    workflow = {
        "nodes": {},
        "edges": [],
        "entry_point": steps[0]["name"] if steps else None
    }
    
    for step in steps:
        workflow["nodes"][step["name"]] = {
            "function": step["function"],
            "description": step.get("description", "")
        }
        
        if "next" in step:
            workflow["edges"].append({
                "from": step["name"],
                "to": step["next"]
            })
    
    return workflow