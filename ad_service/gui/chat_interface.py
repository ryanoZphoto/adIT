import streamlit as st
import os
import sys
import httpx
from openai import OpenAI
import time
import uuid

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import ad matching components
from ad_service.ad_matching.query_analyzer import QueryAnalyzer
from ad_service.ad_matching.ad_matcher import AdMatcher
from ad_service.ad_delivery.config_driven_ad_manager import ConfigDrivenAdManager
# Import analytics components
from ad_service.analytics.metrics_collector import MetricsCollector

# The page config has been moved to the main streamlit_app.py file
# to avoid multiple st.set_page_config() calls

def render_chat_interface():
    st.title("Ad Service Chat Interface")
    
    # Initialize metrics collector for tracking
    try:
        metrics_collector = MetricsCollector()
        metrics_available = True
    except Exception as e:
        st.sidebar.error(f"Metrics collection not available: {str(e)}")
        metrics_available = False
    
    # Initialize ad matcher, query analyzer and config driven ad manager
    try:
        ad_matcher = AdMatcher()
        query_analyzer = QueryAnalyzer()
        config_ad_manager = ConfigDrivenAdManager()
        ad_matching_available = True
        st.sidebar.success("Ad matching system loaded successfully")
    except Exception as e:
        st.sidebar.error(f"Ad matching system not available: {str(e)}")
        ad_matching_available = False
    
    # Generate a unique session ID if not already in session state
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Track user as active in metrics
    if metrics_available:
        metrics_collector.active_users_gauge.inc()
    
    # API key handling in the sidebar
    with st.sidebar:
        st.subheader("OpenAI API Configuration")
        api_key = st.text_input("Enter your OpenAI API key", type="password")
        
        if api_key:
            st.session_state["openai_api_key"] = api_key
            st.success("API key set! You can now chat with the AI assistant.")
        elif "openai_api_key" in st.session_state:
            st.success("API key already set!")
        else:
            st.warning("Please enter your OpenAI API key to enable the chat functionality.")
            st.markdown("Don't have an API key? [Get one here](https://platform.openai.com/api-keys)")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize ad tracking
    if "displayed_ads" not in st.session_state:
        st.session_state.displayed_ads = {}  # {ad_id: timestamp}
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know about?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Record query in metrics
        if metrics_available:
            metrics_collector.ad_requests_counter.inc()
            
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Start query processing timer if metrics available
        query_start_time = time.time()
        
        # Check for relevant ads based on user message
        if ad_matching_available:
            try:
                # Method 1: Use AdMatcher
                try:
                    # Analyze the user's message for potential ad triggers
                    conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                           for msg in st.session_state.messages]
                    
                    # Match ads based on conversation history
                    matched_ads = ad_matcher.match_ads(conversation_history)
                    
                    # Display matched ads in sidebar if any are found
                    if matched_ads:
                        with st.sidebar:
                            st.subheader("Suggested Products (AdMatcher)")
                            for ad_result in matched_ads[:2]:  # Limit to top 2 ads
                                ad = ad_result["ad"]
                                ad_id = ad.get('id', ad.get('ad_id', str(hash(ad['title']))))
                                
                                # Record impression in metrics collector
                                if metrics_available:
                                    metrics_collector.log_ad_impression(
                                        query=prompt,
                                        ad_id=ad_id,
                                        relevance_score=ad_result.get("score", 0.5)
                                    )
                                    metrics_collector.ad_impressions_counter.inc()
                                
                                # Store in session state for tracking
                                st.session_state.displayed_ads[ad_id] = time.time()
                                
                                with st.container():
                                    st.markdown(f"**{ad['title']}**")
                                    st.markdown(f"{ad['description']}")
                                    
                                    # Create a clickable button for tracking
                                    if st.button(ad.get('call_to_action', 'Learn More'), key=f"ad_click_{ad_id}"):
                                        # Record click in metrics collector
                                        if metrics_available:
                                            metrics_collector.log_ad_click(
                                                ad_id=ad_id,
                                                user_id=st.session_state.session_id
                                            )
                                            metrics_collector.ad_clicks_counter.inc()
                                        
                                        # Open URL
                                        st.markdown(f"<script>window.open('{ad['url']}', '_blank')</script>", unsafe_allow_html=True)
                                    
                                    if 'image_url' in ad:
                                        st.image(ad['image_url'], width=200)
                                    st.markdown("---")
                except Exception as e:
                    st.sidebar.error(f"Error with AdMatcher: {str(e)}")
                
                # Method 2: Use ConfigDrivenAdManager 
                try:
                    # Create simple context dictionary
                    context = {
                        'conversation_id': st.session_state.session_id,
                        'timestamp': time.time()
                    }
                    
                    # Use the proper method signature with conversation history
                    conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                           for msg in st.session_state.messages]
                    
                    relevant_ad = config_ad_manager.get_relevant_ad(
                        prompt,
                        context=context,
                        conversation_history=conversation_history
                    )
                    
                    if relevant_ad:
                        with st.sidebar:
                            st.subheader("Suggested Products (ConfigDriven)")
                            
                            # Get ad ID 
                            ad_id = relevant_ad.get('ad_id', relevant_ad.get('id', str(hash(relevant_ad['title']))))
                            
                            # Record impression in metrics collector
                            if metrics_available:
                                score = relevant_ad.get('match_factors', {}).get('total_score', 0.5)
                                metrics_collector.log_ad_impression(
                                    query=prompt,
                                    ad_id=ad_id,
                                    relevance_score=score
                                )
                                metrics_collector.ad_impressions_counter.inc()
                            
                            # Store in session state for tracking
                            st.session_state.displayed_ads[ad_id] = time.time()
                            
                            with st.container():
                                st.markdown(f"**{relevant_ad['title']}**")
                                st.markdown(f"{relevant_ad['description']}")
                                
                                # Handle different field names between ad systems
                                cta = relevant_ad.get('cta', relevant_ad.get('call_to_action', 'Learn More'))
                                target_url = relevant_ad.get('target_url', relevant_ad.get('url', '#'))
                                
                                # Create a clickable button for tracking
                                if st.button(cta, key=f"config_ad_click_{ad_id}"):
                                    # Record click in metrics collector
                                    if metrics_available:
                                        metrics_collector.log_ad_click(
                                            ad_id=ad_id, 
                                            user_id=st.session_state.session_id
                                        )
                                        metrics_collector.ad_clicks_counter.inc()
                                    
                                    # Open URL
                                    st.markdown(f"<script>window.open('{target_url}', '_blank')</script>", unsafe_allow_html=True)
                                
                                if 'image_url' in relevant_ad:
                                    st.image(relevant_ad['image_url'], width=200)
                                st.markdown("---")
                except Exception as e:
                    st.sidebar.error(f"Error with ConfigDrivenAdManager: {str(e)}")
            except Exception as e:
                st.sidebar.error(f"Error matching ads: {str(e)}")
        
        # Display assistant response
        with st.chat_message("assistant"):
            # Check if OpenAI API key is available
            if "openai_api_key" in st.session_state:
                try:
                    # Create a custom httpx client without proxy configuration
                    http_client = httpx.Client(
                        # No proxy configuration here to avoid the error
                        transport=httpx.HTTPTransport(local_address="0.0.0.0")
                    )
                    
                    # Initialize OpenAI client with the API key and custom HTTP client
                    # This avoids the proxies parameter error
                    client = OpenAI(
                        api_key=st.session_state["openai_api_key"],
                        http_client=http_client
                    )
                    
                    # Use a placeholder message while waiting for response
                    message_placeholder = st.empty()
                    message_placeholder.markdown("Thinking...")
                    
                    # Record start time for model generation
                    model_start_time = time.time()
                    
                    # Call the OpenAI API
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful, general-purpose assistant. Provide informative and friendly responses on any topic the user asks about. You may occasionally show relevant advertisements based on keywords in the conversation, but your primary role is to be helpful on any subject."},
                            *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                        ],
                        stream=True
                    )
                    
                    # Stream the response
                    full_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    
                    # Display the final response
                    message_placeholder.markdown(full_response)
                    
                    # Record model generation time
                    model_generation_time = time.time() - model_start_time
                    if metrics_available:
                        metrics_collector.log_model_generation(
                            query=prompt,
                            response=full_response[:200],  # First 200 chars
                            model="gpt-3.5-turbo",
                            generation_time=model_generation_time
                        )
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                except Exception as e:
                    error_message = f"Error connecting to OpenAI API: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                    
                    # Provide more helpful troubleshooting advice
                    st.warning("""
                    Possible solutions:
                    1. Make sure your API key is valid and not expired
                    2. Check if you have sufficient credits in your OpenAI account
                    3. This may be a temporary OpenAI service issue - try again in a few minutes
                    """)
            else:
                # Fallback response if no API key is provided
                response = "Please provide your OpenAI API key in the sidebar to enable AI-powered responses."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Record query processing time
        if metrics_available:
            query_processing_time = time.time() - query_start_time
            metrics_collector.query_processing_time.observe(query_processing_time)

# Rename the main function to render_chat_interface to match import in streamlit_app.py
if __name__ == "__main__":
    render_chat_interface() 