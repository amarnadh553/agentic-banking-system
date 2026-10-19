import os
from dataclasses import dataclass, field
from typing import Dict, List, Union, Any

from dotenv import load_dotenv

load_dotenv()

def get_env_var(var_name:str, default_value: Any = "", required: bool = True) -> Any:
    """
    Retrieve an environment variable with optional requirement.

    Args:
        var_name (str): Name of the environment variable
        required (bool, optional): Whether the variable is required. Defaults to True.

    Returns:
        str: Value of the environment variable

    Raises:
        ValueError: If the variable is required but not set
    """

    value = os.getenv(var_name, default_value)
    if not value and required:
        raise ValueError(f"Required environment variable '{var_name}' is not set. Please make sure to export it.")
    if not value:
        print(f"Warning: Environment variable '{var_name}' is not set. Using default value: {default_value}")
    return value or ""

@dataclass
class Config:

    """Configuration class to store all environment variables and constants"""

    LLM_MODEL_NAME : str = field(default_factory = lambda : get_env_var("LLM_MODEL_NAME", required=True))
    OPENAI_API_KEY : str = field(default_factory = lambda : get_env_var("OPENAI_API_KEY", required=True))
    MAX_ITERATIONS : int = field(default_factory = lambda : int(get_env_var("MAX_ITERATIONS", default_value="5", required=False)))
    TEMPERATURE : float = field(default_factory = lambda : float(get_env_var("TEMPERATURE", default_value="0.0", required=False)))
    TOP_P : float = field(default_factory = lambda : float(get_env_var("TOP_P", default_value="0.0", required=False)))
    FREQUENCY_PENALTY : float = field(default_factory = lambda : float(get_env_var("FREQUENCY_PENALTY", default_value="0.0", required=False)))

# config = Config()
