"""
Ad Matcher Module

This module matches user queries with relevant ads using semantic understanding
and keyword matching. It works with the QueryAnalyzer and AdRepository to find
the most relevant ads for a given user context.
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .ad_repository import AdRepository
from .query_analyzer import QueryAnalyzer

logger = logging.getLogger(__name__)

class AdMatcher:
    def __init__(self, config_path: str = None):
        """
        Initialize the AdMatcher with configuration settings
        
        Args:
            config_path: Optional path to config file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "service_config.json"
            
        self.config = self._load_config(config_path)
        self.relevance_threshold = self.config["ad_matcher"]["relevance_threshold"]
        self.max_ads_per_request = self.config["ad_matcher"].get("max_ads_per_request", 3)
        self.context_window_size = self.config["ad_matcher"].get("context_window_size", 10)
        
        # Initialize components
        self.ad_repository = AdRepository()
        self.query_analyzer = QueryAnalyzer()
        
        # Track processed conversations to avoid showing the same ad repeatedly
        self.conversation_ad_history = {}
        
        logger.info(f"Ad matcher initialized with relevance threshold: {self.relevance_threshold}")

    def _load_config(self, config_path) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path) as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.warning(f"Error loading config: {e}. Using default values.")
            return {
                "ad_matcher": {
                    "relevance_threshold": 0.7,
                    "max_ads_per_request": 3,
                    "context_window_size": 10
                }
            }

    def match_ads(self, conversation_history: List[Dict[str, str]], user_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Match the most relevant ads based on conversation history and user information.
        
        Args:
            conversation_history: List of conversation messages (each with 'role' and 'content')
            user_info: Optional user information for targeting
            
        Returns:
            List of matched ads with relevance scores
        """
        start_time = time.time()
        
        try:
            # Generate a conversation ID if not already tracked
            conversation_id = self._get_conversation_id(conversation_history)
            
            # Extract recent messages for context window
            recent_messages = conversation_history[-self.context_window_size:]
            
            # Analyze the conversation to extract topics, entities, and intent
            analysis = self.query_analyzer.analyze_conversation(recent_messages)
            
            # Get all active ads
            active_ads = self.ad_repository.get_active_ads()
            if not active_ads:
                logger.warning("No active ads available to match")
                return []
            
            # Match ads based on the analysis
            matched_ads = []
            for ad in active_ads:
                relevance_score = self._calculate_relevance(ad, analysis)
                
                # Only consider ads that meet the relevance threshold
                if relevance_score >= self.relevance_threshold:
                    # Apply frequency capping
                    if self._allow_ad_impression(conversation_id, ad["id"]):
                        matched_ads.append({
                            "ad": ad,
                            "relevance_score": relevance_score,
                            "match_factors": self._get_match_factors(ad, analysis)
                        })
            
            # Sort matched ads by relevance score (highest first)
            matched_ads.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Limit the number of ads returned
            matched_ads = matched_ads[:self.max_ads_per_request]
            
            processing_time = (time.time() - start_time) * 1000  # ms
            logger.debug(f"Matched {len(matched_ads)} ads in {processing_time:.2f}ms")
            
            return matched_ads
        
        except Exception as e:
            logger.error(f"Error matching ads: {e}", exc_info=True)
            return []

    def _calculate_relevance(self, ad: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """
        Calculate relevance score based on multiple factors
        
        Args:
            ad: Ad data to evaluate
            analysis: Analysis of the conversation
            
        Returns:
            Relevance score between 0 and 1
        """
        # Get ad keywords and categories
        ad_keywords = [k.lower() for k in ad.get("keywords", [])]
        ad_categories = [c.lower() for c in ad.get("categories", [])]
        
        # Get conversation tokens and entities
        tokens = analysis.get("tokens", [])
        entities = analysis.get("entities", [])
        topics = analysis.get("topics", [])
        
        # Calculate keyword match score
        token_matches = sum(1 for token in tokens if token.lower() in ad_keywords)
        entity_matches = sum(1 for entity in entities if entity.lower() in ad_keywords)
        total_matches = token_matches + entity_matches
        
        # Normalize score based on the number of keywords
        max_keywords = max(1, min(len(ad_keywords), 10))  # Cap at 10 to avoid over-weighting
        keyword_score = min(1.0, total_matches / max_keywords)
        
        # Calculate category match score
        category_matches = sum(1 for topic in topics if topic.lower() in ad_categories)
        max_categories = max(1, min(len(ad_categories), 5))  # Cap at 5
        category_score = min(1.0, category_matches / max_categories)
        
        # Get semantic score if available
        # Get the ad ID, supporting both 'id' and 'ad_id' field names
        ad_id = ad.get("id", ad.get("ad_id", "unknown"))
        semantic_score = analysis.get("semantic_score", {}).get(ad_id, 0.0)
        
        # Check for negative keywords
        negative_keywords = ad.get("negative_keywords", [])
        negative_keyword_score = 1.0  # Default multiplier
        relevant_terms = tokens + entities
        
        for neg_keyword in negative_keywords:
            if any(neg_keyword in term.lower() for term in relevant_terms):
                negative_keyword_score = 0.0
                break
        
        # Calculate combined score with weights
        keyword_weight = 0.4
        category_weight = 0.3
        semantic_weight = 0.3
        
        combined_score = (
            keyword_weight * keyword_score +
            category_weight * category_score +
            semantic_weight * semantic_score
        ) * negative_keyword_score
        
        return combined_score

    def _get_match_factors(self, ad: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed information on why the ad matched
        
        Args:
            ad: Ad data
            analysis: Analysis of the conversation
            
        Returns:
            Dictionary of match factors
        """
        match_factors = {
            "matched_keywords": [],
            "matched_categories": [],
            "matched_topics": []
        }
        
        # Find matched keywords
        ad_keywords = [k.lower() for k in ad.get("keywords", [])]
        tokens = analysis.get("tokens", [])
        entities = analysis.get("entities", [])
        
        for keyword in ad_keywords:
            for token in tokens:
                if keyword in token.lower():
                    match_factors["matched_keywords"].append(keyword)
                    break
            
            for entity in entities:
                if keyword in entity.lower():
                    match_factors["matched_keywords"].append(keyword)
                    break
        
        # Find matched categories
        ad_categories = set(ad.get("categories", []))
        context_categories = set(analysis.get("categories", []))
        match_factors["matched_categories"] = list(ad_categories.intersection(context_categories))
        
        # Find matched topics
        topics = analysis.get("topics", [])
        for topic in topics:
            for keyword in ad_keywords:
                if keyword in topic.lower():
                    match_factors["matched_topics"].append(topic)
                    break
        
        # Remove duplicates
        match_factors["matched_keywords"] = list(set(match_factors["matched_keywords"]))
        match_factors["matched_topics"] = list(set(match_factors["matched_topics"]))
        
        return match_factors

    def _get_conversation_id(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Generate a unique ID for the conversation
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            Conversation ID
        """
        # Use the first message as a seed for the conversation ID
        if conversation_history and 'content' in conversation_history[0]:
            first_msg = conversation_history[0]['content'][:50]  # First 50 chars of first message
            conversation_id = str(hash(first_msg))
            
            # Initialize ad history for this conversation if not already tracking
            if conversation_id not in self.conversation_ad_history:
                self.conversation_ad_history[conversation_id] = {
                    "last_message_count": len(conversation_history),
                    "shown_ads": {}  # Ad ID -> count
                }
            
            return conversation_id
        
        return "unknown_conversation"

    def _allow_ad_impression(self, conversation_id: str, ad_id: str) -> bool:
        """
        Check if an ad should be shown based on frequency capping
        
        Args:
            conversation_id: ID of the conversation
            ad_id: ID of the ad
            
        Returns:
            True if the ad is allowed to be shown
        """
        if conversation_id not in self.conversation_ad_history:
            return True
        
        # Get history for this conversation
        history = self.conversation_ad_history[conversation_id]
        
        # Get count of times this ad has been shown
        shown_count = history["shown_ads"].get(ad_id, 0)
        
        # Don't show the same ad more than 3 times in a conversation
        max_impressions = 3
        
        # Don't show the same ad in consecutive matches
        last_shown_ad = history.get("last_shown_ad")
        
        # Allow if under frequency cap and not the last ad shown
        if shown_count < max_impressions and last_shown_ad != ad_id:
            # Update frequency counter
            history["shown_ads"][ad_id] = shown_count + 1
            history["last_shown_ad"] = ad_id
            return True
        
        return False

    def get_ad_for_display(self, matched_ad: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an ad for display to the user
        
        Args:
            matched_ad: Ad data with relevance score
            
        Returns:
            Formatted ad for display
        """
        ad = matched_ad["ad"]
        display_ad = {
            "id": ad["id"],
            "title": ad["title"],
            "description": ad["description"],
            "call_to_action": ad["call_to_action"],
            "url": ad["url"],
            "display_format": ad.get("display_format", "text"),
            "sponsored": True,
            "relevance_score": matched_ad["relevance_score"]
        }
        
        return display_ad


# If the module is run directly, test it
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Test the ad matcher
    matcher = AdMatcher()
    
    # Sample conversation
    conversation = [
        {"role": "user", "content": "I need new running shoes for my marathon training."},
        {"role": "assistant", "content": "What kind of running do you do and what's your budget?"},
        {"role": "user", "content": "I run about 40 miles per week and need good cushioning. Budget around $150."}
    ]
    
    # Match ads
    matches = matcher.match_ads(conversation)
    
    # Print matches
    print(f"Found {len(matches)} matching ads:")
    for match in matches:
        ad = match["ad"]
        print(f"- {ad['title']} (Score: {match['relevance_score']:.2f})")
        print(f"  {ad['description']}")
        print(f"  Match factors: {match['match_factors']}")
        print()
