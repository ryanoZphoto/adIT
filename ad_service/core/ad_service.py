from openai import OpenAI
import logging
from ad_service.analytics.metrics_collector import MetricsCollector
from ad_service.ad_matching.ad_matcher import AdMatcher

logger = logging.getLogger(__name__)

class AdService:
    def __init__(self):
        self.client = OpenAI()
        self.metrics_collector = MetricsCollector()
        self.ad_matcher = AdMatcher()
        
    def process_query(self, query: str) -> str:
        """
        Process a query and return response with contextual ad
        """
        try:
            # Get base response
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": query}
                ]
            )
            base_response = response.choices[0].message.content
            
            # Match relevant ad
            matched_ad = self.ad_matcher.match_ad(query)
            
            # Combine response with ad
            if matched_ad:
                final_response = f"{base_response}\n\n[Ad] {matched_ad['content']}"
            else:
                final_response = base_response
                
            # Record metrics
            self.metrics_collector.record_ad_request()
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "I apologize, but I encountered an error processing your request. Please try again."
