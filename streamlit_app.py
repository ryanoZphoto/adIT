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

# Now define the main app logic in a function
def main():
    # First show debug info
    show_debug_info()
    
    # Try to install the package in development mode if it's not installed
    try:
        import ad_service
        st.write("ad_service package is already imported")
        
        # Now run the actual application
        try:
            # Clear previous output before running main app
            container = st.empty()
            with container:
                # Import and run the main functionality
                try:
                    # First try ad_manager_ui (safer option)
                    from ad_service.gui.ad_manager_ui import render_ad_manager_ui
                    render_ad_manager_ui()
                except ImportError as e:
                    st.error(f"Error importing ad_manager_ui: {e}")
                    if os.path.exists('ad_service/gui'):
                        st.write(f"ad_service/gui contents: {os.listdir('ad_service/gui')}")
        except ImportError as e:
            st.error(f"Error importing modules: {e}")
    except ImportError:
        st.write("ad_service package not found, importing directly")
        try:
            # Try to run the ad manager UI directly
            from ad_service.gui.ad_manager_ui import render_ad_manager_ui
            render_ad_manager_ui()
        except ImportError as e:
            st.error(f"Error importing ad_service: {e}")
            st.error("Directory structure:")
            if os.path.exists('ad_service'):
                st.write(f"ad_service contents: {os.listdir('ad_service')}")
                if os.path.exists('ad_service/gui'):
                    st.write(f"ad_service/gui contents: {os.listdir('ad_service/gui')}")
            else:
                st.error("ad_service directory not found!")

# Run the main app
if __name__ == "__main__":
    main() 