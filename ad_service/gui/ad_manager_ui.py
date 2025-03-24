import streamlit as st
import json
import os
import logging
import pandas as pd
import datetime
import uuid
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_IMAGE_URL = "https://via.placeholder.com/300x200?text=Ad+Image"
DEFAULT_TARGET_URL = "https://example.com/landing"
DEFAULT_CTA = "Learn More"

def load_ad_config(config_path=None) -> Dict[str, Any]:
    """Load the ad configuration from the JSON file."""
    if config_path is None:
        # Use default path relative to project root
        config_path = Path(__file__).parent.parent / "data" / "ad_config.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading ad configuration: {str(e)}")
        # Return a default configuration if loading fails
        return {
            "ads": [], 
            "system_config": {
                "default_relevance_threshold": 0.3,
                "max_ads_per_query": 3,
                "match_weights": {
                    "keyword": 0.7,
                    "category": 0.3
                }
            }
        }

def save_ad_config(config: Dict[str, Any], config_path=None) -> bool:
    """Save the ad configuration to the JSON file."""
    if config_path is None:
        # Use default path relative to project root
        config_path = Path(__file__).parent.parent / "data" / "ad_config.json"

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # Format the JSON with proper indentation for readability
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Ad configuration saved successfully to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving ad configuration: {str(e)}")
        return False

def get_next_ad_id(ads: List[Dict[str, Any]]) -> str:
    """Generate a unique ID for a new ad."""
    if not ads:
        return "ad-1"

    # Extract numeric parts of IDs
    existing_ids = []
    for ad in ads:
        ad_id = ad.get("id", "")
        if ad_id.startswith("ad-"):
            try:
                num = int(ad_id.split("-")[1])
                existing_ids.append(num)
            except (ValueError, IndexError):
                pass
    
    # Return next number in sequence
    if existing_ids:
        return f"ad-{max(existing_ids) + 1}"
    return "ad-1"

def format_keywords_for_display(keywords: List[str]) -> str:
    """Format a list of keywords for display in the UI."""
    if not keywords:
        return "None"
    
    return ", ".join(keywords)

