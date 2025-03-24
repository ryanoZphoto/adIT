"""
Streamlit Cloud entry point for Ad Service app
"""
import os
import sys
import streamlit as st

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Print for debugging
st.write(f"Python path: {sys.path}")
st.write(f"Current directory: {current_dir}")
st.write(f"Directory contents: {os.listdir(current_dir)}")

# Try to install the package in development mode if it's not installed
try:
    import ad_service
    st.write("ad_service package is already imported")
    
    # Now run the actual application - using main module instead of just ad_manager_ui
    try:
        # Clear previous output
        st.empty()
        
        # Import and run the main application that includes both chat and ad manager
        from ad_service.gui.main import *
        # The main module will handle UI routing between chat and ad manager
    except ImportError as e:
        st.error(f"Error importing main module: {e}")
        st.error("Falling back to ad_manager_ui module")
        try:
            from ad_service.gui.ad_manager_ui import render_ad_manager_ui
            render_ad_manager_ui()
        except ImportError as e2:
            st.error(f"Error importing ad_manager_ui: {e2}")
            if os.path.exists('ad_service/gui'):
                st.write(f"ad_service/gui contents: {os.listdir('ad_service/gui')}")
except ImportError:
    st.write("ad_service package not found, importing directly")
    try:
        # Try to run the main module directly
        from ad_service.gui.main import *
    except ImportError as e:
        st.error(f"Error importing ad_service: {e}")
        st.error("Directory structure:")
        if os.path.exists('ad_service'):
            st.write(f"ad_service contents: {os.listdir('ad_service')}")
            if os.path.exists('ad_service/gui'):
                st.write(f"ad_service/gui contents: {os.listdir('ad_service/gui')}")
        else:
            st.error("ad_service directory not found!") 