import json
import os

def fix_config_file():
    """Fix the configuration file by completely rewriting it with a single valid JSON object"""
    config_path = 'ad_service/config/service_config.json'
    
    # Create a clean configuration with all required sections
    clean_config = {
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
    
    try:
        # Write the clean configuration to the file
        with open(config_path, 'w') as f:
            json.dump(clean_config, f, indent=4)
        
        print("File completely rewritten with a clean configuration")
        
        # Verify the cleaned file
        with open(config_path, 'r') as f:
            new_content = f.read()
        
        print(f"New content length: {len(new_content)} characters")
        
        try:
            json.loads(new_content)
            print("Verification: New content is valid JSON")
            return True
        except json.JSONDecodeError as e:
            print(f"Verification failed: {e}")
            return False
    
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_config_file()
    print(f"Configuration file fix {'succeeded' if success else 'failed'}") 