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
    try:
        import ad_service
        st.write("ad_service package is already imported")
        
        # Import all contents from the main module
        # We need to prevent the main module from calling set_page_config again
        import ad_service.gui.main as main_module
        
        # Delete the set_page_config function to prevent it from being called again
        if hasattr(main_module, 'st') and hasattr(main_module.st, 'set_page_config'):
            # Create a dummy function that does nothing
            def dummy_set_page_config(*args, **kwargs):
                pass
            
            # Replace the real function with our dummy one
            original_set_page_config = main_module.st.set_page_config
            main_module.st.set_page_config = dummy_set_page_config
            
        # Run the core logic from main module
        # Exposing all the variables and functions from main
        for name in dir(main_module):
            if not name.startswith('__'):
                globals()[name] = getattr(main_module, name)
                
        # Run any initialization functions from main if they exist
        if hasattr(main_module, 'initialize_app'):
            main_module.initialize_app()
            
        # Return control to the main module's execution flow
        if hasattr(main_module, 'run_app'):
            main_module.run_app()
            
    except ImportError as e:
        st.error(f"Error importing modules: {e}")
        show_debug_info()
        try:
            # Try to run the main.py directly as fallback
            from ad_service.gui.main import *
        except ImportError as e2:
            st.error(f"Error importing main module: {e2}")
            try:
                # Final fallback to just the Ad Manager UI
                from ad_service.gui.ad_manager_ui import render_ad_manager_ui
                render_ad_manager_ui()
            except ImportError as e3:
                st.error(f"Error importing ad_manager_ui: {e3}")
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