from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from config import settings
from typing import List, Dict, Any, Optional
import logging
import torch

logger = logging.getLogger(__name__)


class TransformersClient:
    def __init__(self):
        self.model_name = settings.llm_model
        self.device = settings.llm_device
        self.max_length = settings.llm_max_length
        self.temperature = settings.llm_temperature

        self.tokenizer = None
        self.model = None
        self.generator = None
        self._initialized = False

    def initialize(self):
        """Initialize the model and tokenizer"""
        if self._initialized:
            return

        try:
            logger.info(f"Loading model: {self.model_name}")
            logger.info(f"Device: {self.device}")

            # Load tokenizer with explicit handling for special tokens
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    trust_remote_code=False
                )
            except Exception as e:
                logger.warning(f"Failed to load tokenizer without trust_remote_code, trying with it: {e}")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    trust_remote_code=True
                )

            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Determine device
            if self.device == "auto":
                device = 0 if torch.cuda.is_available() else -1
            elif self.device == "cuda":
                device = 0 if torch.cuda.is_available() else -1
            else:
                device = -1

            # Create generation pipeline directly (simpler approach)
            self.generator = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.tokenizer,
                device=device,
                torch_dtype=torch.float16 if device >= 0 else torch.float32,
                model_kwargs={"device_map": "auto" if self.device == "auto" else None}
            )

            self._initialized = True
            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Send a chat request to the model.
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool definitions (not used with this implementation)
        Returns:
            Response from the model
        """
        if not self._initialized:
            self.initialize()

        try:
            logger.info(f"Processing chat request with {len(messages)} messages")

            # Build conversation prompt
            conversation = self._build_conversation(messages)
            logger.debug(f"Conversation prompt length: {len(conversation)}")

            # Generate response
            outputs = self.generator(
                conversation,
                max_new_tokens=512,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                return_full_text=False
            )

            # Extract generated text (handle different output formats)
            generated_text = ""
            if isinstance(outputs, list):
                if len(outputs) > 0:
                    if isinstance(outputs[0], dict):
                        generated_text = outputs[0].get("generated_text", "")
                    elif isinstance(outputs[0], str):
                        generated_text = outputs[0]
            elif isinstance(outputs, dict):
                generated_text = outputs.get("generated_text", "")
            elif isinstance(outputs, str):
                generated_text = outputs

            logger.info(f"Generated response length: {len(generated_text)}")

            # Return in expected format
            return {
                "message": {
                    "role": "assistant",
                    "content": generated_text
                }
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def generate(self, prompt: str) -> str:
        """
        Generate a response from a simple prompt.
        Args:
            prompt: The prompt string
        Returns:
            Generated text response
        """
        if not self._initialized:
            self.initialize()

        try:
            logger.info(f"Generating response for prompt length: {len(prompt)}")

            outputs = self.generator(
                prompt,
                max_new_tokens=512,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                return_full_text=False
            )

            # Extract generated text (handle different output formats)
            generated_text = ""
            if isinstance(outputs, list):
                if len(outputs) > 0:
                    if isinstance(outputs[0], dict):
                        generated_text = outputs[0].get("generated_text", "")
                    elif isinstance(outputs[0], str):
                        generated_text = outputs[0]
            elif isinstance(outputs, dict):
                generated_text = outputs.get("generated_text", "")
            elif isinstance(outputs, str):
                generated_text = outputs

            logger.info(f"Generated response length: {len(generated_text)}")
            return generated_text

        except Exception as e:
            logger.error(f"Error in generate: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _build_conversation(self, messages: List[Dict[str, str]]) -> str:
        """
        Build a conversation string from messages.
        Args:
            messages: List of message dictionaries
        Returns:
            Formatted conversation string
        """
        conversation = ""

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                conversation += f"System: {content}\n\n"
            elif role == "user":
                conversation += f"User: {content}\n\n"
            elif role == "assistant":
                conversation += f"Assistant: {content}\n\n"
            elif role == "tool":
                conversation += f"Tool Result: {content}\n\n"

        conversation += "Assistant:"
        return conversation


# Global LLM client instance
llm_client = TransformersClient()
