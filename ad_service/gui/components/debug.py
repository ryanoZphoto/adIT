import streamlit as st

class DebugPanel:
    @staticmethod
    def render():
        if st.session_state.get('debug_mode', False):
            with st.expander("Debug Information"):
                st.write("Session State:", st.session_state)
                st.write("API Key Status:", "Available" if st.session_state.get('OPENAI_API_KEY') else "Missing")
                if st.button("Clear Chat History"):
                    st.session_state.messages = []
                    st.experimental_rerun()