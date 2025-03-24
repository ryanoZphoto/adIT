import streamlit as st
from ad_service.analytics.enhanced_metrics_collector import EnhancedMetricsCollector  # Use enhanced version

class MetricsDashboard:
    def __init__(self):
        self.metrics_collector = EnhancedMetricsCollector()  # Use enhanced collector for more metrics

    def render_system_metrics(self):
        metrics = self.metrics_collector.get_system_metrics()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Ad Requests", metrics['ad_requests'])
        with col2:
            st.metric("Click Rate", f"{metrics['click_rate']:.2f}%")
        with col3:
            st.metric("Active Users", metrics['active_users'])

    def render_performance_metrics(self):
        metrics = self.metrics_collector.get_performance_metrics()
        st.header("Performance Metrics")
        for metric, value in metrics.items():
            st.metric(metric, value)

    def render_debug_controls(self):
        if st.button("Simulate Ad Request"):
            self.metrics_collector.record_ad_request()
            st.success("Ad request recorded!")
            
        if st.button("Simulate Ad Click"):
            self.metrics_collector.record_ad_click()
            st.success("Ad click recorded!")

def show_dashboard():
    st.title("System Metrics Dashboard")
    
    metrics_dashboard = MetricsDashboard()
    
    try:
        # System metrics
        st.header("System Performance")
        metrics_dashboard.render_system_metrics()

        # Performance metrics
        metrics_dashboard.render_performance_metrics()

        # Debug controls
        metrics_dashboard.render_debug_controls()

    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")
