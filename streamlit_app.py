"""
Streamlit Cloud entry point for Ad Service app
"""
import os
import sys
import streamlit as st

# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="Ad Service Chat",
    page_icon="💬",
    layout="wide"
)

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Create a function for the debug info so we don't run Streamlit commands at import time
def show_debug_info():
    st.write(f"Python path: {sys.path}")
    st.write(f"Current directory: {current_dir}")
    st.write(f"Directory contents: {os.listdir(current_dir)}")

# Import necessary dependencies directly
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create the main application
def main():
    try:
        # Import the necessary components directly
        # Instead of importing the problematic main.py module
        
        # First check if ad_service package is available
        import ad_service
        st.write("ad_service package is already imported")
        
        # Define sidebar for navigation
        st.sidebar.title("Ad Service")
        app_mode = st.sidebar.selectbox(
            "Choose Mode:",
            ["Chat Interface", "Ad Manager"]
        )
        
        if app_mode == "Chat Interface":
            # Import chat interface directly
            try:
                from ad_service.gui.chat_interface import render_chat_interface
                render_chat_interface()
            except ImportError as e:
                st.error(f"Error importing chat interface: {e}")
                st.warning("Chat interface not available. Please check your API keys.")
                # Fall back to Ad Manager
                from ad_service.gui.ad_manager_ui import render_ad_manager_ui
                render_ad_manager_ui()
        else:
            # Import Ad Manager UI directly
            from ad_service.gui.ad_manager_ui import render_ad_manager_ui
            render_ad_manager_ui()
            
    except ImportError as e:
        st.error(f"Error importing ad_service package: {e}")
        show_debug_info()
        st.error("Directory structure:")
        if os.path.exists('ad_service'):
            st.write(f"ad_service contents: {os.listdir('ad_service')}")
            if os.path.exists('ad_service/gui'):
                st.write(f"ad_service/gui contents: {os.listdir('ad_service/gui')}")
        else:
            st.error("ad_service directory not found!")

# Run the app
if __name__ == "__main__":
    main() 