import os
import logging
from typing import Optional
import traceback
from pathlib import Path

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from fictional_bank.src.logutils import Logger
from functools import lru_cache


logger = Logger().get_logger()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "fictional_bank" / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)

print(f"ENV file exists: {ENV_FILE.exists()}")
print(f"LLM model: {os.getenv('LLM_MODEL_NAME')}")

# How much a gpt-5 model "thinks" before it answers. Lower = faster and cheaper.
VALID_REASONING_EFFORTS = {"minimal", "low", "medium", "high"}


def initialize_llm():
    llm = ChatOpenAI(model=os.getenv("LLM_MODEL_NAME"))
    return llm

class LLMModelInitializer:
    def __init__(
        self,
        llm_model_name: str,
        open_ai_api_key: str,
        temperature: Optional[float] = 0.0,
        top_p: Optional[float] = 0.0,
        frequency_penalty: float = 0.0,
        logger: Optional[logging.Logger] = None,
        reasoning_effort: Optional[str] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)

        if not llm_model_name or not llm_model_name.strip():
            raise ValueError("llm_model_name must be a non-empty string.")

        self.llm_model_name = llm_model_name
        self.open_ai_api_key = open_ai_api_key

        self.temperature = 0.0 if temperature is None else temperature
        self.top_p = 1.0 if top_p is None else top_p
        self.frequency_penalty = frequency_penalty

        self.reasoning_effort = reasoning_effort

        self.llm_model: Optional[ChatOpenAI] = None

    @classmethod
    def from_config(cls, config, logger: Optional[logging.Logger] = None, **overrides) -> "LLMModelInitializer":
        """Build the initializer from the app Config. Pass keyword arguments to override one setting."""
        settings = {
            "llm_model_name": config.LLM_MODEL_NAME,
            "open_ai_api_key": config.OPENAI_API_KEY,
            "temperature": config.TEMPERATURE,
            "frequency_penalty": config.FREQUENCY_PENALTY,
            "reasoning_effort": config.REASONING_EFFORT,
            "logger": logger,
        }
        settings.update(overrides)
        return cls(**settings)

    @property
    def open_ai_api_key(self) -> str:
        return self.__open_ai_api_key

    @open_ai_api_key.setter
    def open_ai_api_key(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("API key must be a non-empty string.")

        self.__open_ai_api_key = value

    @property
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        if not isinstance(value, (int, float)) or not 0.0 <= value <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0.")

        self._temperature = float(value)

    @property
    def top_p(self) -> float:
        return self._top_p

    @top_p.setter
    def top_p(self, value: float) -> None:
        if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0.")

        self._top_p = float(value)

    def initialise_llm_model(self) -> ChatOpenAI:
        """Initialize the LLM once and return the model instance."""

        if self.llm_model is not None:
            return self.llm_model
        try:
            model_kwargs = {
                "model": self.llm_model_name,
                "api_key": self.open_ai_api_key,
                "temperature": self.temperature,
                # "top_p": self.top_p,
                "frequency_penalty": self.frequency_penalty,
                "max_retries": 2,
            }
            if self.reasoning_effort:
                model_kwargs["reasoning_effort"] = self.reasoning_effort

            self.llm_model = ChatOpenAI(**model_kwargs)
            self.logger.info(
                "Successfully initialized LLM model: %s (reasoning_effort=%s)",
                self.llm_model_name, self.reasoning_effort or "model default",
            )
            return self.llm_model
        except Exception:
            self.logger.exception("Failed to initialize LLM model.")
            raise


def create_llm(config, logger: Optional[logging.Logger] = None, **overrides) -> ChatOpenAI:
    """The one place that builds the chat model. Use it in the app, in the evaluation and anywhere else."""
    return LLMModelInitializer.from_config(config, logger, **overrides).initialise_llm_model()