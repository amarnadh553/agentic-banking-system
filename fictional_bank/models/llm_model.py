
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

# # load_dotenv()
# # PROJECT_ROOT = os.getcwd()+os.sep+'fictional_bank'+os.sep+'.env'
# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# PROJECT_ROOT / "fictional_bank"/'.env'
# load_dotenv(PROJECT_ROOT, override=True)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "fictional_bank" / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)

print(f"ENV file exists: {ENV_FILE.exists()}")
print(f"LLM model: {os.getenv('LLM_MODEL_NAME')}")



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
    ):
        self.logger = logger or logging.getLogger(__name__)

        if not llm_model_name or not llm_model_name.strip():
            raise ValueError("llm_model_name must be a non-empty string.")

        self.llm_model_name = llm_model_name
        self.open_ai_api_key = open_ai_api_key

        self.temperature = 0.0 if temperature is None else temperature
        self.top_p = 1.0 if top_p is None else top_p
        self.frequency_penalty = frequency_penalty

        self.llm_model: Optional[ChatOpenAI] = None

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

            self.llm_model = ChatOpenAI(**model_kwargs)
            self.logger.info("Successfully initialized LLM model: %s", self.llm_model_name)
            return self.llm_model
        except Exception:
            self.logger.exception("Failed to initialize LLM model.")
            raise


# llm_initializer = LLMModelInitializer(
#         llm_model_name=os.getenv("MODEL_NAME", "gpt-4.1-mini"),
#         open_ai_api_key=os.getenv("OPENAI_API_KEY", ""),
#         temperature=0.0,
#         top_p=1.0,
#     )

# llm = llm_initializer.initialise_llm_model()
