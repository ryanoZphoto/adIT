"""
Metrics Collector Module

This module is responsible for collecting metrics data from various components
of the ad service and forwarding it to the metrics storage system.
"""

import logging
import json
from datetime import datetime
import sqlite3
from pathlib import Path
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import os
import pandas as pd
import threading
from prometheus_client import start_http_server
from prometheus_client import multiprocess
import psutil
import time
import platform
from typing import Dict, Any

# Global variable for singleton instance
_metrics_collector_instance = None
# Thread lock for thread safety during initialization
_instance_lock = threading.Lock()
# Thread-local storage for database connections
_thread_local = threading.local()

def configure_root_logger():
    """
    Configure the root logger to avoid duplicates.
    This function should be called once at the start of the application.
    """
    root_logger = logging.getLogger()
    
    # Remove all existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up a single handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    return root_logger

def setup_component_logger(name):
    """Sets up a logger for a specific component."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent propagation to avoid duplicates
    logger.propagate = False
    
    # Clear existing handlers if they exist
    logger.handlers = []
    
    # Add a single handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

class MetricsCollector:
    """Collects metrics for the ad delivery service."""
    
    # Class-level flag to ensure initialization happens only once
    _initialized = False
    # Track system start time
    _start_time = time.time()

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern"""
        global _metrics_collector_instance
        
        with _instance_lock:
            if _metrics_collector_instance is None:
                _metrics_collector_instance = super(MetricsCollector, cls).__new__(cls)
                # Set flag to indicate initialization is needed
                _metrics_collector_instance._needs_init = True
            return _metrics_collector_instance

    def __init__(self, db_path=None):
        """Initialize the metrics collector."""
        # Check if initialization is needed
        if not hasattr(self, '_needs_init') or not self._needs_init:
            return
        
        # Mark as initialized
        self._needs_init = False
        
        # Setup logger only once
        self.logger = setup_component_logger(__name__)
        self.logger.info("Initializing MetricsCollector singleton instance")
        
        # ALWAYS use a path relative to the application directory for better portability
        # Store DB in the 'data' directory relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(current_dir), "data")
        # Ensure the data directory exists
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "metrics.db")
        
        # Store the database path
        self.db_path = db_path
        self.logger.info(f"Using database at: {self.db_path}")
        
        # Initialize Prometheus metrics only once
        if not hasattr(self, 'registry'):
            self.registry = CollectorRegistry()
            
            # Create Prometheus metrics
            self.ad_requests_counter = Counter(
                'ad_requests_total', 
                'Total number of ad requests',
                registry=self.registry
            )
            
            self.ad_impressions_counter = Counter(
                'ad_impressions_total', 
                'Total number of ad impressions',
                registry=self.registry
            )
            
            self.ad_clicks_counter = Counter(
                'ad_clicks_total', 
                'Total number of ad clicks',
                registry=self.registry
            )
            
            self.query_processing_time = Histogram(
                'query_processing_seconds',
                'Time spent processing queries',
                registry=self.registry
            )
            
            self.active_users_gauge = Gauge(
                'active_users', 
                'Number of active users',
                registry=self.registry
            )
            
            # Add system metrics
            self.cpu_usage_gauge = Gauge(
                'cpu_usage_percent',
                'CPU usage percentage',
                registry=self.registry
            )
            
            self.memory_usage_gauge = Gauge(
                'memory_usage_percent',
                'Memory usage percentage',
                registry=self.registry
            )
            
            self.disk_usage_gauge = Gauge(
                'disk_usage_percent',
                'Disk usage percentage',
                registry=self.registry
            )
        
        # Start Prometheus HTTP server on port 8005
        try:
            # Get port from environment or use default
            prometheus_port = int(os.environ.get('PROMETHEUS_PORT', 8005))
            start_http_server(prometheus_port, registry=self.registry)
            self.logger.info(f"Prometheus metrics server started on port {prometheus_port}")
        except Exception as e:
            self.logger.warning(f"Could not start Prometheus server: {e}")
            
        # Create tables in the main thread
        self._get_db_connection(create_tables=True)
        
        # Start tracking system metrics
        self._start_system_metrics_tracking()
        
    def _start_system_metrics_tracking(self):
        """Start a background thread to track system metrics"""
        def update_system_metrics():
            while True:
                try:
                    # Update CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.cpu_usage_gauge.set(cpu_percent)
                    
                    # Update memory usage
                    memory = psutil.virtual_memory()
                    self.memory_usage_gauge.set(memory.percent)
                    
                    # Update disk usage
                    disk = psutil.disk_usage('/')
                    self.disk_usage_gauge.set(disk.percent)
                    
                    # Log system metrics to database
                    self.log_system_metrics(cpu_percent, memory.percent, disk.percent)
                    
                    # Sleep for 5 seconds
                    time.sleep(5)
                except Exception as e:
                    self.logger.error(f"Error updating system metrics: {e}")
                    time.sleep(10)  # Wait longer if there was an error
        
        # Start the thread
        metrics_thread = threading.Thread(target=update_system_metrics, daemon=True)
        metrics_thread.start()
        self.logger.info("System metrics tracking started")

    def log_system_metrics(self, cpu_percent, memory_percent, disk_percent):
        """Log system metrics to the database"""
        try:
            timestamp = datetime.now().isoformat()
            data = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent
            }
            
            # Convert data to JSON string
            data_json = json.dumps(data)
            
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events (timestamp, event_type, data) VALUES (?, ?, ?)",
                (timestamp, "system_metrics", data_json)
            )
            conn.commit()
        except Exception as e:
            self.logger.error(f"Error logging system metrics: {e}")

    def get_system_health(self) -> Dict[str, Any]:
        """Get real-time system health metrics"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            # Get system uptime
            uptime_seconds = time.time() - self._start_time
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m"
            elif hours > 0:
                uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            else:
                uptime_str = f"{int(minutes)}m {int(seconds)}s"
            
            # Get system info
            system_info = {
                "os": platform.system(),
                "version": platform.version(),
                "processor": platform.processor()
            }
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "uptime": uptime_str,
                "uptime_seconds": uptime_seconds,
                "system_info": system_info
            }
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0, 
                "disk_percent": 0,
                "uptime": "Unknown",
                "uptime_seconds": 0,
                "system_info": {
                    "os": "Unknown",
                    "version": "Unknown",
                    "processor": "Unknown"
                },
                "error": str(e)
            }

    def get_historic_system_metrics(self, limit=100):
        """Get historical system metrics from database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events WHERE event_type = 'system_metrics' ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            
            columns = [column[0] for column in cursor.description]
            events = []
            
            for row in cursor.fetchall():
                event = dict(zip(columns, row))
                # Parse the JSON data
                event['data'] = json.loads(event['data'])
                events.append(event)
                
            return events
        except Exception as e:
            self.logger.error(f"Error getting historic system metrics: {e}")
            return []

    def _get_db_connection(self, create_tables=False):
        """Get a thread-local database connection."""
        if not hasattr(_thread_local, 'db_conn'):
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            _thread_local.db_conn = sqlite3.connect(self.db_path)
            if create_tables:
                self.create_tables_if_not_exist(_thread_local.db_conn)
        return _thread_local.db_conn

    def create_tables_if_not_exist(self, conn):
        """Create tables if they don't exist."""
        cursor = conn.cursor()
        
        # Create ad_impressions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ad_impressions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            query TEXT,
            ad_id TEXT,
            relevance_score REAL
        )
        ''')
        
        # Create ad_clicks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ad_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ad_id TEXT,
            user_id TEXT
        )
        ''')
        
        # Create model_generations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            query TEXT,
            response TEXT,
            model TEXT,
            generation_time REAL
        )
        ''')
        
        # Create events table for general event logging
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            data TEXT
        )
        ''')
        
        conn.commit()

    def log_ad_impression(self, query, ad_id, relevance_score):
        """Log an ad impression."""
        timestamp = datetime.now().isoformat()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ad_impressions (timestamp, query, ad_id, relevance_score) VALUES (?, ?, ?, ?)",
            (timestamp, query, ad_id, relevance_score)
        )
        conn.commit()
        
        # Update Prometheus metrics
        self.ad_impressions_counter.inc()
        
        self.logger.info(f"Ad impression logged: query='{query}', ad_id='{ad_id}', relevance_score={relevance_score}")

    def log_ad_click(self, ad_id, user_id):
        """Log an ad click."""
        timestamp = datetime.now().isoformat()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ad_clicks (timestamp, ad_id, user_id) VALUES (?, ?, ?)",
            (timestamp, ad_id, user_id)
        )
        conn.commit()
        
        # Update Prometheus metrics
        self.ad_clicks_counter.inc()
        
        self.logger.info(f"Ad click logged: ad_id='{ad_id}', user_id='{user_id}'")

    def log_model_generation(self, query, response, model, generation_time):
        """Log a model generation."""
        timestamp = datetime.now().isoformat()
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO model_generations (timestamp, query, response, model, generation_time) VALUES (?, ?, ?, ?, ?)",
            (timestamp, query, response, model, generation_time)
        )
        conn.commit()
        
        # Update Prometheus metrics
        self.query_processing_time.observe(generation_time)
        
        self.logger.info(f"Model generation logged: query='{query}', model='{model}', generation_time={generation_time}s")

    def log_ad_event(self, event_type, data):
        """Log a generic ad-related event."""
        timestamp = datetime.now().isoformat()
        
        # Convert data to JSON string
        data_json = json.dumps(data)
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (timestamp, event_type, data) VALUES (?, ?, ?)",
            (timestamp, event_type, data_json)
        )
        conn.commit()
        
        # Log the event
        self.logger.info(f"Event logged: type='{event_type}', data={data}")

    def get_ad_impressions(self, limit=100):
        """Get recent ad impressions."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ad_impressions ORDER BY timestamp DESC LIMIT ?", (limit,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_ad_clicks(self, limit=100):
        """Get recent ad clicks."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ad_clicks ORDER BY timestamp DESC LIMIT ?", (limit,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_model_generations(self, limit=100):
        """Get recent model generations."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM model_generations ORDER BY timestamp DESC LIMIT ?", (limit,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_events(self, event_type=None, limit=100):
        """Get recent events, optionally filtered by event_type."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute("SELECT * FROM events WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?", 
                          (event_type, limit))
        else:
            cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
            
        columns = [column[0] for column in cursor.description]
        events = []
        
        for row in cursor.fetchall():
            event = dict(zip(columns, row))
            # Parse the JSON data
            event['data'] = json.loads(event['data'])
            events.append(event)
            
        return events

    def get_metrics_summary(self):
        """Get a summary of metrics."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Count total ad impressions
        cursor.execute("SELECT COUNT(*) FROM ad_impressions")
        total_impressions = cursor.fetchone()[0]
        
        # Count total ad clicks
        cursor.execute("SELECT COUNT(*) FROM ad_clicks")
        total_clicks = cursor.fetchone()[0]
        
        # Count total model generations
        cursor.execute("SELECT COUNT(*) FROM model_generations")
        total_generations = cursor.fetchone()[0]
        
        # Calculate average generation time
        cursor.execute("SELECT AVG(generation_time) FROM model_generations")
        avg_generation_time = cursor.fetchone()[0] or 0
        
        # Get most recent events
        recent_events = self.get_events(limit=5)
        
        # Get system health
        system_health = self.get_system_health()
        
        return {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_generations": total_generations,
            "avg_generation_time": avg_generation_time,
            "recent_events": recent_events,
            "system_health": system_health
        }

    def close_connection(self):
        """Close the database connection for the current thread."""
        if hasattr(_thread_local, 'db_conn'):
            _thread_local.db_conn.close()
            del _thread_local.db_conn

    def export_metrics_to_csv(self, directory=None):
        """Export all metrics to CSV files."""
        # If no directory is specified, use a subdirectory of where the database is
        if directory is None:
            directory = os.path.join(os.path.dirname(self.db_path), "exports")
        
        # Create the directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
            
        # Get the current timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        conn = self._get_db_connection()
        
        # Export ad impressions
        impressions = pd.read_sql_query("SELECT * FROM ad_impressions", conn)
        impressions_file = os.path.join(directory, f"ad_impressions_{timestamp}.csv")
        impressions.to_csv(impressions_file, index=False)
        
        # Export ad clicks
        clicks = pd.read_sql_query("SELECT * FROM ad_clicks", conn)
        clicks_file = os.path.join(directory, f"ad_clicks_{timestamp}.csv") 
        clicks.to_csv(clicks_file, index=False)
        
        # Export model generations
        generations = pd.read_sql_query("SELECT * FROM model_generations", conn)
        generations_file = os.path.join(directory, f"model_generations_{timestamp}.csv")
        generations.to_csv(generations_file, index=False)
        
        # Export events
        events = pd.read_sql_query("SELECT * FROM events", conn)
        events_file = os.path.join(directory, f"events_{timestamp}.csv")
        events.to_csv(events_file, index=False)
        
        self.logger.info(f"Metrics exported to {directory} directory")
        
        return {
            "impressions": impressions_file,
            "clicks": clicks_file,
            "generations": generations_file,
            "events": events_file
        }

# Standalone metric functions for easier imports and usage in other modules

def record_user_engagement_metric(metric_name, value=1, user_id=None, session_id=None, context=None):
    """
    Record a user engagement metric.
    
    Args:
        metric_name: The name of the metric to record
        value: The value of the metric (default: 1)
        user_id: The ID of the user (optional)
        session_id: The ID of the session (optional)
        context: Additional context data (optional)
    """
    collector = MetricsCollector()
    data = {
        "metric_name": metric_name,
        "value": value,
        "timestamp": datetime.now().isoformat()
    }
    
    if user_id:
        data["user_id"] = user_id
    if session_id:
        data["session_id"] = session_id
    if context:
        data["context"] = context
        
    collector.log_event("user_engagement", data)
    collector.logger.info(f"Recorded user engagement metric: {metric_name} = {value}")

def record_advertiser_metric(advertiser_id, metric_name, value=1, ad_id=None, campaign_id=None, context=None):
    """
    Record an advertiser-related metric.
    
    Args:
        advertiser_id: The ID of the advertiser
        metric_name: The name of the metric to record
        value: The value of the metric (default: 1)
        ad_id: The ID of the ad (optional)
        campaign_id: The ID of the campaign (optional)
        context: Additional context data (optional)
    """
    collector = MetricsCollector()
    data = {
        "advertiser_id": advertiser_id,
        "metric_name": metric_name,
        "value": value,
        "timestamp": datetime.now().isoformat()
    }
    
    if ad_id:
        data["ad_id"] = ad_id
    if campaign_id:
        data["campaign_id"] = campaign_id
    if context:
        data["context"] = context
        
    collector.log_event("advertiser_metric", data)
    collector.logger.info(f"Recorded advertiser metric for {advertiser_id}: {metric_name} = {value}")

def record_system_metric(metric_name, value, component=None, context=None):
    """
    Record a system-level metric.
    
    Args:
        metric_name: The name of the metric to record
        value: The value of the metric
        component: The system component (optional)
        context: Additional context data (optional)
    """
    collector = MetricsCollector()
    data = {
        "metric_name": metric_name,
        "value": value,
        "timestamp": datetime.now().isoformat()
    }
    
    if component:
        data["component"] = component
    if context:
        data["context"] = context
        
    collector.log_event("system_metric", data)
    collector.logger.info(f"Recorded system metric: {metric_name} = {value}")















































