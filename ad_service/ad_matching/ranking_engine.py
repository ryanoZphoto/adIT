"""
Ranking Engine Module

This module applies business rules to rank and select the best ads
after initial matching. It considers factors like bid amount, budget,
user targeting, and ad performance.
"""

import json
import logging
import time
import random
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RankingEngine:
    """
    Applies business rules to rank and select the best ads
    """
    
    def __init__(self, config_path: str = "../config/service_config.json"):
        """
        Initialize the ranking engine
        
        Args:
            config_path: Path to the service configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.ranking_config = self.config.get("ranking", {})
        
        # Default weights for ranking factors
        self.weights = {
            "relevance": 0.40,    # Weight for relevance score
            "bid": 0.35,          # Weight for bid amount
            "ctr": 0.15,          # Weight for historical CTR
            "budget": 0.05,       # Weight for remaining budget
            "targeting": 0.05     # Weight for targeting match
        }
        
        # Override with config values if present
        if "weights" in self.ranking_config:
            self.weights.update(self.ranking_config["weights"])
        
        logger.info("Ranking engine initialized")
    
    def rank_ads(self, matched_ads: List[Dict[str, Any]], user_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Rank matched ads based on business rules
        
        Args:
            matched_ads: List of ads with relevance scores
            user_context: Information about the user for targeting
            
        Returns:
            List of ranked ads with final scores
        """
        start_time = time.time()
        
        if not matched_ads:
            return []
        
        if user_context is None:
            user_context = {}
        
        # Apply ranking factors to each ad
        ranked_ads = []
        for match in matched_ads:
            ad = match["ad"]
            relevance_score = match["relevance_score"]
            
            # Calculate score for each ranking factor
            relevance_factor = relevance_score
            bid_factor = self._normalize_bid(ad.get("bid_amount", 0))
            ctr_factor = self._get_ctr_factor(ad)
            budget_factor = self._get_budget_factor(ad)
            targeting_factor = self._get_targeting_factor(ad, user_context)
            
            # Calculate combined score
            combined_score = (
                self.weights["relevance"] * relevance_factor +
                self.weights["bid"] * bid_factor +
                self.weights["ctr"] * ctr_factor +
                self.weights["budget"] * budget_factor +
                self.weights["targeting"] * targeting_factor
            )
            
            # Add a small random factor to prevent ties (0-1% of score)
            random_factor = random.uniform(0, 0.01) * combined_score
            final_score = combined_score + random_factor
            
            # Add to ranked ads
            ranked_ads.append({
                "ad": ad,
                "relevance_score": relevance_score,
                "final_score": final_score,
                "ranking_factors": {
                    "relevance": relevance_factor,
                    "bid": bid_factor,
                    "ctr": ctr_factor,
                    "budget": budget_factor,
                    "targeting": targeting_factor
                },
                "processing_time_ms": (time.time() - start_time) * 1000
            })
        
        # Sort ads by final score (highest first)
        ranked_ads.sort(key=lambda x: x["final_score"], reverse=True)
        
        logger.debug(f"Ranked {len(ranked_ads)} ads in {(time.time() - start_time) * 1000:.2f}ms")
        return ranked_ads
    
    def _normalize_bid(self, bid_amount: float) -> float:
        """
        Normalize the bid amount to a 0-1 scale
        
        Args:
            bid_amount: The bid amount in dollars
            
        Returns:
            Normalized bid factor (0-1)
        """
        # Get max bid from config or use default
        max_bid = self.ranking_config.get("max_bid", 5.0)
        
        # Normalize to 0-1 scale
        if max_bid <= 0:
            return 0.0
        
        return min(1.0, bid_amount / max_bid)
    
    def _get_ctr_factor(self, ad: Dict[str, Any]) -> float:
        """
        Calculate the CTR factor based on historical performance
        
        Args:
            ad: The ad data
            
        Returns:
            CTR factor (0-1)
        """
        # Get CTR from performance data
        performance = ad.get("performance", {})
        ctr = performance.get("ctr", 0.0)
        
        # Get baseline CTR from config or use default
        baseline_ctr = self.ranking_config.get("baseline_ctr", 2.0)
        
        # Calculate CTR factor (0-1)
        if baseline_ctr <= 0:
            return 0.0
        
        return min(1.0, ctr / baseline_ctr)
    
    def _get_budget_factor(self, ad: Dict[str, Any]) -> float:
        """
        Calculate the budget factor based on remaining daily budget
        
        Args:
            ad: The ad data
            
        Returns:
            Budget factor (0-1)
        """
        # Get daily budget and spent amount
        daily_budget = ad.get("daily_budget", 0.0)
        spent_today = ad.get("spent_today", 0.0)
        
        if daily_budget <= 0:
            return 0.0
        
        # Calculate remaining budget percentage
        remaining_percentage = (daily_budget - spent_today) / daily_budget
        
        # Return 0 if budget is exhausted
        return max(0.0, min(1.0, remaining_percentage))
    
    def _get_targeting_factor(self, ad: Dict[str, Any], user_context: Dict[str, Any]) -> float:
        """
        Calculate the targeting factor based on match between ad target audience and user context
        
        Args:
            ad: The ad data
            user_context: Information about the user
            
        Returns:
            Targeting factor (0-1)
        """
        # If no user context or target audience, return neutral value
        if not user_context or "target_audience" not in ad:
            return 0.5
        
        target_audience = ad["target_audience"]
        match_score = 0.0
        
        # Match interests
        if "interests" in target_audience and "interests" in user_context:
            ad_interests = set(target_audience["interests"])
            user_interests = set(user_context["interests"])
            if ad_interests and user_interests:
                interest_match = len(ad_interests.intersection(user_interests)) / len(ad_interests)
                match_score += interest_match * 0.5  # Interests contribute 50% to the targeting factor
        
        # Match demographics
        if "demographics" in target_audience and "demographics" in user_context:
            ad_demographics = target_audience["demographics"]
            user_demographics = user_context["demographics"]
            
            # Match age range
            if "age_min" in ad_demographics and "age_max" in ad_demographics and "age" in user_demographics:
                user_age = user_demographics["age"]
                if ad_demographics["age_min"] <= user_age <= ad_demographics["age_max"]:
                    match_score += 0.25  # Age match contributes 25% to the targeting factor
            
            # Match other demographics (e.g., location, gender)
            # This is a simplified version, but can be extended for specific requirements
            if "location" in ad_demographics and "location" in user_demographics:
                if ad_demographics["location"] == user_demographics["location"]:
                    match_score += 0.25  # Location match contributes 25% to the targeting factor
        
        return min(1.0, match_score)


