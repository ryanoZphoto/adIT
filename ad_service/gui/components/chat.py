"""
Chat interface component
"""
import streamlit as st
from ad_service.analytics.metrics_collector import MetricsCollector
from ad_service.gui.components.debug import DebugPanel

class ChatInterface:
    @staticmethod
    def render(session_mgr):
        # Initialize chat history if not exists
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("How can I help you?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # Process through session manager
                response = session_mgr.process_chat_message(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
            except Exception as e:
                st.error(f"Error processing message: {str(e)}")

        # Debug panel
        if st.session_state.get('debug_mode', False):
            DebugPanel.render()        
