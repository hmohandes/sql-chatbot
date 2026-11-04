import ollama
from config import settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self):
        self.model = settings.ollama_model
        self.host = settings.ollama_host

    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Send a chat request to Ollama.
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
        Returns:
            Response from Ollama
        """
        try:
            logger.info(f"Sending chat request to Ollama model: {self.model}")

            kwargs = {
                "model": self.model,
                "messages": messages,
            }

            if tools:
                kwargs["tools"] = tools

            response = ollama.chat(**kwargs)

            logger.info(f"Received response from Ollama")
            return response

        except Exception as e:
            logger.error(f"Error communicating with Ollama: {e}")
            raise

    def generate(self, prompt: str) -> str:
        """
        Generate a response from a simple prompt.
        Args:
            prompt: The prompt string
        Returns:
            Generated text response
        """
        try:
            logger.info(f"Sending generate request to Ollama model: {self.model}")

            response = ollama.generate(
                model=self.model,
                prompt=prompt
            )

            logger.info(f"Received generate response from Ollama")
            return response.get("response", "")

        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            raise


# Global Ollama client instance
ollama_client = OllamaClient()
