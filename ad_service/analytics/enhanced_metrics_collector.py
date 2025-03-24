"""
Enhanced Metrics Collector Module

This module extends the basic metrics collector with additional functionality.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import json
import logging
from .metrics_collector import MetricsCollector

class EnhancedMetricsCollector(MetricsCollector):
    def __init__(self):
        # Avoid double initialization of logging
        if not hasattr(self, 'logger'):
            super().__init__()
        
    def get_campaign_analytics(
        self, 
        campaign_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get campaign analytics with proper validation"""
        cursor = self._get_db_connection().cursor()
        
        # Validate date range
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
            
        # Convert datetime objects to strings for SQLite
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        
        # Get impressions and clicks
        cursor.execute("""
            SELECT COUNT(*) as impressions,
                   SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as clicks,
                   SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) as conversions,
                   SUM(CASE WHEN event_type = 'conversion' THEN json_extract(data, '$.conversion_value') ELSE 0 END) as revenue
            FROM events
            WHERE json_extract(data, '$.campaign_id') = ? 
            AND timestamp BETWEEN ? AND ?
        """, (campaign_id, start_date_str, end_date_str))
        
        result = cursor.fetchone()
        
        # Calculate derived metrics with null checks
        impressions = result[0] or 0
        clicks = result[1] or 0
        conversions = result[2] or 0
        revenue = result[3] or 0
        
        # Get cost data from the database 
        cursor.execute("""
            SELECT SUM(json_extract(data, '$.cost')) as total_cost
            FROM events
            WHERE event_type = 'campaign_cost' 
            AND json_extract(data, '$.campaign_id') = ?
            AND timestamp BETWEEN ? AND ?
        """, (campaign_id, start_date_str, end_date_str))
        
        cost_result = cursor.fetchone()
        cost = cost_result[0] or 0
        
        # If no cost records exist yet, use a default cost based on impressions
        if cost == 0 and impressions > 0:
            cost = impressions * 0.01  # Estimate $0.01 per impression
        
        return {
            'impressions': impressions,
            'clicks': clicks,
            'conversions': conversions,
            'revenue': revenue,
            'cost': cost,
            'ctr': (clicks / impressions * 100) if impressions > 0 else 0,
            'conversion_rate': (conversions / clicks * 100) if clicks > 0 else 0,
            'roas': revenue / cost if cost > 0 else 0
        }
        
    def get_performance_metrics(self, campaign_id: str) -> pd.DataFrame:
        """Get performance metrics for a campaign from the database"""
        cursor = self._get_db_connection().cursor()
        
        # Query for click-through rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN event_type = 'click' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(CASE WHEN event_type = 'impression' THEN 1 END), 0) as ctr,
                COUNT(CASE WHEN event_type = 'conversion' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(CASE WHEN event_type = 'click' THEN 1 END), 0) as conversion_rate,
                COUNT(CASE WHEN json_extract(data, '$.bounce') = 'true' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(CASE WHEN event_type = 'session' THEN 1 END), 0) as bounce_rate
            FROM events
            WHERE json_extract(data, '$.campaign_id') = ?
        """, (campaign_id,))
        
        result = cursor.fetchone()
        
        if result:
            return pd.DataFrame({
                'metric': ['CTR', 'Conversion Rate', 'Bounce Rate'],
                'value': [
                    result[0] or 0, 
                    result[1] or 0, 
                    result[2] or 0
                ],
                'change': [0, 0, 0]  # No historical comparison yet
            })
        else:
            # Provide empty dataframe with correct structure if no data
            return pd.DataFrame({
                'metric': ['CTR', 'Conversion Rate', 'Bounce Rate'],
                'value': [0, 0, 0],
                'change': [0, 0, 0]
            })
    
    def get_time_series_metrics(self, campaign_id: str) -> pd.DataFrame:
        """Get time series metrics for a campaign from the database"""
        cursor = self._get_db_connection().cursor()
        
        # Get events grouped by day
        cursor.execute("""
            SELECT 
                date(timestamp) as event_date,
                COUNT(CASE WHEN event_type = 'impression' THEN 1 END) as impressions,
                COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                SUM(CASE WHEN event_type = 'conversion' THEN json_extract(data, '$.conversion_value') ELSE 0 END) as revenue,
                SUM(CASE WHEN event_type = 'campaign_cost' THEN json_extract(data, '$.cost') ELSE 0 END) as cost
            FROM events
            WHERE json_extract(data, '$.campaign_id') = ?
            GROUP BY date(timestamp)
            ORDER BY date(timestamp)
        """, (campaign_id,))
        
        rows = cursor.fetchall()
        
        if rows:
            # Convert to dataframe
            df = pd.DataFrame(rows, columns=['dates', 'impressions', 'clicks', 'revenue', 'cost'])
            
            # Calculate derived metrics
            df['ctr'] = df.apply(lambda x: (x['clicks'] / x['impressions'] * 100) if x['impressions'] > 0 else 0, axis=1)
            df['conversion_rate'] = df.apply(lambda x: (x['revenue'] / x['clicks'] * 100) if x['clicks'] > 0 else 0, axis=1)
            
            return df
        else:
            # If no data, return a dataframe with the last 30 days
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            return pd.DataFrame({
                'dates': dates,
                'impressions': [0] * len(dates),
                'clicks': [0] * len(dates),
                'revenue': [0] * len(dates),
                'cost': [0] * len(dates),
                'ctr': [0] * len(dates),
                'conversion_rate': [0] * len(dates)
            })
    
    def get_engagement_funnel(self, campaign_id: str) -> Dict[str, List]:
        """Get engagement funnel data from the database"""
        cursor = self._get_db_connection().cursor()
        
        # Get funnel metrics
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN event_type = 'impression' THEN 1 END) as impressions,
                COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                COUNT(CASE WHEN event_type = 'signup' THEN 1 END) as signups,
                COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchases
            FROM events
            WHERE json_extract(data, '$.campaign_id') = ?
        """, (campaign_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'stages': ['Impressions', 'Clicks', 'Sign-ups', 'Purchases'],
                'values': [
                    result[0] or 0,
                    result[1] or 0,
                    result[2] or 0,
                    result[3] or 0
                ]
            }
        else:
            # Return zero values if no data
            return {
                'stages': ['Impressions', 'Clicks', 'Sign-ups', 'Purchases'],
                'values': [0, 0, 0, 0]
            }
    
    def get_audience_insights(self, campaign_id: str) -> pd.DataFrame:
        """Get audience insights from the database"""
        cursor = self._get_db_connection().cursor()
        
        # Get device type distribution
        cursor.execute("""
            SELECT 
                json_extract(data, '$.device_type') as segment,
                COUNT(*) as count
            FROM events
            WHERE json_extract(data, '$.campaign_id') = ?
            AND json_extract(data, '$.device_type') IS NOT NULL
            GROUP BY json_extract(data, '$.device_type')
            ORDER BY count DESC
        """, (campaign_id,))
        
        rows = cursor.fetchall()
        
        if rows:
            return pd.DataFrame(rows, columns=['segment', 'count'])
        else:
            # Return placeholder structure if no data
            return pd.DataFrame({
                'segment': ['Mobile', 'Desktop', 'Tablet'],
                'count': [0, 0, 0]
            })
    
    def get_geographic_performance(self, campaign_id: str) -> pd.DataFrame:
        """Get geographic performance from the database"""
        cursor = self._get_db_connection().cursor()
        
        # Get country performance
        cursor.execute("""
            SELECT 
                json_extract(data, '$.country_code') as country_code,
                json_extract(data, '$.country') as country,
                COUNT(*) as count
            FROM events
            WHERE json_extract(data, '$.campaign_id') = ?
            AND json_extract(data, '$.country') IS NOT NULL
            GROUP BY json_extract(data, '$.country_code'), json_extract(data, '$.country')
            ORDER BY count DESC
            LIMIT 10
        """, (campaign_id,))
        
        rows = cursor.fetchall()
        
        if rows:
            df = pd.DataFrame(rows, columns=['country_code', 'country', 'count'])
            # Calculate normalized performance score (0-100)
            max_count = df['count'].max()
            df['performance_score'] = df['count'] / max_count * 100 if max_count > 0 else 0
            return df
        else:
            # Return an empty dataframe with the correct structure
            return pd.DataFrame({
                'country_code': [],
                'country': [],
                'performance_score': []
            })
    
    def get_roi_analysis(self, campaign_id: str) -> pd.DataFrame:
        """Get ROI analysis from the database"""
        cursor = self._get_db_connection().cursor()
        
        # Get revenue and cost
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN event_type = 'conversion' THEN json_extract(data, '$.conversion_value') ELSE 0 END) as revenue,
                SUM(CASE WHEN event_type = 'campaign_cost' THEN json_extract(data, '$.cost') ELSE 0 END) as cost
            FROM events
            WHERE json_extract(data, '$.campaign_id') = ?
        """, (campaign_id,))
        
        result = cursor.fetchone()
        
        if result:
            revenue = result[0] or 0
            cost = result[1] or 0
            roi = ((revenue - cost) / cost * 100) if cost > 0 else 0
            
            return pd.DataFrame({
                'metric': ['Revenue', 'Cost', 'ROI'],
                'value': [revenue, cost, roi]
            })
        else:
            # Return zero values if no data
            return pd.DataFrame({
                'metric': ['Revenue', 'Cost', 'ROI'],
                'value': [0, 0, 0]
            })

    def get_system_metrics(self) -> pd.DataFrame:
        """Get system metrics from real-time monitoring"""
        # Use the get_system_health method from parent class
        system_health = self.get_system_health()
        
        # Format the data as a DataFrame
        return pd.DataFrame({
            'metric': ['Response Time', 'CPU Usage', 'Uptime'],
            'value': [
                f"{self.get_avg_response_time():.2f}ms",
                f"{system_health.get('cpu_percent', 0):.1f}%",
                system_health.get('uptime', 'Unknown')
            ]
        })
    
    def get_avg_response_time(self) -> float:
        """Get average response time from the database"""
        cursor = self._get_db_connection().cursor()
        
        # Get average generation time in milliseconds
        cursor.execute("""
            SELECT AVG(generation_time) * 1000 as avg_response_time
            FROM model_generations
        """)
        
        result = cursor.fetchone()
        return result[0] or 0

    def get_active_campaigns(self) -> List[str]:
        """
        Get a list of active campaign IDs from the database
        
        Returns:
            List[str]: List of active campaign IDs
        """
        cursor = self._get_db_connection().cursor()
        
        # Get distinct campaign IDs
        cursor.execute("""
            SELECT DISTINCT json_extract(data, '$.campaign_id') as campaign_id
            FROM events
            WHERE json_extract(data, '$.campaign_id') IS NOT NULL
        """)
        
        campaigns = [row[0] for row in cursor.fetchall() if row[0]]
        
        # If no campaigns in database, add a default one
        if not campaigns:
            campaigns = ["all_campaigns"]
            
            # Record a campaign creation event
            self.log_ad_event("campaign_creation", {
                "campaign_id": "all_campaigns",
                "name": "All Campaigns",
                "created_at": datetime.now().isoformat()
            })
        
        return campaigns
