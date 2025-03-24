"""
Streamlit application entry point
This script runs the Ad Service application on Streamlit.
"""

import os
import sys
import traceback
import logging
import streamlit as st

# Set page config at the very beginning before any other Streamlit commands
st.set_page_config(
    page_title="Ad Service",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

def show_debug_info():
    """Display debug information about the environment."""
    st.sidebar.title("Debug Info")
    st.sidebar.write(f"Python executable: {sys.executable}")
    st.sidebar.write(f"Python version: {sys.version}")
    st.sidebar.write(f"System path: {sys.path}")
    st.sidebar.write(f"Current directory: {os.getcwd()}")
    st.sidebar.write(f"Directory contents: {os.listdir('.')}")
    
    try:
        import ad_service
        st.sidebar.write(f"ad_service version: {ad_service.__version__}")
        st.sidebar.write(f"ad_service path: {ad_service.__path__}")
    except (ImportError, AttributeError) as e:
        st.sidebar.error(f"Error getting ad_service info: {str(e)}")

def main():
    """Main application entry point"""
    try:
        # Import components directly
        from ad_service.gui.ad_manager_ui import AdManagerUI
        from ad_service.gui.chat_interface import ChatInterface
        
        # Set up the sidebar for navigation
        st.sidebar.title("Navigation")
        app_mode = st.sidebar.radio("Go to", ["Chat Interface", "Ad Manager"])
        
        # Initialize session state for storing data between reruns
        if "history" not in st.session_state:
            st.session_state.history = []
        
        if "ad_manager_initialized" not in st.session_state:
            st.session_state.ad_manager_initialized = False
            
        # Show the selected component based on user choice
        if app_mode == "Chat Interface":
            # Initialize and display the chat interface
            chat_interface = ChatInterface()
            chat_interface.display()
        else:
            # Initialize and display the ad manager UI
            ad_manager = AdManagerUI()
            ad_manager.display()
            
    except ImportError as e:
        st.error(f"Error importing required modules: {str(e)}")
        st.error(traceback.format_exc())
        show_debug_info()
        
        # Try a fallback to just the Ad Manager UI if available
        try:
            from ad_service.gui.ad_manager_ui import AdManagerUI
            st.warning("Chat Interface not available. Displaying Ad Manager UI only.")
            ad_manager = AdManagerUI()
            ad_manager.display()
        except ImportError:
            st.error("Failed to load the Ad Manager UI component.")
            show_debug_info()
            
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.error(traceback.format_exc())
        show_debug_info()

if __name__ == "__main__":
    main() 