import streamlit as st
from datetime import datetime
import json
import logging
from typing import Dict, Any

class DebugPanel:
    @staticmethod
    def render():
        with st.expander("Debug Panel", expanded=False):
            # Create tabs for different debug information
            tab1, tab2, tab3, tab4 = st.tabs([
                "Ad Pipeline", "API Calls", "System Metrics", "Error Log"
            ])
            
            with tab1:
                st.subheader("Ad Service Pipeline")
                if 'ad_events' not in st.session_state:
                    st.session_state.ad_events = []
                
                for event in st.session_state.ad_events:
                    with st.expander(f"Query: {event.get('query', 'N/A')} - {event.get('timestamp', '')}"):
                        # Content Safety Check
                        st.markdown("#### 1. Content Safety Check")
                        safety_step = next((step for step in event.get('steps', []) 
                                         if step['step'] == 'content_safety'), {})
                        st.code(json.dumps(safety_step, indent=2))
                        
                        # Query Analysis
                        st.markdown("#### 2. Query Analysis")
                        analysis_step = next((step for step in event.get('steps', []) 
                                           if step['step'] == 'query_analysis'), {})
                        st.code(json.dumps(analysis_step, indent=2))
                        
                        # Ad Matching
                        st.markdown("#### 3. Ad Matching")
                        matching_step = next((step for step in event.get('steps', []) 
                                           if step['step'] == 'ad_matching'), {})
                        st.code(json.dumps(matching_step, indent=2))
                        
                        # Ad Generation
                        st.markdown("#### 4. Ad Generation")
                        generation_step = next((step for step in event.get('steps', []) 
                                             if step['step'] == 'ad_generation'), {})
                        st.code(json.dumps(generation_step, indent=2))
                        
                        # Processing Time
                        st.metric("Total Processing Time", 
                                f"{event.get('processing_time_ms', 0):.2f}ms")
            
            with tab2:
                st.subheader("API Calls")
                if 'api_calls' not in st.session_state:
                    st.session_state.api_calls = []
                
                for call in st.session_state.api_calls:
                    with st.expander(f"{call.get('endpoint', 'Unknown')} - {call.get('timestamp', '')}"):
                        st.json({
                            "request": call.get('request', {}),
                            "response": call.get('response', {}),
                            "latency_ms": call.get('latency_ms', 0),
                            "status": call.get('status', 'unknown')
                        })
            
            with tab3:
                st.subheader("System Metrics")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Ad Trigger Rate", 
                            f"{st.session_state.get('ad_trigger_rate', 0)}%")
                    st.metric("Avg Response Time", 
                            f"{st.session_state.get('avg_response_time', 0)}ms")
                    st.metric("Active Sessions", 
                            st.session_state.get('active_sessions', 0))
                
                with col2:
                    st.metric("Memory Usage", 
                            f"{st.session_state.get('memory_usage_mb', 0)}MB")
                    st.metric("API Calls/min", 
                            st.session_state.get('api_calls_per_minute', 0))
                    st.metric("Error Rate", 
                            f"{st.session_state.get('error_rate', 0)}%")
            
            with tab4:
                st.subheader("Error Log")
                if 'error_log' not in st.session_state:
                    st.session_state.error_log = []
                
                for error in st.session_state.error_log:
                    with st.expander(f"{error.get('timestamp', '')} - {error.get('error_type', 'Unknown Error')}"):
                        st.error(error.get('message', ''))
                        if error.get('stack_trace'):
                            st.code(error.get('stack_trace'))
            
            # Debug Controls
            st.divider()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Clear Debug Data"):
                    st.session_state.ad_events = []
                    st.session_state.api_calls = []
                    st.session_state.error_log = []
            
            with col2:
                if st.button("Export Debug Log"):
                    debug_data = {
                        "ad_events": st.session_state.ad_events,
                        "api_calls": st.session_state.api_calls,
                        "error_log": st.session_state.error_log,
                        "metrics": {
                            "ad_trigger_rate": st.session_state.get('ad_trigger_rate', 0),
                            "avg_response_time": st.session_state.get('avg_response_time', 0),
                            "active_sessions": st.session_state.get('active_sessions', 0),
                            "memory_usage_mb": st.session_state.get('memory_usage_mb', 0),
                            "api_calls_per_minute": st.session_state.get('api_calls_per_minute', 0),
                            "error_rate": st.session_state.get('error_rate', 0)
                        }
                    }
                    st.download_button(
                        "Download Debug Log",
                        data=json.dumps(debug_data, indent=2),
                        file_name=f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            with col3:
                log_level = st.selectbox(
                    "Log Level",
                    ["DEBUG", "INFO", "WARNING", "ERROR"],
                    index=1
                )
                if log_level:
                    logging.getLogger().setLevel(getattr(logging, log_level))