def create_ad_preview(ad: Dict[str, Any]) -> None:
    """Create a visual preview of how the ad might appear."""
    # Create a styled container for the ad preview
    with st.container():
        st.markdown("### Ad Preview")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display the ad image
            st.image(
                ad.get("image_url", DEFAULT_IMAGE_URL),
                caption="Ad Image",
                use_column_width=True
            )
        
        with col2:
            # Display the ad content
            st.markdown(f"#### {ad.get('title', 'Ad Title')}")
            st.markdown(f"*{ad.get('description', 'Ad description would appear here.')}*")
            
            # Simulate a button for the call to action
            st.markdown(
                f"""
                <div style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;">
                    {ad.get('cta', DEFAULT_CTA)}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Display the target URL
            st.caption(f"Links to: {ad.get('target_url', DEFAULT_TARGET_URL)}")

def simulate_ad_performance(ad_id: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Simulate ad performance metrics for demonstration purposes.
    In a real application, this would fetch actual performance data.
    """
    # Create date range for the last 30 days
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate random metrics
    np.random.seed(hash(ad_id) % 10000)  # Use ad_id as seed for consistent randomness per ad
    
    impressions = np.random.randint(50, 500, size=len(date_range))
    clicks = np.random.randint(5, min(50, max(impressions) // 5), size=len(date_range))
    # Ensure clicks are always less than impressions
    clicks = np.minimum(clicks, impressions * 0.2)
    
    # Calculate CTR
    ctr = clicks / impressions * 100
    
    # Create DataFrame
    data = {
        'date': date_range,
        'impressions': impressions,
        'clicks': clicks,
        'ctr': ctr
    }
    df = pd.DataFrame(data)
    
    # Calculate summary metrics
    summary = {
        'total_impressions': int(df['impressions'].sum()),
        'total_clicks': int(df['clicks'].sum()),
        'avg_ctr': float(df['ctr'].mean()),
        'best_day': df.loc[df['clicks'].idxmax(), 'date'].strftime('%Y-%m-%d'),
        'best_day_clicks': int(df.loc[df['clicks'].idxmax(), 'clicks'])
    }
    
    return df, summary

def plot_ad_performance(df: pd.DataFrame, metrics: List[str]) -> None:
    """Generate a performance plot for the selected metrics."""
    fig, ax = plt.subplots(figsize=(10, 4))
    
    for metric in metrics:
        ax.plot(df['date'], df[metric], label=metric.capitalize())
    
    ax.set_title('Ad Performance Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Count')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Adjust layout to make room for x-labels
    plt.tight_layout()
    
    st.pyplot(fig)

def display_ad_analytics(ad: Dict[str, Any]) -> None:
    """Display analytics for a given ad."""
    st.subheader("📊 Ad Performance Analytics")
    
    # Get performance data
    df, metrics_summary = simulate_ad_performance(ad['id'])
    
    # Allow user to select which metrics to view
    metrics = st.multiselect(
        "Select metrics to display:", 
        ["Impressions", "Clicks", "CTR"],
        default=["Impressions", "Clicks"],
        key=f"metrics_select_{ad['id']}"  # Add unique key based on ad ID
    )
    
    if metrics:
        plot_ad_performance(df, metrics)
    else:
        st.warning("Please select at least one metric to display the chart.")

def create_new_ad_form(ads: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Display the form for creating a new ad and process the submission."""
    ad_added = False
    added_title = ""
    
    with st.form("new_ad_form"):
        st.markdown("### Basic Information")
        
        # Basic ad information
        title = st.text_input("Ad Title", value="", help="The main headline of your ad")
        
        description = st.text_area(
            "Ad Description", 
            value="", 
            help="Detailed description of your ad"
        )
        
        # Layout in columns for more compact form
        col1, col2 = st.columns(2)
        
        with col1:
            cta = st.text_input(
                "Call to Action", 
                value=DEFAULT_CTA, 
                help="Button text (e.g., 'Shop Now')"
            )
            brand = st.text_input(
                "Brand Name",
                value="",
                help="Your brand or company name"
            )
        
        with col2:
            campaign = st.text_input(
                "Campaign", 
                value="", 
                help="Campaign this ad belongs to"
            )
            advertiser_id = st.text_input(
                "Advertiser ID",
                value="",
                help="Your unique advertiser identifier"
            )
        
        st.markdown("### URLs and Media")
        
        # URLs and media
        col1, col2 = st.columns(2)
        
        with col1:
            image_url = st.text_input(
                "Image URL", 
                value=DEFAULT_IMAGE_URL, 
                help="URL to the ad image"
            )
            display_format = st.selectbox(
                "Display Format",
                options=["text", "image", "rich_media"],
                help="How the ad should be displayed"
            )
        
        with col2:
            target_url = st.text_input(
                "Target URL", 
                value=DEFAULT_TARGET_URL, 
                help="Landing page URL"
            )
            tracking_pixel = st.text_input(
                "Tracking Pixel URL",
                value="",
                help="Optional URL for impression tracking"
            )
        
        st.markdown("### Targeting")
        
        # Keywords and categories with examples
        col1, col2 = st.columns(2)
        
        with col1:
            keywords_input = st.text_area(
                "Keywords", 
                value="",
                help="Words that should trigger this ad (one per line). Include variations and related terms."
            )
            
            st.caption("Example keywords:\nrunning shoes\nrunners\njogging footwear\nmarathon training")
        
        with col2:
            categories_input = st.text_area(
                "Categories", 
                value="",
                help="Categories this ad belongs to (one per line). Be specific and hierarchical."
            )
            
            st.caption("Example categories:\nsports/running\nfitness/footwear\nathletic/performance")
        
        st.markdown("### Intent Targeting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            target_intents = st.multiselect(
                "Target User Intents",
                options=[
                    "purchase_intent",
                    "research_intent",
                    "price_check",
                    "comparison",
                    "information",
                    "support"
                ],
                default=["purchase_intent"],
                help="What user intentions should trigger this ad"
            )
        
        with col2:
            target_preferences = st.multiselect(
                "Target User Preferences",
                options=[
                    "budget_conscious",
                    "premium",
                    "performance",
                    "quality",
                    "convenience"
                ],
                help="What user preferences this ad caters to"
            )
        
        st.markdown("### Advanced Settings")
        
        # Advanced settings in expandable section
        with st.expander("Advanced Settings", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                priority = st.slider(
                    "Priority", 
                    min_value=1, 
                    max_value=10, 
                    value=5,
                    help="Higher priority ads shown more often when multiple ads match"
                )
                
                bid_amount = st.number_input(
                    "Bid Amount ($)",
                    min_value=0.01,
                    max_value=1000.0,
                    value=1.0,
                    step=0.01,
                    help="Maximum amount to pay per click"
                )
            
            with col2:
                active = st.checkbox(
                    "Active", 
                    value=True,
                    help="Inactive ads will not be shown"
                )
                
                daily_budget = st.number_input(
                    "Daily Budget ($)",
                    min_value=0.0,
                    value=50.0,
                    step=5.0,
                    help="Maximum daily spend"
                )
            
            with col3:
                match_weights = {
                    "keyword_match": st.slider(
                        "Keyword Match Weight",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.4,
                        help="Importance of keyword matches"
                    ),
                    "category_match": st.slider(
                        "Category Match Weight",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.3,
                        help="Importance of category matches"
                    ),
                    "intent_match": st.slider(
                        "Intent Match Weight",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.3,
                        help="Importance of intent matches"
                    )
                }
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start Date", 
                    value=datetime.datetime.now().date(),
                    help="When to start showing this ad"
                )
            
            with col2:
                end_date = st.date_input(
                    "End Date", 
                    value=datetime.datetime.now().date() + datetime.timedelta(days=30),
                    help="When to stop showing this ad"
                )
            
            # Targeting restrictions
            st.subheader("Targeting Restrictions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                frequency_cap = st.number_input(
                    "Frequency Cap",
                    min_value=0,
                    value=3,
                    help="Maximum times to show ad to same user per day"
                )
                
                excluded_keywords = st.text_area(
                    "Excluded Keywords",
                    value="",
                    help="Keywords that should NOT trigger this ad (one per line)"
                )
            
            with col2:
                min_relevance_score = st.slider(
                    "Minimum Relevance Score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    help="Minimum relevance score required to show ad"
                )
                
                excluded_categories = st.text_area(
                    "Excluded Categories",
                    value="",
                    help="Categories where this ad should NOT appear (one per line)"
                )
        
        # Submit button
        submitted = st.form_submit_button("Add Ad")
        
        if submitted:
            try:
                # Parse inputs
                keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
                categories = [c.strip() for c in categories_input.split("\n") if c.strip()]
                excluded_kw = [k.strip() for k in excluded_keywords.split("\n") if k.strip()]
                excluded_cat = [c.strip() for c in excluded_categories.split("\n") if c.strip()]
                
                # Validate inputs
                if not title:
                    st.error("Ad title is required")
                elif not description:
                    st.error("Ad description is required")
                elif not keywords:
                    st.error("At least one keyword is required")
                elif start_date > end_date:
                    st.error("End date must be after start date")
                else:
                    # Create new ad object
                    new_ad = {
                        "id": get_next_ad_id(ads),
                        "title": title,
                        "description": description,
                        "brand": brand,
                        "advertiser_id": advertiser_id,
                        "cta": cta,
                        "campaign": campaign,
                        "image_url": image_url,
                        "target_url": target_url,
                        "tracking_pixel": tracking_pixel,
                        "display_format": display_format,
                        "keywords": keywords,
                        "categories": categories,
                        "target_intents": target_intents,
                        "target_preferences": target_preferences,
                        "excluded_keywords": excluded_kw,
                        "excluded_categories": excluded_cat,
                        "priority": priority,
                        "bid_amount": bid_amount,
                        "daily_budget": daily_budget,
                        "match_weights": match_weights,
                        "min_relevance_score": min_relevance_score,
                        "frequency_cap": frequency_cap,
                        "active": active,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "created_at": datetime.datetime.now().isoformat(),
                        "updated_at": datetime.datetime.now().isoformat(),
                        "performance": {
                            "impressions": 0,
                            "clicks": 0,
                            "conversions": 0,
                            "ctr": 0.0,
                            "conversion_rate": 0.0,
                            "quality_score": 0.0,
                            "avg_position": 0.0
                        }
                    }
                    
                    # Preview the ad
                    create_ad_preview(new_ad)
                    
                    # Add to configuration if confirmed
                    if st.button("Confirm and Add Ad"):
                        ads.append(new_ad)
                        config = load_ad_config()
                        config["ads"] = ads
                        
                        if save_ad_config(config):
                            st.success(f"Ad '{title}' added successfully!")
                            st.info("The ad will be available for matching after reloading.")
                            ad_added = True
                            added_title = title
                        else:
                            st.error("Failed to save ad configuration")
            
            except Exception as e:
                st.error(f"Error adding ad: {str(e)}")
                logger.exception("Error adding ad")
    
    return ad_added, added_title

def edit_ad_form(ad: Dict[str, Any], ads: List[Dict[str, Any]]) -> bool:
    """Display a form for editing an existing ad and process the submission."""
    updated = False
    
    with st.form(f"edit_ad_form_{ad.get('id', '')}"):
        st.markdown("### Basic Information")
        
        # Basic ad information
        title = st.text_input("Ad Title", value=ad.get("title", ""), help="The main headline of your ad")
        
        description = st.text_area(
            "Ad Description", 
            value=ad.get("description", ""), 
            help="Detailed description of your ad"
        )
        
        # Layout in columns for more compact form
        col1, col2 = st.columns(2)
        
        with col1:
            cta = st.text_input(
                "Call to Action", 
                value=ad.get("cta", DEFAULT_CTA), 
                help="Button text (e.g., 'Shop Now')"
            )
        
        with col2:
            # Add a campaign field
            campaign = st.text_input(
                "Campaign", 
                value=ad.get("campaign", ""), 
                help="Optional campaign this ad belongs to"
            )
        
        st.markdown("### URLs")
        
        # URLs
        col1, col2 = st.columns(2)
        
        with col1:
            image_url = st.text_input(
                "Image URL", 
                value=ad.get("image_url", DEFAULT_IMAGE_URL), 
                help="URL to the ad image"
            )
        
        with col2:
            target_url = st.text_input(
                "Target URL", 
                value=ad.get("target_url", DEFAULT_TARGET_URL), 
                help="Landing page URL"
            )
        
        st.markdown("### Targeting")
        
        # Keywords and categories
        col1, col2 = st.columns(2)
        
        with col1:
            keywords_input = st.text_input(
                "Keywords (comma-separated)", 
                value=format_keywords_for_display(ad.get("keywords", [])),
                help="Words that should trigger this ad when in user queries"
            )
        
        with col2:
            categories_input = st.text_input(
                "Categories (comma-separated)", 
                value=format_keywords_for_display(ad.get("categories", [])),
                help="Higher-level groupings this ad belongs to"
            )
        
        st.markdown("### Advanced Settings")
        
        # Advanced settings in expandable section
        with st.expander("Advanced Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                priority = st.slider(
                    "Priority", 
                    min_value=1, 
                    max_value=10, 
                    value=ad.get("priority", 5),
                    help="Higher priority ads will be shown more often when multiple ads match"
                )
            
            with col2:
                active = st.checkbox(
                    "Active", 
                    value=ad.get("active", True),
                    help="Inactive ads will not be shown to users"
                )
                
            # Get current start and end dates
            try:
                current_start_date = datetime.date.fromisoformat(ad.get("start_date", datetime.datetime.now().date().isoformat()))
            except (ValueError, TypeError):
                current_start_date = datetime.datetime.now().date()
                
            try:
                current_end_date = datetime.date.fromisoformat(ad.get("end_date", (datetime.datetime.now().date() + datetime.timedelta(days=30)).isoformat()))
            except (ValueError, TypeError):
                current_end_date = datetime.datetime.now().date() + datetime.timedelta(days=30)
                
            start_date = st.date_input(
                "Start Date", 
                value=current_start_date,
                help="When this ad should start being shown"
            )
            
            end_date = st.date_input(
                "End Date", 
                value=current_end_date,
                help="When this ad should stop being shown"
            )
        
        # Submit button
        submitted = st.form_submit_button("Update Ad")
        
        if submitted:
            # Process form submission
            try:
                # Parse keywords and categories
                keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
                categories = [c.strip() for c in categories_input.split(",") if c.strip()]
                
                # Validate inputs
                if not title:
                    st.error("Ad title is required")
                elif not description:
                    st.error("Ad description is required")
                elif not keywords:
                    st.error("At least one keyword is required")
                elif start_date > end_date:
                    st.error("End date must be after start date")
                else:
                    # Update ad object
                    updated_ad = {
                        "id": ad.get("id", ""),
                        "title": title,
                        "description": description,
                        "cta": cta,
                        "campaign": campaign if campaign else None,
                        "image_url": image_url,
                        "target_url": target_url,
                        "keywords": keywords,
                        "categories": categories,
                        "priority": priority,
                        "active": active,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "created_at": ad.get("created_at", datetime.datetime.now().isoformat()),
                        "updated_at": datetime.datetime.now().isoformat()
                    }
                    
                    # Preview the updated ad
                    create_ad_preview(updated_ad)
                    
                    # Update the ad if confirmed
                    if st.button("Confirm and Update Ad"):
                        # Find and replace the ad in the list
                        for i, existing_ad in enumerate(ads):
                            if existing_ad.get("id") == ad.get("id"):
                                ads[i] = updated_ad
                                break
                        
                        config = load_ad_config()
                        config["ads"] = ads
                        
                        # Save updated configuration
                        if save_ad_config(config):
                            st.success(f"Ad '{title}' updated successfully!")
                            st.info("The updated ad will be available after reloading.")
                            updated = True
                        else:
                            st.error("Failed to save ad configuration")
            
            except Exception as e:
                st.error(f"Error updating ad: {str(e)}")
                logger.exception("Error updating ad")
    
    return updated

def render_dashboard(ads: List[Dict[str, Any]]) -> None:
    """Render a dashboard overview of all ads."""
    st.header("Ad Dashboard")
    
    # Create some key metrics
    active_ads = sum(1 for ad in ads if ad.get("active", True))
    inactive_ads = len(ads) - active_ads
    unique_keywords = set()
    unique_categories = set()
    campaigns = set()
    
    for ad in ads:
        unique_keywords.update(ad.get("keywords", []))
        unique_categories.update(ad.get("categories", []))
        if ad.get("campaign"):
            campaigns.add(ad.get("campaign"))
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ads", len(ads))
    
    with col2:
        st.metric("Active Ads", active_ads)
    
    with col3:
        st.metric("Unique Keywords", len(unique_keywords))
    
    with col4:
        st.metric("Campaigns", len(campaigns))
    
    # Create and display some charts
    if ads:
        st.subheader("Ad Status")
        
        # Create a pie chart for active vs inactive ads
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(
            [active_ads, inactive_ads],
            labels=['Active', 'Inactive'],
            autopct='%1.1f%%',
            startangle=90,
            colors=['#4CAF50', '#F44336']
        )
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        st.pyplot(fig)
        
        # Display campaigns if any exist
        if campaigns:
            st.subheader("Ads by Campaign")
            
            # Count ads per campaign
            campaign_counts = {}
            for ad in ads:
                campaign = ad.get("campaign", "No Campaign")
                if not campaign:
                    campaign = "No Campaign"
                campaign_counts[campaign] = campaign_counts.get(campaign, 0) + 1
            
            # Create a bar chart
            fig, ax = plt.subplots(figsize=(10, 4))
            campaigns = list(campaign_counts.keys())
            counts = list(campaign_counts.values())
            
            ax.bar(campaigns, counts, color='#2196F3')
            ax.set_xlabel('Campaign')
            ax.set_ylabel('Number of Ads')
            ax.set_title('Ads by Campaign')
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
            
            # Adjust layout to make room for x-labels
            plt.tight_layout()
            
            st.pyplot(fig)
        
        # Display top keywords
        st.subheader("Top Keywords")
        
        # Count usage of each keyword
        keyword_counts = {}
        for ad in ads:
            for keyword in ad.get("keywords", []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Sort and get top 10
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_keywords:
            # Create a bar chart
            fig, ax = plt.subplots(figsize=(10, 4))
            keywords = [k[0] for k in top_keywords]
            counts = [k[1] for k in top_keywords]
            
            ax.barh(keywords, counts, color='#FF9800')
            ax.set_xlabel('Number of Ads')
            ax.set_ylabel('Keyword')
            ax.set_title('Top 10 Keywords')
            
            # Adjust layout
            plt.tight_layout()
            
            st.pyplot(fig)
        else:
            st.info("No keywords found in ads.")
    else:
        st.info("No ads found. Start by creating some ads to see dashboard analytics.")

def view_existing_ads(ads: List[Dict[str, Any]]) -> bool:
    """Display existing ads with filtering, sorting, and search capabilities."""
    reloaded = False
    
    if not ads:
        st.info("No ads found in the configuration.")
        return reloaded
    
    # Add search and filtering options
    st.subheader("Search & Filter")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("Search Ads", placeholder="Enter title, keyword, or category")
    
    with col2:
        filter_options = ["All", "Active Only", "Inactive Only"]
        if any(ad.get("campaign") for ad in ads):
            # Add campaign filter options if any ads have campaigns
            campaigns = sorted(set(ad.get("campaign") for ad in ads if ad.get("campaign")))
            filter_options.extend([f"Campaign: {c}" for c in campaigns])
        
        status_filter = st.selectbox("Filter", filter_options)
    
    # Add sorting options
    col1, col2 = st.columns(2)
    
    with col1:
        sort_options = ["Title (A-Z)", "Title (Z-A)", "Newest First", "Oldest First", "Priority (High to Low)"]
        sort_option = st.selectbox("Sort By", sort_options)
    
    # Apply filters and search
    filtered_ads = []
    
    for ad in ads:
        # Apply status filter
        if status_filter == "Active Only" and not ad.get("active", True):
            continue
        elif status_filter == "Inactive Only" and ad.get("active", True):
            continue
        elif status_filter.startswith("Campaign:"):
            campaign_name = status_filter.replace("Campaign: ", "")
            if ad.get("campaign") != campaign_name:
                continue
        
        # Apply search filter if provided
        if search_term:
            search_term_lower = search_term.lower()
            title_match = search_term_lower in ad.get("title", "").lower()
            description_match = search_term_lower in ad.get("description", "").lower()
            keyword_match = any(search_term_lower in k.lower() for k in ad.get("keywords", []))
            category_match = any(search_term_lower in c.lower() for c in ad.get("categories", []))
            
            if not (title_match or description_match or keyword_match or category_match):
                continue
        
        filtered_ads.append(ad)
    
    # Apply sorting
    if sort_option == "Title (A-Z)":
        filtered_ads.sort(key=lambda x: x.get("title", "").lower())
    elif sort_option == "Title (Z-A)":
        filtered_ads.sort(key=lambda x: x.get("title", "").lower(), reverse=True)
    elif sort_option == "Newest First":
        filtered_ads.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_option == "Oldest First":
        filtered_ads.sort(key=lambda x: x.get("created_at", ""))
    elif sort_option == "Priority (High to Low)":
        filtered_ads.sort(key=lambda x: x.get("priority", 0), reverse=True)
    
    # Display count of filtered ads
    st.markdown(f"### Showing {len(filtered_ads)} of {len(ads)} ads")
    
    # Display the filtered ads
    for i, ad in enumerate(filtered_ads):
        with st.expander(f"{ad.get('title', 'Unnamed Ad')}", expanded=i == 0 and len(filtered_ads) < 5):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**ID:** {ad.get('id', '')}")
                st.markdown(f"**Description:** {ad.get('description', '')}")
                st.markdown(f"**Call to Action:** {ad.get('cta', '')}")
                st.markdown(f"**Keywords:** {format_keywords_for_display(ad.get('keywords', []))}")
                st.markdown(f"**Categories:** {format_keywords_for_display(ad.get('categories', []))}")
                
                if ad.get("campaign"):
                    st.markdown(f"**Campaign:** {ad.get('campaign')}")
                
                # Display status
                status_color = "green" if ad.get("active", True) else "red"
                status_text = "Active" if ad.get("active", True) else "Inactive"
                st.markdown(f"**Status:** <span style='color:{status_color};'>{status_text}</span>", unsafe_allow_html=True)
                
                # Display dates
                if ad.get("start_date") and ad.get("end_date"):
                    st.markdown(f"**Active Period:** {ad.get('start_date')} to {ad.get('end_date')}")
            
            with col2:
                # Display image
                st.image(
                    ad.get("image_url", DEFAULT_IMAGE_URL),
                    caption="Ad Image",
                    use_column_width=True
                )
                
                # Action buttons for the ad
                button_col1, button_col2 = st.columns(2)
                
                with button_col1:
                    if st.button(f"Edit {ad.get('id', '')}", key=f"edit_{ad.get('id', '')}"):
                        st.session_state["edit_ad"] = ad.get("id", "")
                
                with button_col2:
                    if st.button(f"Delete {ad.get('id', '')}", key=f"delete_{ad.get('id', '')}"):
                        confirmation = st.checkbox(
                            f"Confirm deletion of '{ad.get('title')}'",
                            key=f"confirm_delete_{ad.get('id', '')}"
                        )
                        
                        if confirmation:
                            # Delete the ad
                            config = load_ad_config()
                            config["ads"] = [a for a in config["ads"] if a.get("id") != ad.get("id")]
                            
                            if save_ad_config(config):
                                st.success(f"Ad '{ad.get('title')}' deleted successfully!")
                                st.info("Reload to update the ad list.")
                                reloaded = True
                                # Force rerun to refresh the list
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete ad")
            
            # Tab options for detailed view
            detail_tab1, detail_tab2 = st.tabs(["Preview", "Analytics"])
            
            with detail_tab1:
                create_ad_preview(ad)
            
            with detail_tab2:
                display_ad_analytics(ad)
    
    return reloaded

def render_ad_manager_ui():
    """Render the ad manager UI in Streamlit."""
    st.title("Ad Manager")
    
    # Initialize session state if needed
    if "edit_ad" not in st.session_state:
        st.session_state["edit_ad"] = None
    
    # Load current configuration
    config = load_ad_config()
    ads = config.get("ads", [])
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Create New Ad", "View & Edit Ads"])
    
    with tab1:
        render_dashboard(ads)
    
    with tab2:
        st.header("Create a New Ad")
        ad_added, added_title = create_new_ad_form(ads)
        
        # Add the reload button outside the form
        if ad_added:
            if st.button("Reload Ad Manager", key="reload_after_add"):
                # Force reload of the ConfigDrivenAdManager
                try:
                    from ad_service.ad_delivery.config_driven_ad_manager import ConfigDrivenAdManager
                    ad_manager = ConfigDrivenAdManager()
                    ad_manager.reload_config()
                    st.success("Ad Manager reloaded!")
                except Exception as e:
                    st.error(f"Error reloading Ad Manager: {str(e)}")
                    logger.exception("Error reloading Ad Manager")
    
    with tab3:
        st.header("Existing Ads")
        
        # Handle edit mode if active
        if st.session_state["edit_ad"]:
            # Find the ad to edit
            edit_ad = None
            for ad in ads:
                if ad.get("id") == st.session_state["edit_ad"]:
                    edit_ad = ad
                    break
            
            if edit_ad:
                st.subheader(f"Edit Ad: {edit_ad.get('title', '')}")
                
                # Add back button
                if st.button("← Back to Ad List", key="back_from_edit"):
                    st.session_state["edit_ad"] = None
                    st.experimental_rerun()
                
                # Display edit form
                updated = edit_ad_form(edit_ad, ads)
                
                if updated:
                    if st.button("Reload Ad Manager", key="reload_after_edit"):
                        try:
                            from ad_service.ad_delivery.config_driven_ad_manager import ConfigDrivenAdManager
                            ad_manager = ConfigDrivenAdManager()
                            ad_manager.reload_config()
                            st.success("Ad Manager reloaded!")
                            st.session_state["edit_ad"] = None  # Exit edit mode
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error reloading Ad Manager: {str(e)}")
                            logger.exception("Error reloading Ad Manager")
            else:
                st.error(f"Ad with ID {st.session_state['edit_ad']} not found")
                st.session_state["edit_ad"] = None
                st.experimental_rerun()
        else:
            # Display the ad list
            reloaded = view_existing_ads(ads)
            
            if reloaded:
                if st.button("Reload Ad Manager", key="reload_after_delete"):
                    try:
                        from ad_service.ad_delivery.config_driven_ad_manager import ConfigDrivenAdManager
                        ad_manager = ConfigDrivenAdManager()
                        ad_manager.reload_config()
                        st.success("Ad Manager reloaded!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error reloading Ad Manager: {str(e)}")
                        logger.exception("Error reloading Ad Manager")


if __name__ == "__main__":
    render_ad_manager_ui()