import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta
import os

# Set page config
st.set_page_config(
    page_title="Ad Service Metrics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Get database path from environment or use default
service_root = os.getenv('AD_SERVICE_ROOT', os.path.dirname(os.path.dirname(__file__)))
db_path = os.path.join(service_root, 'data', 'metrics.db')

def get_db_connection():
    return sqlite3.connect(db_path)

def load_impressions_data():
    with get_db_connection() as conn:
        return pd.read_sql_query("""
            SELECT timestamp, ad_id, company_id, relevance_score, position
            FROM ad_impressions
            WHERE timestamp >= datetime('now', '-7 days')
        """, conn)

def load_clicks_data():
    with get_db_connection() as conn:
        return pd.read_sql_query("""
            SELECT timestamp, ad_id, company_id
            FROM ad_clicks
            WHERE timestamp >= datetime('now', '-7 days')
        """, conn)

def main():
    st.title("Ad Service Metrics Dashboard")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    date_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
        index=1
    )
    
    try:
        # Load data
        impressions_df = load_impressions_data()
        clicks_df = load_clicks_data()
        
        # Convert timestamp to datetime
        impressions_df['timestamp'] = pd.to_datetime(impressions_df['timestamp'])
        clicks_df['timestamp'] = pd.to_datetime(clicks_df['timestamp'])
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_impressions = len(impressions_df)
            st.metric("Total Impressions", f"{total_impressions:,}")
            
        with col2:
            total_clicks = len(clicks_df)
            st.metric("Total Clicks", f"{total_clicks:,}")
            
        with col3:
            ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            st.metric("Click-Through Rate", f"{ctr:.2f}%")
            
        with col4:
            avg_relevance = impressions_df['relevance_score'].mean()
            st.metric("Avg Relevance Score", f"{avg_relevance:.2f}")
        
        # Impressions Over Time
        st.subheader("Impressions Over Time")
        daily_impressions = impressions_df.groupby(
            impressions_df['timestamp'].dt.date
        ).size().reset_index(name='count')
        
        fig = px.line(
            daily_impressions,
            x='timestamp',
            y='count',
            title="Daily Impressions"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top Performing Ads
        st.subheader("Top Performing Ads")
        top_ads = pd.merge(
            impressions_df.groupby('ad_id').size().reset_index(name='impressions'),
            clicks_df.groupby('ad_id').size().reset_index(name='clicks'),
            on='ad_id',
            how='left'
        )
        top_ads['ctr'] = (top_ads['clicks'] / top_ads['impressions'] * 100).fillna(0)
        top_ads = top_ads.sort_values('ctr', ascending=False).head(10)
        
        fig = px.bar(
            top_ads,
            x='ad_id',
            y='ctr',
            title="Top 10 Ads by CTR"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")
        st.info("If this is a new installation, metrics will appear as data is collected.")

if __name__ == "__main__":
    main() 