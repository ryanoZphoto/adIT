import streamlit as st
import sys
import os
from pathlib import Path
import time

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ad_service.analytics.metrics_collector import MetricsCollector

def main():
    st.title("Basic Analytics Dashboard")
    
    # Get real metrics from the metrics collector
    metrics_collector = MetricsCollector()
    
    # Fetch actual metrics summary
    metrics_summary = metrics_collector.get_metrics_summary()
    
    # Get real system health metrics
    system_health = metrics_summary.get("system_health", {})
    
    # Format the metrics for display
    total_interactions = metrics_summary["total_generations"] + metrics_summary["total_impressions"]
    avg_response_time = f"{metrics_summary['avg_generation_time']:.2f}s" if metrics_summary['avg_generation_time'] else "N/A"
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Interactions", total_interactions)
    
    with col2:
        st.metric("Avg Response Time", avg_response_time)
    
    with col3:
        st.metric("System Uptime", system_health.get("uptime", "N/A"))
    
    # Add system health details
    st.subheader("System Health")
    
    # Display system health metrics in columns
    health_col1, health_col2, health_col3 = st.columns(3)
    
    with health_col1:
        cpu_percent = system_health.get("cpu_percent", 0)
        st.metric("CPU Usage", f"{cpu_percent:.1f}%")
    
    with health_col2:
        memory_percent = system_health.get("memory_percent", 0)
        st.metric("Memory Usage", f"{memory_percent:.1f}%")
    
    with health_col3:
        disk_percent = system_health.get("disk_percent", 0)
        st.metric("Disk Usage", f"{disk_percent:.1f}%")
    
    # Add system info
    system_info = system_health.get("system_info", {})
    os_name = system_info.get("os", "Unknown")
    os_version = system_info.get("version", "Unknown")
    
    with st.expander("System Information"):
        st.write(f"Operating System: {os_name} ({os_version})")
        st.write(f"Processor: {system_info.get('processor', 'Unknown')}")
    
    # Add a refresh button
    if st.button("Refresh Data"):
        st.rerun()
    
    # Display recent activity
    st.subheader("Recent Activity")
    
    # Get recent model generations
    recent_generations = metrics_collector.get_model_generations(limit=5)
    if recent_generations:
        st.write("Recent Queries:")
        for gen in recent_generations:
            st.write(f"- Query: '{gen['query']}' ({gen['timestamp']})")
    else:
        st.write("No recent queries found.")
    
    # Get recent ad impressions
    recent_impressions = metrics_collector.get_ad_impressions(limit=5)
    if recent_impressions:
        st.write("Recent Ad Impressions:")
        for imp in recent_impressions:
            st.write(f"- Ad ID: {imp['ad_id']} for query: '{imp['query']}' (Score: {imp['relevance_score']})")
    else:
        st.write("No recent ad impressions found.")

if __name__ == "__main__":
    main()
