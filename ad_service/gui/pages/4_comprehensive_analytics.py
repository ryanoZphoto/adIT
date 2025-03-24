import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from ad_service.analytics.enhanced_metrics_collector import EnhancedMetricsCollector
from ad_service.analytics.metrics_collector import MetricsCollector

def render_comprehensive_analytics():
    st.title("📊 Comprehensive Analytics Dashboard")
    
    # Initialize metrics collector with a fallback approach
    try:
        metrics_collector = EnhancedMetricsCollector()
        
        # Check if the metrics_collector is actually an EnhancedMetricsCollector
        if not hasattr(metrics_collector, 'get_active_campaigns'):
            st.warning("Enhanced metrics features not available. Using basic metrics collector.")
            # Create a simplified dashboard without campaign data
            render_simplified_analytics(metrics_collector)
            return
    except Exception as e:
        st.error(f"Error initializing enhanced metrics: {str(e)}")
        metrics_collector = MetricsCollector()
        render_simplified_analytics(metrics_collector)
        return
    
    # Date Range Selector
    with st.sidebar:
        st.header("Filters")
        start_date, end_date = st.date_input(
            "Select Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            key="date_range"
        )
        
        # Get active campaigns using a try/except block to handle potential errors
        try:
            active_campaigns = metrics_collector.get_active_campaigns()
        except Exception as e:
            st.error(f"Error loading campaigns: {str(e)}")
            active_campaigns = ["all_campaigns"]
        
        campaign_id = st.selectbox(
            "Select Campaign",
            options=active_campaigns,
            key="campaign_selector"
        )
    
    # Campaign Analytics
    try:
        campaign_metrics = metrics_collector.get_campaign_analytics(
            campaign_id=campaign_id,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time())
        )
        
        # Display metrics with proper data validation
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "CTR", 
                f"{campaign_metrics.get('ctr', 0):.2f}%",
                help="Click-through rate"
            )
        with col2:
            st.metric(
                "Conversion Rate", 
                f"{campaign_metrics.get('conversion_rate', 0):.2f}%",
                help="Conversion rate from clicks"
            )
        with col3:
            st.metric(
                "ROAS", 
                f"{campaign_metrics.get('roas', 0):.2f}x",
                help="Return on ad spend"
            )
            
        # Add more detailed visualizations
        st.subheader("Performance Over Time")
        try:
            time_series_data = metrics_collector.get_time_series_metrics(campaign_id)
            if not time_series_data.empty:
                fig = px.line(time_series_data, 
                             x="date", 
                             y=["impressions", "clicks", "conversions"],
                             title="Campaign Performance Trends")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No time series data available for this campaign and date range.")
        except Exception as e:
            st.warning(f"Could not load time series data: {str(e)}")
            
    except Exception as e:
        st.error(f"Error retrieving campaign data: {str(e)}")
        st.info("Please select a different campaign or date range.")

def render_simplified_analytics(metrics_collector):
    """Render simplified analytics without campaign data"""
    st.subheader("System Metrics")
    
    # Get system health data
    system_health = metrics_collector.get_system_health()
    
    # Display system metrics in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("CPU Usage", f"{system_health.get('cpu_percent', 0):.1f}%")
    with col2:
        st.metric("Memory Usage", f"{system_health.get('memory_percent', 0):.1f}%")
    with col3:
        st.metric("Disk Usage", f"{system_health.get('disk_percent', 0):.1f}%")
    
    # Display system info
    st.subheader("System Information")
    st.code(system_health.get('system_info', 'System information not available'))
    
    # Get events from database for basic statistics
    conn = metrics_collector._get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'impression'")
        total_impressions = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'click'")
        total_clicks = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM model_generations")
        total_generations = cursor.fetchone()[0] or 0
        
        # Display basic statistics
        st.subheader("Basic Statistics")
        basic_stats = pd.DataFrame({
            "Metric": ["Total Events", "Ad Impressions", "Ad Clicks", "Model Generations"],
            "Count": [total_events, total_impressions, total_clicks, total_generations]
        })
        st.dataframe(basic_stats, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error retrieving basic statistics: {str(e)}")

if __name__ == "__main__":
    render_comprehensive_analytics()
