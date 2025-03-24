import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables once at module level
load_dotenv(verbose=True)

def get_openai_client():
    """Creates and returns an OpenAI client using the API key from environment variables"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        raise ValueError(
            "OPENAI_API_KEY not found. Please ensure:\n"
            "1. Your .env file exists in the project root\n"
            "2. The file contains: OPENAI_API_KEY=your-key-here"
        )
    
    return OpenAI(api_key=api_key)

# Create a singleton instance
_client = None

def get_client():
    """
    Returns a singleton instance of the OpenAI client
    """
    global _client
    if _client is None:
        _client = get_openai_client()
    return _client

class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    async def analyze_query(self, query: str, context: List[Dict] = None) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "Analyze the user query for intent and context."},
            {"role": "user", "content": query}
        ]
        if context:
            messages.extend(context)
            
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        return response.choices[0].message.content

    async def check_content_safety(self, text: str) -> bool:
        response = await self.client.moderations.create(input=text)
        return not response.results[0].flagged