# If the module is run directly, test it
if __name__ == "__main__":
    # Test the ranking engine
    from query_analyzer import QueryAnalyzer
    from ad_repository import AdRepository
    from ad_matcher import AdMatcher
    
    # Initialize components
    analyzer = QueryAnalyzer()
    repository = AdRepository()
    matcher = AdMatcher()
    ranking_engine = RankingEngine()
    
    # Analyze a test query
    query = "What's the best plywood for building a bookshelf?"
    analysis = analyzer.analyze_query(query)
    
    # Get all ads
    ads = repository.get_all_ads()
    
    # Match ads
    matched_ads = matcher.match_ads(analysis, ads)
    
    # Create a mock user context
    user_context = {
        "interests": ["DIY", "home improvement", "reading"],
        "demographics": {
            "age": 35,
            "location": "New York"
        }
    }
    
    # Rank ads
    ranked_ads = ranking_engine.rank_ads(matched_ads, user_context)
    
    # Print results
    print(f"Query: {query}")
    print(f"Found {len(ranked_ads)} ranked ads:")
    for i, ranked_ad in enumerate(ranked_ads):
        ad = ranked_ad["ad"]
        print(f"\n{i+1}. {ad['title']} (Final Score: {ranked_ad['final_score']:.2f})")
        print(f"   {ad['description']}")
        print(f"   Relevance: {ranked_ad['ranking_factors']['relevance']:.2f}")
        print(f"   Bid: ${ad['bid_amount']:.2f} (Factor: {ranked_ad['ranking_factors']['bid']:.2f})")
        print(f"   CTR Factor: {ranked_ad['ranking_factors']['ctr']:.2f}")
