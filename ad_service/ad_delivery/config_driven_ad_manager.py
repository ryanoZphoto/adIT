import json
import os
import logging
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> dict:
    """Load configuration from config.yaml"""
    root_dir = os.getenv('AD_SERVICE_ROOT', '.')
    config_path = os.path.join(root_dir, 'config', 'config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        # If config file doesn't exist, return default configuration
        return {
            "paths": {
                "companies_dir": "companies"
            }
        }
        
    # Ensure required configuration sections exist
    if 'paths' not in config:
        config['paths'] = {}
        
    # Add default companies_dir if not present
    if 'companies_dir' not in config.get('paths', {}):
        config['paths']['companies_dir'] = "companies"
        
    return config

def resolve_path(path: str) -> str:
    """Resolve a path relative to the root directory"""
    root_dir = os.getenv('AD_SERVICE_ROOT', '.')
    return os.path.join(root_dir, path)

class ConfigDrivenAdManager:
    """
    Ad Manager that uses a configuration file to determine ad matching.
    All matching is dynamic based on actual ad content and real-time context.
    """
    
    # Intent detection patterns
    INTENT_PATTERNS = {
        'purchase_intent': [
            r'(?i)(looking for|want to buy|need a|shopping for)',
            r'(?i)(purchase|buy|get|acquire)',
            r'(?i)(recommend|suggest).*(to buy|purchase)',
        ],
        'research_intent': [
            r'(?i)(what\'s|what is|tell me about|learn about)',
            r'(?i)(compare|difference between|vs|versus)',
            r'(?i)(recommend|suggestion|advice|opinion)',
            r'(?i)(review|rating|best)',
        ],
        'price_check': [
            r'(?i)(how much|price|cost|pricing)',
            r'(?i)(cheaper|expensive|affordable)',
            r'(?i)(deal|discount|offer|sale)',
        ]
    }
    
    def __init__(self, companies_dir: str = None):
        """
        Initialize the ad manager with a companies directory.
        
        Args:
            companies_dir: Optional override for companies directory path
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Load configuration
        self.config = load_config()
        
        # Set companies directory from config if not provided
        if companies_dir is None:
            try:
                companies_dir = resolve_path(self.config['paths']['companies_dir'])
            except (KeyError, TypeError):
                # Fallback to default directory if path config is invalid
                companies_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "companies")
                self.logger.warning(f"No companies_dir configured, using default: {companies_dir}")
        
        # Verify companies directory exists
        if not os.path.exists(companies_dir):
            self.logger.warning(f"Companies directory not found at {companies_dir}. Ad matching will be limited.")
            # Create empty company data structures
            self.companies_dir = companies_dir
            self.company_configs = {}
            self.ads = {}
            self.keyword_index = defaultdict(list)
            self.category_index = defaultdict(list)
        else:
            self.companies_dir = companies_dir
            self.logger.info(f"Loading company configurations from {self.companies_dir}")
            
            # Initialize tracking dictionaries
            self.company_configs = {}
            self.ads = {}
            self.keyword_index = defaultdict(list)
            self.category_index = defaultdict(list)
            
            # Load all company configurations
            self._load_company_configs()
        
        # Log initialization summary
        msg = (f"ConfigDrivenAdManager initialized with {len(self.ads)} ads "
               f"from {len(self.company_configs)} companies")
        self.logger.critical(msg)
        
        self.logger.info(
            f"Built keyword index with {len(self.keyword_index)} unique keywords"
        )
        self.logger.info(
            f"Built category index with {len(self.category_index)} unique categories"
        )
        
        self.system_config = {
            "default_relevance_threshold": 0.3,
            "max_ads_per_query": 1
        }
        self.conversation_contexts = {}  # Track conversation context
        
        # Build indexes for fast lookup
        self._build_indexes()
        
    def _load_company_configs(self):
        """Load configurations for all companies."""
        try:
            self.logger.info(f"Loading company configurations from {self.companies_dir}")
            
            # Get all company directories
            company_dirs = [d for d in os.listdir(self.companies_dir) 
                           if os.path.isdir(os.path.join(self.companies_dir, d)) 
                           and not d.startswith('.')]
            
            for company_dir in company_dirs:
                if company_dir == 'template_company':
                    continue  # Skip template directory
                    
                company_path = os.path.join(self.companies_dir, company_dir)
                config_path = os.path.join(company_path, 'config', 'company_config.json')
                
                # Skip if company doesn't have a config file
                if not os.path.exists(config_path):
                    self.logger.info(f"Skipping {company_dir} - no configuration found")
                    continue
                    
                try:
                    self._load_company_config(company_dir, company_path)
                except Exception as e:
                    self.logger.warning(
                        f"Error loading configuration for {company_dir}: {str(e)}"
                    )
                    continue
            
            self.logger.info(f"Loaded configurations for {len(self.company_configs)} companies")
            
        except Exception as e:
            self.logger.error(f"Error scanning company directories: {str(e)}")
            # Initialize with empty configuration
            self.ads = {}
            self.company_configs = {}

    def _load_company_config(self, company_id: str, company_path: str):
        """Load configuration for a specific company."""
        try:
            # Load company config
            config_path = os.path.join(company_path, 'config', 'company_config.json')
            with open(config_path, 'r') as f:
                company_config = json.load(f)
            
            self.company_configs[company_id] = company_config
            
            # Load all campaign files
            campaigns_path = os.path.join(company_path, 'ads')
            campaign_files = [f for f in os.listdir(campaigns_path) 
                             if f.endswith('.json')]
            
            for campaign_file in campaign_files:
                campaign_path = os.path.join(campaigns_path, campaign_file)
                with open(campaign_path, 'r') as f:
                    campaign = json.load(f)
                
                # Process each ad in the campaign
                for ad in campaign.get('ads', []):
                    # Add company and campaign information to the ad
                    ad['company_id'] = company_id
                    ad['campaign_id'] = campaign['campaign_id']
                    
                    # Apply company default settings if not specified
                    if 'match_weights' not in ad:
                        ad['match_weights'] = company_config['ad_settings']['default_match_weights']
                    
                    # Add the ad to our collection
                    self.ads[ad['ad_id']] = ad
            
            self.logger.info(
                f"Loaded {len(campaign_files)} campaigns for company {company_id}"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error loading configuration for company {company_id}: {str(e)}"
            )
            raise

    def _build_indexes(self):
        """Build keyword and category indexes for fast ad lookup."""
        self.keyword_index = defaultdict(list)
        self.category_index = defaultdict(list)
        
        for ad in self.ads.values():
            ad_id = ad.get('ad_id')
            
            # Index keywords
            for keyword in ad.get('keywords', []):
                keyword = keyword.lower()
                self.keyword_index[keyword].append(ad_id)
            
            # Index categories
            for category in ad.get('categories', []):
                category = category.lower()
                self.category_index[category].append(ad_id)
        
        self.logger.info(f"Built keyword index with {len(self.keyword_index)} unique keywords")
        self.logger.info(f"Built category index with {len(self.category_index)} unique categories")
    
    def _detect_intents(self, query: str) -> Dict[str, float]:
        """
        Detect user intents from the query text.
        Returns a dictionary of intent types and their confidence scores.
        """
        intents = {}
        
        # Check each intent type
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            # Count how many patterns match
            matches = sum(1 for pattern in patterns if re.search(pattern, query))
            if matches:
                # Calculate confidence based on number of matching patterns
                confidence = min(1.0, matches / len(patterns) + 0.3)
                intents[intent_type] = confidence
        
        return intents

    def _update_conversation_context(
        self, 
        query: str, 
        context: Dict,
        conversation_history: List[Dict]
    ) -> None:
        """Update the conversation context with new information."""
        conv_id = context.get('conversation_id', 'default')
        
        if conv_id not in self.conversation_contexts:
            self.conversation_contexts[conv_id] = {
                'topics': defaultdict(float),  # Topic -> relevance score
                'intents': defaultdict(float),  # Intent -> confidence score
                'preferences': defaultdict(float),  # Product/feature preferences
                'discussed_products': [],  # Products mentioned in conversation
                'topic_history': [],  # Track topic transitions
                'last_queries': [],  # Recent queries
                'last_update': time.time()
            }
        
        context_data = self.conversation_contexts[conv_id]
        
        # Update last queries with timestamp
        context_data['last_queries'].append({
            'text': query,
            'timestamp': time.time()
        })
        if len(context_data['last_queries']) > 5:  # Keep last 5 queries
            context_data['last_queries'].pop(0)
        
        # Detect current topics and preferences
        current_topics = self._extract_topics(query)
        current_prefs = self._extract_preferences(query)
        
        # Update topic history
        if current_topics:
            context_data['topic_history'].append({
                'topics': current_topics,
                'timestamp': time.time()
            })
            if len(context_data['topic_history']) > 10:  # Keep last 10 topic transitions
                context_data['topic_history'].pop(0)
        
        # Update topic scores with temporal decay
        for topic, score in current_topics.items():
            old_score = context_data['topics'][topic] * 0.8  # Decay factor
            context_data['topics'][topic] = min(1.0, max(old_score, score))
        
        # Update user preferences
        for pref, value in current_prefs.items():
            old_value = context_data['preferences'][pref] * 0.9  # Slower decay for preferences
            context_data['preferences'][pref] = min(1.0, max(old_value, value))
        
        # Extract and track discussed products
        products = self._extract_products(query)
        for product in products:
            if product not in context_data['discussed_products']:
                context_data['discussed_products'].append({
                    'name': product,
                    'first_mentioned': time.time(),
                    'last_mentioned': time.time(),
                    'mention_count': 1
                })
            else:
                # Update existing product stats
                for p in context_data['discussed_products']:
                    if p['name'] == product:
                        p['last_mentioned'] = time.time()
                        p['mention_count'] += 1
        
        # Detect intents from the current query
        current_intents = self._detect_intents(query)
        
        # Update conversation intents with temporal decay
        for intent, score in current_intents.items():
            old_score = context_data['intents'][intent] * 0.8  # Decay factor
            context_data['intents'][intent] = min(1.0, max(score, old_score))
        
        # Process conversation history if available
        if conversation_history:
            self._process_history(conv_id, conversation_history)

    def _extract_preferences(self, text: str) -> Dict[str, float]:
        """Extract user preferences from text."""
        preferences = {}
        
        # Price sensitivity patterns
        price_patterns = {
            'budget_conscious': [
                r'(?i)(cheap|affordable|budget|save money|cost-effective)',
                r'(?i)(lowest price|best deal|discount|sale)',
            ],
            'premium': [
                r'(?i)(high-end|premium|luxury|best quality|top-tier)',
                r'(?i)(professional|advanced|elite)',
            ]
        }
        
        # Feature preference patterns
        feature_patterns = {
            'performance': [
                r'(?i)(fast|powerful|speed|performance|efficient)',
                r'(?i)(high-performance|processing|capacity)',
            ],
            'quality': [
                r'(?i)(reliable|durable|long-lasting|quality)',
                r'(?i)(well-made|solid|robust)',
            ],
            'convenience': [
                r'(?i)(easy|simple|convenient|quick|handy)',
                r'(?i)(user-friendly|straightforward)',
            ]
        }
        
        # Check price preferences
        for pref_type, patterns in price_patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text))
            if matches:
                preferences[pref_type] = min(1.0, matches / len(patterns) + 0.3)
        
        # Check feature preferences
        for pref_type, patterns in feature_patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text))
            if matches:
                preferences[pref_type] = min(1.0, matches / len(patterns) + 0.3)
        
        return preferences

    def _extract_products(self, text: str) -> List[str]:
        """Extract product mentions from text."""
        products = []
        
        # Extract products from ads index
        for keyword in self.keyword_index.keys():
            if ' ' in keyword and keyword.lower() in text.lower():
                products.append(keyword)
        
        # Extract brand mentions
        for ad in self.ads.values():
            brand = ad.get('brand', '').lower()
            if brand and brand in text.lower():
                products.append(brand)
        
        return list(set(products))  # Remove duplicates

    def _process_history(self, conv_id: str, history: List[Dict]) -> None:
        """Process conversation history to update context."""
        context_data = self.conversation_contexts[conv_id]
        
        for message in history[-5:]:  # Process last 5 messages
            if isinstance(message, dict) and 'content' in message:
                text = message['content']
                
                # Extract and update topics with reduced weight
                topics = self._extract_topics(text)
                for topic, score in topics.items():
                    context_data['topics'][topic] = min(
                        1.0, 
                        context_data['topics'][topic] * 0.9 + score * 0.1
                    )
                
                # Extract and update preferences with reduced weight
                prefs = self._extract_preferences(text)
                for pref, value in prefs.items():
                    context_data['preferences'][pref] = min(
                        1.0,
                        context_data['preferences'][pref] * 0.9 + value * 0.1
                    )
                
                # Track products mentioned in history
                products = self._extract_products(text)
                for product in products:
                    if product not in [p['name'] for p in context_data['discussed_products']]:
                        context_data['discussed_products'].append({
                            'name': product,
                            'first_mentioned': time.time(),
                            'last_mentioned': time.time(),
                            'mention_count': 1
                        })

    def _extract_topics(self, text: str) -> Dict[str, float]:
        """Extract topics from text with confidence scores."""
        topics = {}
        text = text.lower()
        
        # Topic patterns with weights
        topic_patterns = {
            'technology': {
                'patterns': [
                    (r'(?i)(computer|laptop|phone|tech|software|hardware|device)', 1.0),
                    (r'(?i)(digital|smart|electronic|gadget|app)', 0.8),
                    (r'(?i)(processor|memory|storage|battery)', 0.9)
                ],
                'keywords': ['computer', 'laptop', 'phone', 'tech', 'software', 'hardware']
            },
            'fashion': {
                'patterns': [
                    (r'(?i)(shoes|clothing|wear|fashion|style|outfit)', 1.0),
                    (r'(?i)(dress|shirt|pants|accessories)', 0.8),
                    (r'(?i)(comfortable|fit|size)', 0.7)
                ],
                'keywords': ['shoes', 'clothing', 'wear', 'fashion', 'style']
            },
            'sports': {
                'patterns': [
                    (r'(?i)(run|sport|exercise|fitness|workout|training)', 1.0),
                    (r'(?i)(athletic|gym|performance|endurance)', 0.8),
                    (r'(?i)(muscle|strength|cardio)', 0.7)
                ],
                'keywords': ['run', 'sport', 'exercise', 'fitness', 'workout']
            }
        }
        
        # Check each topic
        for topic, config in topic_patterns.items():
            score = 0.0
            
            # Check patterns with weights
            for pattern, weight in config['patterns']:
                if re.search(pattern, text):
                    score += weight
            
            # Check keywords
            keyword_matches = sum(1 for word in config['keywords'] if word in text)
            if keyword_matches:
                score += keyword_matches * 0.2
            
            # Normalize score
            if score > 0:
                topics[topic] = min(1.0, score / 3.0)  # Normalize to 0-1 range
        
        return topics

    def get_relevant_ad(
        self, 
        query: str, 
        context: Dict = None,
        conversation_history: List = None
    ) -> Optional[Dict]:
        """
        Find the most relevant ad for a given query.
        
        Args:
            query: The user's query text
            context: Additional context about the query (optional)
            conversation_history: Previous conversation for context (optional)
            
        Returns:
            Dict containing the ad information or None if no relevant ad found
        """
        try:
            self.logger.info(f"Finding relevant ad for query: '{query}'")
            
            # Update conversation context
            if context:
                self._update_conversation_context(query, context, conversation_history)
            
            # Normalize query
            normalized_query = query.lower()
            
            # 1. Try direct keyword matching first
            keyword_matches = self._find_keyword_matches(normalized_query)
            self.logger.info(f"Keyword matches: {keyword_matches}")
            
            # 2. Try category matching if no keywords match
            category_matches = {}
            if not keyword_matches:
                category_matches = self._find_category_matches(normalized_query)
                self.logger.info(f"Category matches: {category_matches}")
            
            # 3. Calculate relevance scores
            scored_ads = self._calculate_relevance_scores(
                normalized_query, 
                keyword_matches,
                category_matches,
                context
            )
            self.logger.info(f"Scored ads: {scored_ads}")
            
            # 4. Get the highest scoring ad that meets the threshold
            if scored_ads:
                # Sort by score, highest first
                sorted_ads = sorted(
                    scored_ads.items(),
                    key=lambda x: x[1]['total_score'],
                    reverse=True
                )
                top_ad_id, top_score = sorted_ads[0]
                
                # Get the full ad details
                for ad in self.ads.values():
                    if ad['ad_id'] == top_ad_id:
                        result_ad = ad.copy()
                        result_ad['match_factors'] = top_score
                        self.logger.info(
                            f"Found relevant ad: {result_ad['title']} "
                            f"(score: {top_score['total_score']:.2f})"
                        )
                        return result_ad
            
            self.logger.info("No relevant ad found for query")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding relevant ad: {str(e)}")
            return None
    
    def _find_keyword_matches(self, query: str) -> Dict[str, List[str]]:
        """Find all ads that have matching keywords with the query."""
        matches = {}
        query = query.lower()  # Convert query to lowercase for case-insensitive matching
        
        self.logger.debug(f"Searching for matches in query: '{query}'")
        self.logger.debug(f"Available keywords: {list(self.keyword_index.keys())}")
        
        # Extract words from query
        query_words = re.findall(r'\b\w+\b', query.lower())
        self.logger.debug(f"Query words: {query_words}")
        
        # Check for each keyword (exact word matches)
        for word in query_words:
            if word in self.keyword_index:
                for ad_id in self.keyword_index[word]:
                    if ad_id not in matches:
                        matches[ad_id] = []
                    matches[ad_id].append(word)
        
        # Also check for multi-word keywords
        for keyword in self.keyword_index:
            if ' ' in keyword and keyword.lower() in query:
                for ad_id in self.keyword_index[keyword]:
                    if ad_id not in matches:
                        matches[ad_id] = []
                    matches[ad_id].append(keyword)
        
        # Check for partial matches in both directions:
        # 1. Keywords contained within query words (e.g., "tv" in "smart tv")
        # 2. Query words contained within keywords (e.g., "apple" when keyword is "apple products")
        for keyword in self.keyword_index:
            # Skip already matched exact keywords or multi-word keywords
            is_already_matched = (keyword.lower() in query_words or 
                                (' ' in keyword and keyword.lower() in query))
            if is_already_matched:
                continue
                
            # Case 1: Keyword is contained within a query word or phrase
            # This handles cases like "tv" in "smart tv" or "m3" in "m3 chip"
            found_match = False
            # Check for keyword within individual words
            for query_word in query_words:
                if (keyword.lower() in query_word and 
                    keyword.lower() != query_word):
                    found_match = True
                    break
            
            # Check for keyword within the entire query even if not a whole word
            # This helps with things like partial brand names or product identifiers
            if not found_match and keyword.lower() in query.lower():
                found_match = True
                
            if found_match:
                for ad_id in self.keyword_index[keyword]:
                    if ad_id not in matches:
                        matches[ad_id] = []
                    if keyword not in matches[ad_id]:  # Avoid duplicates
                        matches[ad_id].append(keyword)
            
            # Case 2: Query word is contained within a keyword
            # This handles cases like query "apple" matching keyword "apple products"
            elif ' ' in keyword.lower():
                keyword_parts = keyword.lower().split()
                for query_word in query_words:
                    if query_word in keyword_parts:
                        for ad_id in self.keyword_index[keyword]:
                            if ad_id not in matches:
                                matches[ad_id] = []
                            if keyword not in matches[ad_id]:  # Avoid duplicates
                                matches[ad_id].append(keyword)
                                break
        
        self.logger.debug(f"Keyword matches found: {matches}")
        return matches
    
    def _find_category_matches(self, query: str) -> Dict[str, List[str]]:
        """Find all ads that have matching categories with the query."""
        matches = {}
        
        # Extract words from query
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        # Check for each category
        for word in query_words:
            if word in self.category_index:
                for ad_id in self.category_index[word]:
                    if ad_id not in matches:
                        matches[ad_id] = []
                    matches[ad_id].append(word)
        
        return matches
    
    def _calculate_relevance_scores(
        self,
        query: str,
        keyword_matches: Dict,
        category_matches: Dict,
        context: Dict = None
    ) -> Dict:
        """Calculate relevance scores for all potential matching ads."""
        scored_ads = {}
        
        # Calculate scores for keyword matches
        for ad_id, matched_keywords in keyword_matches.items():
            for ad in self.ads.values():
                if ad['ad_id'] == ad_id:
                    # Get weighting configuration for this ad
                    weights = ad.get('match_weights', {
                        'keyword_match': 0.4,
                        'category_match': 0.3,
                        'intent_match': 0.3
                    })
                    
                    # Calculate keyword score based on number of matched keywords
                    total_keywords = len(ad.get('keywords', []))
                    keyword_count = len(matched_keywords)
                    
                    # Boost score for exact matches
                    keyword_boost = 1.0
                    if any(kw.lower() in query.lower() for kw in matched_keywords):
                        keyword_boost = 1.5  # Boost for exact matches
                        
                    keyword_score = min(
                        1.0,
                        (keyword_count / max(1, min(total_keywords, 5))) * keyword_boost
                    )
                    
                    # Direct term score (1.0 if exact match)
                    direct_term_score = 1.0 if any(kw in query for kw in matched_keywords) else 0.8
                    
                    # Calculate intent match score if context available
                    intent_score = 0.0
                    if context and 'conversation_id' in context:
                        conv_id = context['conversation_id']
                        if conv_id in self.conversation_contexts:
                            # Get the highest intent score
                            intents = self.conversation_contexts[conv_id]['intents']
                            if intents:
                                intent_score = max(intents.values())
                    
                    # Calculate total score with all factors
                    total_score = (
                        keyword_score * weights['keyword_match'] +
                        direct_term_score * weights['category_match'] +
                        intent_score * weights['intent_match']
                    )
                    
                    # Apply additional boost for matches that use multiple words
                    if keyword_count > 1:
                        total_score *= 1.2  # 20% boost for multiple keyword matches
                    
                    scored_ads[ad_id] = {
                        'total_score': min(1.0, total_score),  # Cap at 1.0
                        'keyword_score': keyword_score,
                        'direct_term_score': direct_term_score,
                        'intent_score': intent_score,
                        'matched_keywords': matched_keywords,
                        'matched_categories': []
                    }
        
        # Calculate scores for category matches
        for ad_id, matched_categories in category_matches.items():
            for ad in self.ads.values():
                if ad['ad_id'] == ad_id:
                    # Get weighting configuration for this ad
                    weights = ad.get('match_weights', {
                        'keyword_match': 0.4,
                        'category_match': 0.3,
                        'intent_match': 0.3
                    })
                    
                    # Calculate category score based on number of matched categories
                    total_categories = len(ad.get('categories', []))
                    category_count = len(matched_categories)
                    category_score = min(1.0, category_count / max(1, total_categories)) if total_categories > 0 else 0
                    
                    # Calculate intent match score if context available
                    intent_score = 0.0
                    if context and 'conversation_id' in context:
                        conv_id = context['conversation_id']
                        if conv_id in self.conversation_contexts:
                            # Get the highest intent score
                            intents = self.conversation_contexts[conv_id]['intents']
                            if intents:
                                intent_score = max(intents.values())
                    
                    # Calculate total score
                    total_score = (
                        category_score * weights['category_match'] +
                        intent_score * weights['intent_match']
                    )
                    
                    # If we already calculated a keyword score, just update with category info
                    if ad_id in scored_ads:
                        scored_ads[ad_id]['category_score'] = category_score
                        scored_ads[ad_id]['matched_categories'] = matched_categories
                        scored_ads[ad_id]['intent_score'] = intent_score
                        scored_ads[ad_id]['total_score'] += total_score
                        # Cap at 1.0
                        scored_ads[ad_id]['total_score'] = min(
                            1.0,
                            scored_ads[ad_id]['total_score']
                        )
                    else:
                        scored_ads[ad_id] = {
                            'total_score': min(1.0, total_score),  # Cap at 1.0
                            'category_score': category_score,
                            'keyword_score': 0.0,
                            'direct_term_score': 0.0,
                            'intent_score': intent_score,
                            'matched_keywords': [],
                            'matched_categories': matched_categories
                        }
        
        # Apply minimum threshold from system config
        threshold = self.system_config.get('default_relevance_threshold', 0.3)
        self.logger.info(f"Using relevance threshold: {threshold}")
        
        filtered_ads = {
            k: v for k, v in scored_ads.items()
            if v['total_score'] >= threshold
        }
        self.logger.info(f"Filtered ads (after threshold): {filtered_ads}")
        return filtered_ads
    
    def reload_config(self):
        """Reload all company configurations."""
        self.ads = {}
        self.company_configs = {}
        self._load_company_configs()
        self._build_indexes()
        self.logger.info("Reloaded all company configurations")

    def _calculate_context_score(self, ad: Dict, context: Dict) -> float:
        """Calculate how well an ad matches the conversation context."""
        score = 0.0
        
        # Get ad metadata
        ad_topics = set(ad.get('topics', []))
        ad_categories = set(ad.get('categories', []))
        ad_keywords = set(ad.get('keywords', []))
        
        # Topic alignment
        for topic, relevance in context['topics'].items():
            if topic in ad_topics or topic.lower() in ad_categories:
                score += relevance * 0.4  # Topics contribute 40% to context score
        
        # Intent alignment
        ad_intent = ad.get('target_intent', [])
        if isinstance(ad_intent, str):
            ad_intent = [ad_intent]
        
        for intent, confidence in context['intents'].items():
            if intent in ad_intent:
                score += confidence * 0.4  # Intent contributes 40% to context score
        
        # Recent query alignment
        recent_queries = context['last_queries']
        if recent_queries:
            # Check if any recent queries are particularly relevant to this ad
            query_matches = sum(
                1 for query in recent_queries 
                if any(kw in query for kw in ad_keywords)
            )
            score += min(0.2, query_matches * 0.05)  # Recent queries contribute up to 20%
        
        return min(1.0, score)  # Cap at 1.0


# Example usage
if __name__ == "__main__":
    ad_manager = ConfigDrivenAdManager()
    
    # Test some queries
    test_queries = [
        "I need new running shoes",
        "What's a good laptop for college?",
        "Tell me about the MacBook Pro",
        "I want to learn data science",
        "education classes online"
    ]
    
    for query in test_queries:
        ad = ad_manager.get_relevant_ad(query)
        if ad:
            print(f"Query: '{query}' → Ad: {ad['title']} (Score: {ad.get('match_factors', {}).get('total_score', 'N/A')})")
        else:
            print(f"Query: '{query}' → No relevant ad found") 