import streamlit as st
import sys
import json
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def load_config():
    """Load the current service configuration"""
    config_path = os.path.join(project_root, "config", "service_config.json")
    try:
        with open(config_path, 'r') as f:
            config_content = f.read().strip()
            return json.loads(config_content)
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")
        return {
            "ad_matcher": {
                "relevance_threshold": 0.7,
                "max_ads_per_response": 3
            },
            "openai": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 150
            },
            "api": {
                "endpoint": "https://api.example.com",
                "key": ""
            },
            "app": {
                "theme": "Light",
                "response_delay_ms": 500,
                "log_level": "INFO"
            },
            "ads": {
                "relevance_threshold": 0.7,
                "max_ads_per_response": 2
            }
        }

def save_config(new_settings):
    """Save the updated service configuration"""
    config_path = os.path.join(project_root, "config", "service_config.json")
    try:
        # Load existing config to preserve other settings
        current_config = load_config()
        
        # Update with new settings
        if "api" in new_settings:
            current_config["api"] = new_settings["api"]
        if "app" in new_settings:
            current_config["app"] = new_settings["app"]
        if "ads" in new_settings:
            current_config["ad_matcher"] = {
                "relevance_threshold": new_settings["ads"]["relevance_threshold"],
                "max_ads_per_response": new_settings["ads"]["max_ads_per_response"]
            }
            current_config["ads"] = new_settings["ads"]
        
        # Write the updated config
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(current_config, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False

def main():
    st.title("Settings")
    
    # Load the current configuration
    config = load_config()
    
    with st.form("settings_form"):
        st.subheader("Application Settings")
        
        # API Configuration
        st.subheader("API Configuration")
        api_key = st.text_input("API Key", 
                              value=config.get("api", {}).get("key", ""),
                              type="password")
        api_endpoint = st.text_input("API Endpoint", 
                                  value=config.get("api", {}).get("endpoint", "https://api.example.com"))
        
        # OpenAI Settings
        st.subheader("OpenAI Settings")
        model = st.selectbox(
            "Model",
            options=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            index=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"].index(
                config.get("openai", {}).get("model", "gpt-3.5-turbo")
            )
        )
        temperature = st.slider(
            "Temperature",
            0.0, 1.0,
            value=float(config.get("openai", {}).get("temperature", 0.7)),
            step=0.1
        )
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=50, max_value=4000,
            value=int(config.get("openai", {}).get("max_tokens", 150))
        )
        
        # General Settings
        st.subheader("General Settings")
        theme = st.selectbox("Theme", 
                          options=["Light", "Dark"],
                          index=0 if config.get("app", {}).get("theme", "Light") == "Light" else 1)
        
        response_delay = st.slider("Response Delay (ms)", 
                                0, 1000, 
                                value=int(config.get("app", {}).get("response_delay_ms", 500)))
        
        log_level = st.selectbox("Log Level", 
                              options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                              index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                                  config.get("app", {}).get("log_level", "INFO")))
        
        # Ad Settings
        st.subheader("Ad Settings")
        relevance_threshold = st.slider("Relevance Threshold", 
                                     0.0, 1.0, 
                                     value=float(config.get("ad_matcher", {}).get("relevance_threshold", 0.7)),
                                     step=0.05)
        
        max_ads = st.number_input("Maximum Ads Per Response", 
                               min_value=0, max_value=10, 
                               value=int(config.get("ad_matcher", {}).get("max_ads_per_response", 2)))
        
        # Submit button
        submitted = st.form_submit_button("Save Settings")
        if submitted:
            # Update the configuration
            new_config = {
                "api": {
                    "endpoint": api_endpoint,
                    "key": api_key
                },
                "openai": {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                "app": {
                    "theme": theme,
                    "response_delay_ms": response_delay,
                    "log_level": log_level
                },
                "ads": {
                    "relevance_threshold": relevance_threshold,
                    "max_ads_per_response": max_ads
                }
            }
            
            if save_config(new_config):
                st.success("Settings saved successfully! Please restart the application for changes to take effect.")
            else:
                st.error("Failed to save settings.")
    
    # Add a section to show the current configuration
    with st.expander("View Current Configuration"):
        st.json(config)

if __name__ == "__main__":
    main()
