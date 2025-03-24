"""
Handles user session management and state persistence
"""
import uuid
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
import logging
from ad_service.core.ad_service import AdService

logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    user_id: str
    start_time: datetime
    messages: List[Dict]
    interaction_count: int = 0

class SessionManager:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.ad_service = AdService()  # Use AdService instead of direct OpenAI client
        self.current_session = None
        self.metrics_collector = None

    def initialize_session(self) -> None:
        self.current_session = {
            "messages": [],
            "interaction_count": 0
        }
    
    def add_message(self, role: str, content: str, ad: str = None) -> None:
        if not self.current_session:
            self.initialize_session()
        
        message = {"role": role, "content": content}
        if ad:
            message["ad"] = ad
            
        self.current_session.messages.append(message)
        self.current_session.interaction_count += 1
    
    def clear_session(self) -> None:
        if self.current_session:
            self.current_session.messages = []
            self.current_session.interaction_count = 0

    def process_chat_message(self, message: str) -> str:
        if not self.current_session:
            self.initialize_session()
            
        try:
            # Use AdService to get response with matched ads
            response = self.ad_service.process_query(message)
            
            # Store messages in session
            self.current_session["messages"].append({"role": "user", "content": message})
            self.current_session["messages"].append({"role": "assistant", "content": response})
            self.current_session["interaction_count"] += 1
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            raise
