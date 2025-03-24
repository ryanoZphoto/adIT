"""
Ad Performance Dashboard

This page displays detailed ad performance metrics, showing how ads are performing
in the conversational AI context. It provides visualizations of impressions, clicks,
conversions, and other key metrics for advertisers to understand their ROI.
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3
import os
import sys

# Add parent directory to path to import from parent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from analytics.metrics_collector import MetricsCollector
from analytics.enhanced_metrics_collector import EnhancedMetricsCollector
from ad_matching.ad_repository import AdRepository

# Page configuration
st.set_page_config(
    page_title="Ad Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

def render_ad_performance_dashboard():
    """Render the Ad Performance Dashboard page"""
    
    st.title("📊 Ad Performance Dashboard")
    st.subheader("Monitor and analyze your ad campaign performance")
    
    # Get data sources
    try:
        metrics_collector = EnhancedMetricsCollector()
        ad_repository = AdRepository()
    except Exception as e:
        st.error(f"Error loading data sources: {e}")
        st.warning("Using sample data for demonstration purposes.")
        metrics_collector = None
        ad_repository = None
    
    # Load ad data
    try:
        if ad_repository:
            ads = ad_repository.get_all_ads()
        else:
            # Use the modified ads.json directly if repository not available
            with open('../data/ads.json', 'r') as f:
                ads = json.load(f)
    except Exception as e:
        st.error(f"Error loading ad data: {e}")
        # Provide sample data as fallback
        ads = load_sample_ad_data()
    
    # Filters section
    with st.expander("📌 Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get unique advertisers
            advertisers = list(set([ad.get('advertiser_id', 'Unknown') for ad in ads]))
            selected_advertiser = st.selectbox(
                "Select Advertiser", 
                options=["All Advertisers"] + advertisers
            )
        
        with col2:
            # Get unique campaigns
            campaigns = list(set([ad.get('campaign_id', 'Unknown') for ad in ads]))
            selected_campaign = st.selectbox(
                "Select Campaign", 
                options=["All Campaigns"] + campaigns
            )
        
        with col3:
            # Date range selection
            date_options = {
                "Last 7 Days": 7,
                "Last 30 Days": 30,
                "Last 90 Days": 90,
                "All Time": 365 * 10  # Very large number for "all time"
            }
            selected_date_range = st.selectbox(
                "Date Range",
                options=list(date_options.keys())
            )
            date_range_days = date_options[selected_date_range]
    
    # Filter ads based on selection
    filtered_ads = filter_ads(ads, selected_advertiser, selected_campaign)
    
    # Performance Summary Cards
    st.subheader("📈 Performance Summary")
    
    # Calculate totals
    total_impressions = sum(ad.get('performance', {}).get('impressions', 0) for ad in filtered_ads)
    total_clicks = sum(ad.get('performance', {}).get('clicks', 0) for ad in filtered_ads)
    total_conversions = sum(ad.get('performance', {}).get('conversions', 0) for ad in filtered_ads)
    
    # Calculate rates
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    avg_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    
    # Estimate spend based on clicks and average bid
    avg_bid = sum(ad.get('bid_amount', 0) for ad in filtered_ads) / len(filtered_ads) if filtered_ads else 0
    estimated_spend = total_clicks * avg_bid
    
    # Create metric cards
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Impressions", f"{total_impressions:,}")
    col2.metric("Clicks", f"{total_clicks:,}")
    col3.metric("CTR", f"{avg_ctr:.2f}%")
    col4.metric("Conversions", f"{total_conversions:,}")
    col5.metric("Est. Spend", f"${estimated_spend:.2f}")
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    # Ad Performance Comparison
    with col1:
        st.subheader("Ad Performance Comparison")
        fig = create_ad_performance_chart(filtered_ads)
        st.plotly_chart(fig, use_container_width=True)
    
    # CTR and Conversion Rate Trends
    with col2:
        st.subheader("CTR vs Conversion Rate")
        fig = create_ctr_conversion_chart(filtered_ads)
        st.plotly_chart(fig, use_container_width=True)
    
    # Ad Details Table
    st.subheader("📋 Detailed Ad Performance")
    ad_df = create_ad_performance_table(filtered_ads)
    st.dataframe(ad_df, use_container_width=True)
    
    # Conversation Context Analysis
    st.subheader("💬 Conversation Context Analysis")
    
    # Create sample context data - in a real implementation, this would come from the metrics collector
    context_data = generate_context_data(filtered_ads)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Matched Keywords")
        keyword_df = pd.DataFrame(context_data['top_keywords'].items(), columns=['Keyword', 'Count'])
        keyword_df = keyword_df.sort_values('Count', ascending=False).head(10)
        
        fig = px.bar(keyword_df, x='Count', y='Keyword', orientation='h',
                    title="Keywords That Triggered Ads",
                    labels={'Count': 'Number of Matches', 'Keyword': ''})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Commercial Intent Detection")
        intent_data = pd.DataFrame({
            'Intent Type': ['Commercial Intent', 'Informational', 'Other'],
            'Percentage': [
                context_data['intent_distribution'].get('commercial', 0),
                context_data['intent_distribution'].get('informational', 0),
                context_data['intent_distribution'].get('other', 0)
            ]
        })
        
        fig = px.pie(intent_data, values='Percentage', names='Intent Type',
                    title="Conversation Intent Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Daily Performance Trends
    st.subheader("📅 Daily Performance Trends")
    
    # Generate sample time series data
    dates = pd.date_range(end=datetime.now(), periods=date_range_days)
    daily_data = generate_daily_performance_data(dates, filtered_ads)
    
    # Plot time series
    fig = px.line(daily_data, x='Date', y=['Impressions', 'Clicks', 'Conversions'],
                 title="Daily Ad Performance Metrics")
    st.plotly_chart(fig, use_container_width=True)
    
    # Matching Factors Analysis
    st.subheader("🔍 Ad Matching Analysis")
    
    matching_data = generate_matching_data(filtered_ads)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Create gauge chart for average relevance score
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = matching_data['avg_relevance_score'],
            title = {'text': "Average Relevance Score"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.3], 'color': "red"},
                    {'range': [0.3, 0.7], 'color': "orange"},
                    {'range': [0.7, 1], 'color': "green"}
                ]
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Create radar chart for matching factors
        categories = ['Keyword Match', 'Category Match', 'Semantic Match', 
                     'Demographic Match', 'Interest Match']
        values = [
            matching_data['match_factors']['keyword_match'],
            matching_data['match_factors']['category_match'],
            matching_data['match_factors']['semantic_match'],
            matching_data['match_factors']['demographic_match'],
            matching_data['match_factors']['interest_match']
        ]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Match Factors'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="Ad Matching Factor Distribution (%)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Action recommendations
    st.subheader("🚀 Optimization Recommendations")
    
    recommendations = generate_recommendations(filtered_ads, matching_data)
    
    for i, (title, desc) in enumerate(recommendations):
        with st.expander(f"Recommendation {i+1}: {title}"):
            st.markdown(desc)
    
    # Add data refresh button
    if st.button("Refresh Data"):
        st.rerun()
    
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def filter_ads(ads, advertiser, campaign):
    """Filter ads based on selected filters"""
    filtered = ads.copy()
    
    if advertiser != "All Advertisers":
        filtered = [ad for ad in filtered if ad.get('advertiser_id') == advertiser]
    
    if campaign != "All Campaigns":
        filtered = [ad for ad in filtered if ad.get('campaign_id') == campaign]
    
    return filtered


def create_ad_performance_chart(ads):
    """Create a chart comparing performance across different ads"""
    # Prepare data
    ad_data = []
    for ad in ads:
        perf = ad.get('performance', {})
        ad_data.append({
            'Ad Title': ad.get('title', 'Unknown Ad'),
            'Impressions': perf.get('impressions', 0),
            'Clicks': perf.get('clicks', 0),
            'CTR': perf.get('ctr', 0)
        })
    
    df = pd.DataFrame(ad_data)
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add bar chart for impressions and clicks
    fig.add_trace(
        go.Bar(x=df['Ad Title'], y=df['Impressions'], name="Impressions"),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Bar(x=df['Ad Title'], y=df['Clicks'], name="Clicks"),
        secondary_y=False,
    )
    
    # Add line chart for CTR
    fig.add_trace(
        go.Scatter(x=df['Ad Title'], y=df['CTR'], name="CTR (%)", line=dict(color='red')),
        secondary_y=True,
    )
    
    # Set y-axes titles
    fig.update_yaxes(title_text="Count", secondary_y=False)
    fig.update_yaxes(title_text="CTR (%)", secondary_y=True)
    
    fig.update_layout(
        title="Ad Performance Metrics",
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_ctr_conversion_chart(ads):
    """Create a scatter plot showing CTR vs Conversion Rate for each ad"""
    # Prepare data
    ad_data = []
    for ad in ads:
        perf = ad.get('performance', {})
        ad_data.append({
            'Ad Title': ad.get('title', 'Unknown Ad')[:20] + "...",  # Truncate for display
            'CTR': perf.get('ctr', 0),
            'Conversion Rate': perf.get('conversion_rate', 0),
            'Impressions': perf.get('impressions', 0),
            'Quality Score': perf.get('quality_score', 5)
        })
    
    df = pd.DataFrame(ad_data)
    
    # Create scatter plot
    fig = px.scatter(df, x='CTR', y='Conversion Rate', size='Impressions', 
                    color='Quality Score', hover_name='Ad Title',
                    size_max=60, color_continuous_scale=px.colors.sequential.Viridis)
    
    fig.update_layout(
        title="CTR vs Conversion Rate by Ad",
        xaxis_title="Click-Through Rate (%)",
        yaxis_title="Conversion Rate (%)",
        coloraxis_colorbar=dict(title="Quality Score")
    )
    
    return fig


def create_ad_performance_table(ads):
    """Create a DataFrame for the ad performance table"""
    rows = []
    for ad in ads:
        perf = ad.get('performance', {})
        
        # Calculate cost assuming bid amount per click
        estimated_cost = perf.get('clicks', 0) * ad.get('bid_amount', 0)
        cost_per_conversion = estimated_cost / perf.get('conversions', 1) if perf.get('conversions', 0) > 0 else 0
        
        rows.append({
            'Ad ID': ad.get('id', 'Unknown'),
            'Title': ad.get('title', 'Unknown Ad'),
            'Campaign': ad.get('campaign_id', 'Unknown'),
            'Impressions': perf.get('impressions', 0),
            'Clicks': perf.get('clicks', 0),
            'CTR (%)': perf.get('ctr', 0),
            'Conversions': perf.get('conversions', 0),
            'Conv. Rate (%)': perf.get('conversion_rate', 0),
            'Bid Amount': f"${ad.get('bid_amount', 0):.2f}",
            'Est. Cost': f"${estimated_cost:.2f}",
            'Cost/Conv.': f"${cost_per_conversion:.2f}",
            'Quality Score': perf.get('quality_score', 0),
            'Avg Position': perf.get('avg_position', 0)
        })
    
    return pd.DataFrame(rows)


def generate_context_data(ads):
    """Generate sample conversation context data - in a real implementation, this would come from the metrics collector"""
    # This simulates the data that would be collected about what context ads were shown in
    all_keywords = []
    for ad in ads:
        all_keywords.extend(ad.get('keywords', []))
    
    # Count keyword frequencies
    keyword_counts = {}
    for kw in all_keywords:
        if kw in keyword_counts:
            keyword_counts[kw] += np.random.randint(5, 100)  # Random counts for demonstration
        else:
            keyword_counts[kw] = np.random.randint(5, 100)
    
    # Generate mock intent distribution
    intent_distribution = {
        'commercial': np.random.randint(40, 70),  # Commercial intent percentage
        'informational': np.random.randint(20, 40),  # Informational intent
        'other': np.random.randint(5, 20)  # Other intent types
    }
    
    # Normalize to 100%
    total = sum(intent_distribution.values())
    for key in intent_distribution:
        intent_distribution[key] = (intent_distribution[key] / total) * 100
    
    return {
        'top_keywords': keyword_counts,
        'intent_distribution': intent_distribution
    }


def generate_daily_performance_data(dates, ads):
    """Generate sample daily performance data for the time series chart"""
    # Sum up total performance metrics
    total_impressions = sum(ad.get('performance', {}).get('impressions', 0) for ad in ads)
    total_clicks = sum(ad.get('performance', {}).get('clicks', 0) for ad in ads)
    total_conversions = sum(ad.get('performance', {}).get('conversions', 0) for ad in ads)
    
    # Create daily distribution
    daily_impressions = distribute_over_days(total_impressions, len(dates))
    daily_clicks = distribute_over_days(total_clicks, len(dates))
    daily_conversions = distribute_over_days(total_conversions, len(dates))
    
    # Create DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Impressions': daily_impressions,
        'Clicks': daily_clicks,
        'Conversions': daily_conversions
    })
    
    return df


def distribute_over_days(total, num_days):
    """Distribute a total value over days with some randomness to create realistic patterns"""
    if total == 0 or num_days == 0:
        return [0] * max(1, num_days)
    
    # Create a basic distribution
    base = total / num_days
    
    # Add randomness with weekly patterns
    daily_values = []
    for i in range(num_days):
        # Weekend effect (days 5 and 6 in a week have different patterns)
        weekend_factor = 0.8 if i % 7 >= 5 else 1.1
        
        # Random daily variation
        random_factor = np.random.normal(1, 0.2)  # Mean of 1 with standard deviation of 0.2
        
        # Combine factors and add to result
        daily_value = base * weekend_factor * random_factor
        daily_values.append(max(0, int(daily_value)))  # Ensure non-negative
    
    # Ensure the sum matches the total by adjusting the last value
    current_sum = sum(daily_values)
    daily_values[-1] += (total - current_sum)
    daily_values[-1] = max(0, daily_values[-1])  # Ensure non-negative
    
    return daily_values


def generate_matching_data(ads):
    """Generate sample data about how ads were matched"""
    # In a real implementation, this would come from tracking match factors for each impression
    
    # Calculate average relevance score
    relevance_scores = [np.random.uniform(0.6, 0.95) for _ in range(len(ads))]
    avg_relevance_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.7
    
    # Mock distribution of matching factors
    match_factors = {
        'keyword_match': np.random.randint(40, 60),
        'category_match': np.random.randint(15, 30),
        'semantic_match': np.random.randint(10, 25),
        'demographic_match': np.random.randint(5, 15),
        'interest_match': np.random.randint(5, 15)
    }
    
    # Normalize to 100%
    total = sum(match_factors.values())
    for key in match_factors:
        match_factors[key] = (match_factors[key] / total) * 100
    
    return {
        'avg_relevance_score': avg_relevance_score,
        'match_factors': match_factors
    }


def generate_recommendations(ads, matching_data):
    """Generate optimization recommendations based on ad performance"""
    recommendations = []
    
    # Sample recommendations based on patterns in the data
    if matching_data['match_factors']['keyword_match'] > 50:
        recommendations.append(
            ("Expand Your Keywords", 
             """Your ads are primarily matching based on keywords. Consider:
             - Adding more category-specific keywords
             - Including related terms that potential customers might use
             - Testing long-tail keywords for specific intent""")
        )
    
    low_ctr_ads = [ad for ad in ads if ad.get('performance', {}).get('ctr', 0) < 2.0]
    if low_ctr_ads:
        recommendations.append(
            ("Improve Ad Creative for Low CTR Ads", 
             f"""You have {len(low_ctr_ads)} ads with CTR below 2%. Try:
             - A/B testing different ad titles
             - Adding stronger call-to-action phrases
             - Making the value proposition clearer
             - Testing different display formats""")
        )
    
    high_cost_ads = [ad for ad in ads if ad.get('bid_amount', 0) > 2.5]
    if high_cost_ads:
        recommendations.append(
            ("Optimize Bidding Strategy", 
             f"""You have {len(high_cost_ads)} ads with high bid amounts. Consider:
             - Reducing bids for ads with low conversion rates
             - Implementing automated bid adjustments based on performance
             - Setting different bids for different conversation contexts""")
        )
    
    # Always provide a recommendation about targeting
    recommendations.append(
        ("Refine Your Audience Targeting", 
         """Enhance your targeting precision by:
         - Reviewing audience interests and demographics settings
         - Adding negative keywords for irrelevant contexts
         - Setting dayparting to focus on high-conversion time periods
         - Creating more specific campaigns for different user segments""")
    )
    
    return recommendations


def load_sample_ad_data():
    """Load sample ad data for demonstration when actual data isn't available"""
    try:
        with open('../data/ads.json', 'r') as f:
            return json.load(f)
    except:
        # Create basic sample data if file can't be loaded
        return [
            {
                "id": "ad_sample_1",
                "advertiser_id": "sample_advertiser",
                "campaign_id": "sample_campaign",
                "title": "Sample Ad 1",
                "bid_amount": 1.50,
                "keywords": ["sample", "test", "example"],
                "performance": {
                    "impressions": 1000,
                    "clicks": 30,
                    "conversions": 5,
                    "ctr": 3.0,
                    "conversion_rate": 16.67,
                    "quality_score": 7,
                    "avg_position": 2.1
                }
            },
            {
                "id": "ad_sample_2",
                "advertiser_id": "sample_advertiser",
                "campaign_id": "sample_campaign",
                "title": "Sample Ad 2",
                "bid_amount": 1.75,
                "keywords": ["demo", "test", "showcase"],
                "performance": {
                    "impressions": 800,
                    "clicks": 25,
                    "conversions": 3,
                    "ctr": 3.13,
                    "conversion_rate": 12.0,
                    "quality_score": 6,
                    "avg_position": 2.5
                }
            }
        ]


# Render the dashboard when the page loads
if __name__ == "__main__":
    render_ad_performance_dashboard()
else:
    render_ad_performance_dashboard() 