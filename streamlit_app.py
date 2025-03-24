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
        
        # Import the main module
        import ad_service.gui.main as main_module
        
        # Delete the set_page_config function to prevent it from being called again
        if hasattr(main_module, 'st') and hasattr(main_module.st, 'set_page_config'):
            # Create a dummy function that does nothing
            def dummy_set_page_config(*args, **kwargs):
                pass
            
            # Replace the real function with our dummy one
            main_module.st.set_page_config = dummy_set_page_config
        
        # Execute the main module's content
        # This will run all the top-level code in main.py
        # Due to how the main.py is structured, this should work to display the UI
        try:
            # Run any initialization functions from main if they exist
            if hasattr(main_module, 'initialize_app'):
                main_module.initialize_app()
                
            # Call the main UI rendering function if it exists
            if hasattr(main_module, 'run_app'):
                main_module.run_app()
            else:
                # If main module doesn't have specific entry points, run what we know exists
                # Try to access known functions/variables from the main module
                if hasattr(main_module, 'render_chat_interface'):
                    main_module.render_chat_interface()
                elif hasattr(main_module, 'render_ad_manager_ui'):
                    main_module.render_ad_manager_ui()
        except Exception as app_error:
            st.error(f"Error running main module: {app_error}")
            
    except ImportError as e:
        st.error(f"Error importing modules: {e}")
        show_debug_info()
        try:
            # Final fallback to just the Ad Manager UI
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "ad_manager_ui", 
                os.path.join(current_dir, "ad_service/gui/ad_manager_ui.py")
            )
            if spec and spec.loader:
                ad_manager = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ad_manager)
                if hasattr(ad_manager, 'render_ad_manager_ui'):
                    ad_manager.render_ad_manager_ui()
            else:
                st.error("Could not load ad_manager_ui module")
        except Exception as e3:
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