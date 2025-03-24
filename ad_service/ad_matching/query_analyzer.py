"""
Query Analyzer Module

This module analyzes user queries to extract intent, keywords, and context
for more accurate ad matching.
"""

import logging
import json
import time
from typing import Dict, List, Any, Tuple
import re
import httpx  # Add httpx import
from openai import OpenAI  # Updated import for OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyzes user queries to extract relevant information for ad matching
    """
    
    def __init__(self, config_path: str = "../config/service_config.json"):
        """
        Initialize the query analyzer
        
        Args:
            config_path: Path to the service configuration file
        """
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create default config if file doesn't exist or is invalid
            self.config = {}
        
        # Initialize OpenAI configuration, prioritizing environment variables
        self.openai_config = {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "default_model": os.getenv("OPENAI_CHAT_MODEL", "gpt-3.5-turbo"),
            "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        }
        
        # Fall back to config file values if env vars not set
        if not self.openai_config["api_key"] and "openai" in self.config:
            self.openai_config.update(self.config.get("openai", {}))
        
        self.api_key = self.openai_config["api_key"]
        self.default_model = self.openai_config["default_model"]
        self.embedding_model = self.openai_config["embedding_model"]
        
        # Create a custom httpx client without proxy configuration
        http_client = httpx.Client(
            transport=httpx.HTTPTransport(local_address="0.0.0.0")
        )
        
        # Set up OpenAI client with the custom HTTP client
        # This avoids the proxies parameter error
        self.client = OpenAI(
            api_key=self.api_key,
            http_client=http_client
        )
        
        logger.info("Query analyzer initialized")

    def analyze_conversation(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze an entire conversation to extract topics, entities, and context
        for ad matching.
        
        Args:
            conversation_history: List of messages in the conversation
            
        Returns:
            Dict with extracted information about the conversation
        """
        start_time = time.time()
        
        if not conversation_history:
            return {
                "tokens": [],
                "entities": [],
                "topics": [],
                "categories": [],
                "semantic_score": {},
                "commercial_intent": False,
                "processing_time_ms": 0
            }
        
        # Extract the latest user message
        latest_user_message = ""
        for msg in reversed(conversation_history):
            if msg.get("role") == "user" and msg.get("content"):
                latest_user_message = msg["content"]
                break
        
        # If no user message found, use the last message
        if not latest_user_message and conversation_history[-1].get("content"):
            latest_user_message = conversation_history[-1]["content"]
        
        # Create a context summary from the entire conversation
        context_summary = self._get_conversation_summary(conversation_history)
        
        # Extract entities, topics, and keywords using NLP
        extracted_data = self._extract_data_with_openai(latest_user_message, conversation_history)
        
        # Get additional context from the conversation history
        context_keywords = self._extract_context_keywords(conversation_history)
        
        # Combine extracted keywords with context keywords
        all_keywords = list(set(extracted_data["keywords"] + context_keywords))
        
        # Create embeddings for semantic matching (if needed)
        conversation_text = " ".join([msg.get("content", "") for msg in conversation_history if msg.get("content")])
        conversation_embedding = self._create_embedding(conversation_text) if conversation_text else []
        
        # Put everything together
        analysis_result = {
            "tokens": all_keywords,
            "entities": extracted_data["entities"],
            "topics": extracted_data.get("topics", []),
            "categories": extracted_data["categories"],
            "semantic_score": {},  # This would be populated when comparing to ads
            "commercial_intent": extracted_data["is_commercial_intent"],
            "context_summary": context_summary,
            "sentiment": extracted_data["sentiment"],
            "intent": extracted_data["intent"],
            "conversation_embedding": conversation_embedding,
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
        logger.debug(f"Analyzed conversation with {len(conversation_history)} messages")
        return analysis_result
    
    def analyze_query(self, query_text: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Analyze a user query to extract intent, keywords, and context
        
        Args:
            query_text: The text of the user's query
            conversation_history: Previous messages in the conversation
            
        Returns:
            Dict with extracted information about the query
        """
        start_time = time.time()
        
        if conversation_history is None:
            conversation_history = []
        
        # Create embedding for semantic matching
        query_embedding = self._create_embedding(query_text)
        
        # Extract keywords and intent using OpenAI
        extracted_data = self._extract_data_with_openai(query_text, conversation_history)
        
        # Combine the results
        analysis_result = {
            "query_text": query_text,
            "query_embedding": query_embedding,
            "detected_keywords": extracted_data["keywords"],
            "query_intent": extracted_data["intent"],
            "categories": extracted_data["categories"],
            "entities": extracted_data["entities"],
            "sentiment": extracted_data["sentiment"],
            "is_commercial_intent": extracted_data["is_commercial_intent"],
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
        logger.debug(f"Analyzed query: {query_text}")
        return analysis_result
    
    def _create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding vector for the text using OpenAI's API
        
        Args:
            text: Text to create embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            
            # Extract the embedding vector
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            # Return empty embedding as fallback
            return []
    
    def _extract_data_with_openai(self, query_text: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Use OpenAI's API to extract keywords, intent, and other information
        
        Args:
            query_text: User query text
            conversation_history: Previous messages in the conversation
            
        Returns:
            Dict with extracted information
        """
        try:
            # Create a context-aware prompt
            system_prompt = """
            Analyze the user query and extract the following information:
            1. Keywords: Extract 3-7 relevant keywords for ad matching
            2. Intent: Categorize the primary intent (informational, transactional, navigational)
            3. Categories: List 1-3 relevant product/service categories 
            4. Entities: Extract named entities (products, brands, locations)
            5. Sentiment: Determine sentiment (positive, negative, neutral)
            6. Commercial Intent: Is the user likely to be interested in purchasing something? (true/false)
            7. Topics: Identify 1-3 main topics being discussed
            
            Format your response as a valid JSON object with these keys.
            """
            
            # Prepare conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (limited to last 5 messages)
            if conversation_history:
                for msg in conversation_history[-5:]:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        messages.append(msg)
            
            # Add the current query if not already included
            if not any(msg.get("role") == "user" and msg.get("content") == query_text for msg in messages):
                messages.append({"role": "user", "content": query_text})
            
            # Call OpenAI API with updated client
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more deterministic output
                max_tokens=300,
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            # Extract the JSON part
            try:
                result_json = json.loads(result_text)
                
                # Ensure all expected keys are present
                default_keys = {
                    "keywords": [],
                    "intent": "unknown",
                    "categories": [],
                    "entities": [],
                    "sentiment": "neutral",
                    "is_commercial_intent": False,
                    "topics": []
                }
                
                for key, default_value in default_keys.items():
                    if key not in result_json:
                        result_json[key] = default_value
                
                return result_json
                
            except json.JSONDecodeError:
                # If JSON parsing fails, extract data using a simpler approach
                logger.warning("Failed to parse OpenAI response as JSON. Using fallback extraction.")
                return self._fallback_extraction(result_text)
                
        except Exception as e:
            logger.error(f"Error extracting data with OpenAI: {e}")
            # Return empty results as fallback
            return {
                "keywords": [],
                "intent": "unknown",
                "categories": [],
                "entities": [],
                "sentiment": "neutral",
                "is_commercial_intent": False,
                "topics": []
            }
    
    def _get_conversation_summary(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Generate a summary of the conversation context
        
        Args:
            conversation_history: List of messages in the conversation
            
        Returns:
            String summary of the conversation
        """
        if not conversation_history:
            return ""
            
        try:
            # Create prompt for summarization
            system_prompt = """
            Summarize the key points of this conversation, focusing on:
            1. Main topics discussed
            2. User interests and needs
            3. Products or services mentioned
            4. Any purchase intent signals
            
            Keep the summary concise (50-100 words).
            """
            
            # Prepare conversation for the API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add up to last 10 messages from conversation
            for msg in conversation_history[-10:]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(msg)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                temperature=0.3,
                max_tokens=150
            )
            
            # Return the summary
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            # Fallback: Just concatenate last few messages
            return " ".join([msg.get("content", "") for msg in conversation_history[-3:] if msg.get("content")])
    
    def _extract_context_keywords(self, conversation_history: List[Dict[str, str]]) -> List[str]:
        """
        Extract additional keywords from conversation context
        
        Args:
            conversation_history: List of messages in the conversation
            
        Returns:
            List of keywords extracted from context
        """
        # Simple keyword extraction using regex patterns
        keywords = []
        
        # Join last 5 messages
        conversation_text = " ".join([
            msg.get("content", "") 
            for msg in conversation_history[-5:] 
            if msg.get("content")
        ])
        
        # Extract potential keywords (nouns, product names, etc.)
        # This is a simple approach - in production would use NLP
        word_pattern = r'\b[A-Za-z][A-Za-z0-9]{2,}\b'
        words = re.findall(word_pattern, conversation_text)
        
        # Filter out common words, keep potential keywords
        stopwords = {"the", "and", "for", "with", "that", "have", "this", "from", "they", "would", "what"}
        keywords = [word.lower() for word in words if word.lower() not in stopwords]
        
        # Remove duplicates and limit to top 10
        unique_keywords = list(set(keywords))
        return unique_keywords[:10]
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """
        Fallback method to extract information when JSON parsing fails
        
        Args:
            text: Raw text from OpenAI response
            
        Returns:
            Dict with extracted information
        """
        # Simple extraction based on keywords in the response
        result = {
            "keywords": [],
            "intent": "unknown",
            "categories": [],
            "entities": [],
            "sentiment": "neutral",
            "is_commercial_intent": False,
            "topics": []
        }
        
        # Extract keywords
        if "Keywords:" in text:
            keywords_section = text.split("Keywords:")[1].split("\n")[0]
            result["keywords"] = [k.strip() for k in keywords_section.split(",")]
        
        # Extract intent
        if "Intent:" in text:
            intent_section = text.split("Intent:")[1].split("\n")[0].strip().lower()
            if "informational" in intent_section:
                result["intent"] = "informational"
            elif "transactional" in intent_section:
                result["intent"] = "transactional"
            elif "navigational" in intent_section:
                result["intent"] = "navigational"
        
        # Extract commercial intent
        if "Commercial Intent:" in text:
            commercial_section = text.split("Commercial Intent:")[1].split("\n")[0].strip().lower()
            result["is_commercial_intent"] = "true" in commercial_section or "yes" in commercial_section
        
        # Extract sentiment
        if "Sentiment:" in text:
            sentiment_section = text.split("Sentiment:")[1].split("\n")[0].strip().lower()
            if "positive" in sentiment_section:
                result["sentiment"] = "positive"
            elif "negative" in sentiment_section:
                result["sentiment"] = "negative"
            else:
                result["sentiment"] = "neutral"
        
        # Extract topics
        if "Topics:" in text:
            topics_section = text.split("Topics:")[1].split("\n")[0].strip()
            result["topics"] = [t.strip() for t in topics_section.split(",")]
        
        return result


# If the module is run directly, test it
if __name__ == "__main__":
    # Test the query analyzer with a sample query
    analyzer = QueryAnalyzer()
    result = analyzer.analyze_query("What's the best plywood for building a bookshelf?")
    print(json.dumps(result, indent=2)) 
