import streamlit as st
from ad_service.analytics.metrics_collector import MetricsCollector

def analytics_page():
    st.title("Detailed Analytics")
    
    metrics = MetricsCollector()
    
    # Basic metrics display
    st.header("Key Metrics")
    
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Ad Impressions", 
                     value=len(metrics.get_ad_impressions(limit=1000)))
        
        with col2:
            st.metric(label="Ad Clicks", 
                     value=len(metrics.get_ad_clicks(limit=1000)))
        
        with col3:
            st.metric(label="Total Events", 
                     value=len(metrics.get_events(limit=1000)))
            
    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")
    
    # Display recent impressions
    st.header("Recent Ad Impressions")
    try:
        impressions = metrics.get_ad_impressions(limit=10)
        if impressions:
            impression_data = []
            for imp in impressions:
                impression_data.append({
                    "Time": imp.get("timestamp", ""),
                    "Query": imp.get("query", ""),
                    "Ad ID": imp.get("ad_id", ""),
                    "Relevance": f"{imp.get('relevance_score', 0):.2f}"
                })
            st.dataframe(impression_data)
        else:
            st.info("No ad impressions recorded yet")
    except Exception as e:
        st.error(f"Error loading ad impressions: {str(e)}")
    
    # Display recent model generations
    st.header("Recent Model Generations")
    try:
        generations = metrics.get_model_generations(limit=10)
        if generations:
            generation_data = []
            for gen in generations:
                generation_data.append({
                    "Time": gen.get("timestamp", ""),
                    "Query": gen.get("query", ""),
                    "Model": gen.get("model", ""),
                    "Generation Time": f"{gen.get('generation_time', 0):.2f}s"
                })
            st.dataframe(generation_data)
        else:
            st.info("No model generations recorded yet")
    except Exception as e:
        st.error(f"Error loading model generations: {str(e)}")

if __name__ == "__main__":
    analytics_page()
