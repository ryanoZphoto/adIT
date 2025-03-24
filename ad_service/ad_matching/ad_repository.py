"""
Ad Repository Module

This module manages the ad inventory and provides methods for retrieving 
and updating ads. It serves as a data access layer for the ad matching engine.
"""

import json
import logging
import time
import os
from typing import List, Dict, Any, Optional
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdRepository:
    """
    Manages the ad inventory and provides access to ad data
    """
    
    def __init__(self, config_path: str = "../config/service_config.json"):
        """
        Initialize the ad repository
        
        Args:
            config_path: Path to the service configuration file
        """
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading config: {e}. Using default values.")
            self.config = {}
        
        # Initial product catalog
        self.ads = {
            "amazon_kindle": {
                "advertiser_id": "amazon_101",
                "campaign_id": "book_lovers",
                "title": "Amazon Kindle - Perfect for Book Lovers",
                "description": "Store thousands of books in one device. Special offer: 20% off Kindle Paperwhite!",
                "landing_page": "https://www.amazon.com/kindle-offer",
                "bid_amount": 1.80,
                "daily_budget": 200.00,
                "keywords": ["books", "reading", "e-reader", "kindle", "Amazon"],
                "categories": ["electronics", "reading", "books"],
                "status": "active"
            },
            "lowes_plywood": {
                "advertiser_id": "lowes_456",
                "title": "Lowe's - Birch Plywood Sale",
                "description": "Premium birch plywood, perfect for furniture. Now 20% off at Lowe's!",
                "bid_amount": 1.50,
                "daily_budget": 150.00,
                "landing_page": "https://www.lowes.com/birch-plywood",
                "keywords": ["birch plywood", "furniture", "wood"],
                "categories": ["home improvement", "DIY", "furniture"],
                "status": "active"
            }
        }
        
        logger.info("Ad repository initialized")
    
    def get_ads_by_category(self, category: str) -> List[Dict]:
        return [ad for ad in self.ads.values() if category in ad["categories"]]
    
    def get_ads_by_keywords(self, keywords: List[str]) -> List[Dict]:
        return [
            ad for ad in self.ads.values() 
            if any(keyword.lower() in [k.lower() for k in ad["keywords"]] for keyword in keywords)
        ]
    
    def get_all_ads(self) -> List[Dict[str, Any]]:
        """
        Get all ads in the inventory
        
        Returns:
            List of all ads
        """
        return list(self.ads.values())
    
    def get_ad_by_id(self, ad_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an ad by its ID
        
        Args:
            ad_id: Unique identifier for the ad
            
        Returns:
            Ad data or None if not found
        """
        return self.ads.get(ad_id)
    
    def get_ads_by_advertiser(self, advertiser_id: str) -> List[Dict[str, Any]]:
        """
        Get all ads for a specific advertiser
        
        Args:
            advertiser_id: Unique identifier for the advertiser
            
        Returns:
            List of ads for the advertiser
        """
        return [ad for ad in self.ads.values() if ad["advertiser_id"] == advertiser_id]
    
    def get_active_ads(self) -> List[Dict[str, Any]]:
        """
        Get all active ads
        
        Returns:
            List of active ads
        """
        return [ad for ad in self.ads.values() if ad["status"] == "active"]
    
    def add_ad(self, ad_data: Dict[str, Any]) -> str:
        """
        Add a new ad to the inventory
        
        Args:
            ad_data: Data for the new ad
            
        Returns:
            ID of the new ad
        """
        ad_id = ad_data.get("ad_id", str(uuid.uuid4()))
        ad_data["ad_id"] = ad_id
        ad_data["created_at"] = time.time()
        ad_data["performance"] = {
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "ctr": 0.0,
            "conversion_rate": 0.0
        }
        self.ads[ad_id] = ad_data
        logger.info(f"Added new ad with ID: {ad_id}")
        return ad_id
    
    def update_ad(self, ad_id: str, ad_data: Dict[str, Any]) -> bool:
        """
        Update an existing ad
        
        Args:
            ad_id: Unique identifier for the ad
            ad_data: Updated data for the ad
            
        Returns:
            True if the ad was updated, False if not found
        """
        if ad_id in self.ads:
            self.ads[ad_id].update(ad_data)
            logger.info(f"Updated ad with ID: {ad_id}")
            return True
        logger.warning(f"Failed to update ad - ID not found: {ad_id}")
        return False
    
    def update_ad_performance(self, ad_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Update performance metrics for an ad
        
        Args:
            ad_id: Unique identifier for the ad
            metrics: Updated performance metrics
            
        Returns:
            True if the ad was updated, False if not found
        """
        if ad_id in self.ads:
            ad = self.ads[ad_id]
            ad["performance"].update(metrics)
            impressions = ad["performance"]["impressions"]
            clicks = ad["performance"]["clicks"]
            conversions = ad["performance"]["conversions"]
            
            if impressions > 0:
                ad["performance"]["ctr"] = (clicks / impressions) * 100
            
            if clicks > 0:
                ad["performance"]["conversion_rate"] = (conversions / clicks) * 100
            
            logger.debug(f"Updated performance metrics for ad ID: {ad_id}")
            return True
        logger.warning(f"Failed to update performance - ad ID not found: {ad_id}")
        return False
    
    def delete_ad(self, ad_id: str) -> bool:
        """
        Delete an ad from the inventory
        
        Args:
            ad_id: Unique identifier for the ad
            
        Returns:
            True if the ad was deleted, False if not found
        """
        if ad_id in self.ads:
            del self.ads[ad_id]
            logger.info(f"Deleted ad with ID: {ad_id}")
            return True
        logger.warning(f"Failed to delete ad - ID not found: {ad_id}")
        return False


# If the module is run directly, test it
if __name__ == "__main__":
    # Test the ad repository
    repo = AdRepository()
    
    # Print all ads
    ads = repo.get_all_ads()
    print(f"Total ads: {len(ads)}")
    
    # Add a new ad
    new_ad = {
        "advertiser_id": "amazon_101",
        "campaign_id": "book_lovers",
        "title": "Amazon Kindle - Perfect for Book Lovers",
        "description": "Store thousands of books in one device. Special offer: 20% off Kindle Paperwhite!",
        "landing_page": "https://www.amazon.com/kindle-offer",
        "bid_amount": 1.80,
        "daily_budget": 200.00,
        "keywords": ["books", "reading", "e-reader", "kindle", "Amazon"],
        "categories": ["electronics", "reading", "books"],
        "status": "active"
    }
    
    new_ad_id = repo.add_ad(new_ad)
    print(f"Added new ad with ID: {new_ad_id}")
    
    # Update performance metrics
    repo.update_ad_performance(new_ad_id, {
        "impressions": 100,
        "clicks": 5,
        "conversions": 1
    })
    
    # Get and print the updated ad
    updated_ad = repo.get_ad_by_id(new_ad_id)
    print(f"Updated ad: {updated_ad}") 
