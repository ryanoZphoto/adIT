import streamlit as st
import os
import sys
import httpx
from openai import OpenAI

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# The page config has been moved to the main streamlit_app.py file
# to avoid multiple st.set_page_config() calls

def render_chat_interface():
    st.title("Ad Service Chat Interface")
    
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
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know about?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
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
                    
                    # Call the OpenAI API
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant for an ad service. Provide informative and concise responses about advertising, marketing, and related topics."},
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

# Rename the main function to render_chat_interface to match import in streamlit_app.py
if __name__ == "__main__":
    render_chat_interface() 