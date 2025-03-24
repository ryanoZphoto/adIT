import streamlit as st
import os
import sys
import json
from datetime import datetime

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Set page config
st.set_page_config(
    page_title="Ad Service Manager",
    page_icon="🎯",
    layout="wide"
)

def load_ads():
    """Load existing ads from the ads.json file."""
    ads_file = os.path.join(parent_dir, 'data', 'ads.json')
    if os.path.exists(ads_file):
        with open(ads_file, 'r') as f:
            return json.load(f)
    return {"ads": []}

def save_ad(ad_data):
    """Save a new ad to the ads.json file."""
    ads_file = os.path.join(parent_dir, 'data', 'ads.json')
    ads = load_ads()
    
    # Add timestamp and ID
    ad_data['created_at'] = datetime.now().isoformat()
    ad_data['id'] = f"ad_{len(ads['ads']) + 1}"
    
    ads['ads'].append(ad_data)
    
    with open(ads_file, 'w') as f:
        json.dump(ads, f, indent=2)

def main():
    st.title("Ad Service Manager")
    
    tab1, tab2 = st.tabs(["Create Ad", "View Ads"])
    
    with tab1:
        st.header("Create New Ad")
        
        with st.form("new_ad_form"):
            company_id = st.text_input("Company ID")
            ad_title = st.text_input("Ad Title")
            ad_text = st.text_area("Ad Text")
            keywords = st.text_input("Keywords (comma-separated)")
            target_url = st.text_input("Target URL")
            
            submitted = st.form_submit_button("Create Ad")
            
            if submitted:
                if not all([company_id, ad_title, ad_text, keywords, target_url]):
                    st.error("All fields are required!")
                else:
                    ad_data = {
                        "company_id": company_id,
                        "title": ad_title,
                        "text": ad_text,
                        "keywords": [k.strip() for k in keywords.split(",")],
                        "target_url": target_url,
                        "status": "active"
                    }
                    
                    try:
                        save_ad(ad_data)
                        st.success("Ad created successfully!")
                    except Exception as e:
                        st.error(f"Error creating ad: {str(e)}")
    
    with tab2:
        st.header("Existing Ads")
        ads = load_ads()
        
        if not ads['ads']:
            st.info("No ads found. Create your first ad using the Create Ad tab!")
        else:
            for ad in ads['ads']:
                with st.expander(f"{ad['title']} ({ad['id']})"):
                    st.write("**Company ID:**", ad['company_id'])
                    st.write("**Text:**", ad['text'])
                    st.write("**Keywords:**", ", ".join(ad['keywords']))
                    st.write("**Target URL:**", ad['target_url'])
                    st.write("**Status:**", ad['status'])
                    st.write("**Created:**", ad['created_at'])

if __name__ == "__main__":
    main() 