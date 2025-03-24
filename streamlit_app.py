"""
Streamlit Cloud entry point for Ad Service app
"""
import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app's main module
from ad_service.gui.main import *

# The imports above should have executed the Streamlit app code 