import streamlit as st
from openai import OpenAI
import os
import time
import uuid
import logging
from dotenv import load_dotenv
from ad_service.analytics.metrics_collector import (
    MetricsCollector, 
    configure_root_logger
)
from ad_service.gui.ad_manager_ui import (
    render_ad_manager_ui  # Import the ad manager UI
)

# Configure logging
configure_root_logger()

# Get logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Force DEBUG level for this module

# Log startup
logger.critical("MAIN APP STARTING - USING CONFIG DRIVEN AD MANAGER")

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Ad Service Chat",
    page_icon="💬",
    layout="wide"
)

# Initialize services
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Now that we've fixed the path issues, we can use ConfigDrivenAdManager
try:
    # First try to use the config-driven manager
    from ad_service.ad_delivery.config_driven_ad_manager import (
        ConfigDrivenAdManager
    )
    ad_manager = ConfigDrivenAdManager()
    logger.critical("Successfully loaded CONFIG DRIVEN AD MANAGER")
except ImportError as e:
    # Fall back to original if import fails
    logger.critical(f"Failed to import ConfigDrivenAdManager: {e}")
    logger.critical("Falling back to original AdDeliveryManager")
    from ad_service.ad_delivery.ad_delivery_manager import AdDeliveryManager
    ad_manager = AdDeliveryManager()

metrics = MetricsCollector()

# Log initialization
logger.critical(
    f"CONFIG-DRIVEN AD MANAGER INITIALIZED: "
    f"{len(ad_manager.ads)} ads available"
)

# Initialize session state for UI control
if "show_ad_manager" not in st.session_state:
    st.session_state.show_ad_manager = False
    
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

st.title("Ad Service Chat")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Add sidebar with conversation info
with st.sidebar:
    st.subheader("Conversation Information")
    st.write(f"Conversation ID: {st.session_state.conversation_id}")
    st.write(f"Message count: {len(st.session_state.messages)}")
    
    # Add debug controls
    st.subheader("Debug Controls")
    show_match_factors = st.checkbox("Show Ad Match Factors", value=True)
    
    # Add specific debug for the ad system
    st.subheader("Ad System Info")
    st.info("Configuration-Driven Ad Matching Active")
    
    # Add a debug section to help troubleshoot matching
    with st.expander("System Information", expanded=True):
        st.markdown("**Active Match Factors:**")
        st.markdown("- Keyword matching")
        st.markdown("- Category matching")
        st.markdown("- Relevance scoring")
        st.markdown("- Configuration-based targeting")
        
        # Show the available ads
        st.markdown("**Available Ads:**")
        for ad in ad_manager.ads:
            st.markdown(f"- {ad.get('title', 'Unknown')}")
        
        # Add config reload button
        if st.button("Reload Ad Configuration"):
            ad_manager.reload_config()
            st.success("Ad configuration reloaded successfully!")
    
    # Add a conversation reset button
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())
        st.rerun()

# Create sidebar with navigation options
with st.sidebar:
    st.title("Ad Service")
    st.write("Chat with AI and see relevant ads.")
    
    # Add a horizontal line for separation
    st.markdown("---")
    
    # Add a link to the Ad Manager
    st.subheader("Admin Tools")
    
    if st.button("🛠️ Open Ad Manager"):
        # Set session state to show Ad Manager UI
        st.session_state.show_ad_manager = True
    
    if st.button("💬 Return to Chat"):
        # Return to chat interface
        st.session_state.show_ad_manager = False
    
    st.markdown("---")
    
    # Add a small footer to the sidebar
    st.caption("Ad Service v1.0")

# Conditional UI based on what should be shown
if st.session_state.show_ad_manager:
    # Show the Ad Manager UI
    render_ad_manager_ui()
else:
    # Show the normal chat interface
    # Handle user input
    if query := st.chat_input("How can I help you today?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # Log the user query
        logger.critical(f"PROCESSING USER QUERY: '{query}'")
        
        try:
            # Initialize start_time for timing the generation
            start_time = time.time()
            
            # Get conversation context from previous messages
            conversation_context = {
                "conversation_id": st.session_state.conversation_id,
                "message_count": len(st.session_state.messages)
            }
            
            # Get conversation history
            conversation_history = (
                st.session_state.messages[-5:] 
                if len(st.session_state.messages) > 0 
                else []
            )
            
            # Process query to find relevant ad
            try:
                # Try to use context-aware ad matching
                logger.critical(
                    f"CALLING CONFIG-DRIVEN AD MANAGER WITH QUERY: '{query}'"
                )
                ad = ad_manager.get_relevant_ad(
                    query=query, 
                    context=conversation_context, 
                    conversation_history=conversation_history
                )
                if ad:
                    match_score = (
                        ad.get('match_factors', {}).get('total_score', 0)
                    )
                    logger.critical(
                        f"MATCHED AD: {ad.get('title')} "
                        f"(Score: {match_score:.2f})"
                    )
                else:
                    logger.critical("NO MATCHING AD FOUND")
            except Exception as e:
                logger.critical(f"Error getting ad: {str(e)}")
                ad = None
            
            # Generate response with OpenAI
            system_msg = (
                "You are a helpful assistant. "
                "Provide direct answers to questions."
            )
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_msg},
                    *[
                        {"role": m["role"], "content": m["content"]} 
                        for m in st.session_state.messages
                    ]
                ]
            )
            generation_time = time.time() - start_time
            assistant_response = response.choices[0].message.content
            
            # Log the model generation
            metrics.log_model_generation(
                query=query,
                response=assistant_response,
                model="gpt-3.5-turbo",
                generation_time=generation_time
            )
            
            # Append ad recommendation if available
            if ad:
                ad_id = ad.get("id", "unknown")
                ad_title = ad.get("title", "")
                ad_description = ad.get("description", "")
                ad_cta = ad.get("call_to_action", "Learn More")
                
                # Format the ad display
                ad_display = (
                    f"\n\n*Recommended for you: **{ad_title}** - "
                    f"{ad_description}* [{ad_cta}]({ad.get('url', '#')})"
                )
                assistant_response += ad_display
                
                # Show match factors if in debug mode
                if show_match_factors and "match_factors" in ad:
                    title = f"Match factors for '{ad_title}'"
                    with st.expander(title, expanded=True):
                        st.json(ad["match_factors"])
                
                # Log the ad impression
                try:
                    relevance_score = 0.5
                    if ("match_factors" in ad and 
                            "total_score" in ad["match_factors"]):
                        relevance_score = ad["match_factors"]["total_score"]
                    
                    metrics.log_ad_impression(
                        query=query,
                        ad_id=ad_id,
                        relevance_score=relevance_score
                    )
                    logger.critical(f"LOGGED AD IMPRESSION: {ad_title}")
                except Exception as e:
                    logger.critical(f"ERROR LOGGING AD IMPRESSION: {str(e)}")
            else:
                logger.critical("NO RELEVANT AD FOUND FOR THIS QUERY")
            
            # Display the assistant response
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
            
            # Add assistant response to chat history
            st.session_state.messages.append(
                {"role": "assistant", "content": assistant_response}
            )
            
        except Exception as e:
            logger.critical(f"ERROR PROCESSING QUERY: {str(e)}")
            metrics.log_ad_event("error", {"error": str(e), "query": query})
            st.error(f"Error: {str(e)}") 