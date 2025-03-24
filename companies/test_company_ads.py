import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from ad_service.ad_delivery.config_driven_ad_manager import ConfigDrivenAdManager

def test_company_ads():
    # Initialize the ad manager with our companies directory
    companies_dir = str(Path(__file__).parent)
    ad_manager = ConfigDrivenAdManager(companies_dir)
    
    print("\n=== Test Company Ad System Verification ===\n")
    
    # Print loaded companies
    print("1. Loaded Companies:")
    print("-" * 50)
    for company_id, config in ad_manager.company_configs.items():
        print(f"Company: {config['company_name']} (ID: {company_id})")
        print(f"Settings:")
        print(f"- Default Bid: ${config['ad_settings']['default_bid']}")
        print(f"- Daily Budget: ${config['ad_settings']['daily_budget']}")
        if 'testing_flags' in config:
            print("Testing Flags:")
            for flag, value in config['testing_flags'].items():
                print(f"- {flag}: {value}")
        print()
    
    # Print all loaded ads
    print("\n2. Loaded Ads:")
    print("-" * 50)
    for ad in ad_manager.ads:
        print(f"\nAd ID: {ad['ad_id']}")
        print(f"Title: {ad['title']}")
        print(f"Company: {ad['company_id']}")
        print(f"Campaign: {ad.get('campaign_id', 'N/A')}")
        print(f"Description: {ad['description']}")
        print(f"Categories: {', '.join(ad.get('categories', []))}")
        print(f"Keywords: {', '.join(ad.get('keywords', []))}")
        if 'intent_triggers' in ad:
            print("Intent Triggers:")
            for intent, triggers in ad['intent_triggers'].items():
                print(f"- {intent}: {', '.join(triggers)}")
        print(f"Price: ${ad.get('price', 'N/A')}")
        print("-" * 30)
    
    # Test various types of queries
    print("\n3. Testing Ad Matching:")
    print("-" * 50)
    
    test_queries = [
        # Purchase intent queries
        "I want to buy a new TV",
        "Looking for gaming laptop deals",
        "Need wireless headphones",
        
        # Research intent queries
        "What's the best 4K TV?",
        "Compare gaming laptops",
        "Reviews of noise-canceling headphones",
        
        # Price check queries
        "How much is the 65-inch smart TV?",
        "Price of RTX gaming laptops",
        "Cost of wireless headphones",
        
        # Contextual queries
        "Something good for watching movies",
        "Need a powerful computer for gaming",
        "Good for listening to music while traveling"
    ]
    
    conversation_id = "test_session_1"
    context = {"conversation_id": conversation_id}
    conversation_history = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest Query {i}: '{query}'")
        print("-" * 30)
        
        # Get relevant ad
        ad = ad_manager.get_relevant_ad(
            query, 
            context=context,
            conversation_history=conversation_history
        )
        
        if ad:
            print(f"Matched Ad: {ad['title']}")
            print(f"Relevance Score: {ad.get('relevance_score', 'N/A')}")
            if 'intent_match' in ad:
                print(f"Detected Intent: {ad['intent_match']}")
            if 'context_score' in ad:
                print(f"Context Score: {ad['context_score']}")
            print()
            
            # Add to conversation history
            conversation_history.append({
                "content": query,
                "timestamp": "2024-03-24T00:00:00Z",
                "matched_ad": ad['ad_id']
            })
        else:
            print("No matching ad found")
        print()


if __name__ == "__main__":
    test_company_ads() 