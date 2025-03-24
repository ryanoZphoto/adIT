#!/usr/bin/env python3
"""
Metrics Visualization Script
----------------------------
This script generates visualizations from the metrics database
to help analyze system performance and user interactions.
"""

import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import os
import json
from datetime import datetime
from pathlib import Path
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description='Generate visualizations from metrics database')
parser.add_argument('--output', '-o', default='charts', help='Output directory for charts')
parser.add_argument('--db', default='ad_service/data/metrics.db', help='Path to metrics.db file')
parser.add_argument('--type', '-t', choices=['all', 'impressions', 'performance', 'system'], 
                    default='all', help='Type of charts to generate')
args = parser.parse_args()

# Create output directory if it doesn't exist
output_dir = Path(args.output)
output_dir.mkdir(exist_ok=True, parents=True)

# Connect to the database
db_path = Path(args.db)
if not db_path.exists():
    print(f"Error: Database file not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)

def generate_impressions_charts():
    """Generate charts related to ad impressions"""
    print("Generating ad impressions charts...")
    
    # Query for ad impressions over time
    df = pd.read_sql_query("""
        SELECT 
            strftime('%Y-%m-%d %H:%M', timestamp) as time_period, 
            COUNT(*) as impression_count
        FROM ad_impressions 
        GROUP BY time_period
        ORDER BY time_period
    """, conn)
    
    if df.empty:
        print("No ad impression data found")
        return
    
    # Convert to datetime for better plotting
    df['time_period'] = pd.to_datetime(df['time_period'])
    
    # Plot impressions over time
    plt.figure(figsize=(12, 6))
    plt.plot(df['time_period'], df['impression_count'], marker='o', linestyle='-')
    plt.title('Ad Impressions Over Time')
    plt.xlabel('Time')
    plt.ylabel('Number of Impressions')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / 'impressions_over_time.png')
    plt.close()
    
    # Query for top ads by impressions
    df = pd.read_sql_query("""
        SELECT 
            ad_id, 
            COUNT(*) as impression_count
        FROM ad_impressions 
        GROUP BY ad_id
        ORDER BY impression_count DESC
        LIMIT 10
    """, conn)
    
    if not df.empty:
        plt.figure(figsize=(12, 6))
        bars = plt.bar(df['ad_id'], df['impression_count'])
        plt.title('Top 10 Ads by Impressions')
        plt.xlabel('Ad ID')
        plt.ylabel('Number of Impressions')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'top_ads_by_impressions.png')
        plt.close()
    
    # Query for relevance score distribution
    df = pd.read_sql_query("""
        SELECT relevance_score
        FROM ad_impressions 
    """, conn)
    
    if not df.empty:
        plt.figure(figsize=(10, 6))
        plt.hist(df['relevance_score'], bins=20, alpha=0.7, color='blue', edgecolor='black')
        plt.title('Distribution of Ad Relevance Scores')
        plt.xlabel('Relevance Score')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / 'relevance_score_distribution.png')
        plt.close()

def generate_performance_charts():
    """Generate charts related to model performance"""
    print("Generating model performance charts...")
    
    # Query for model generation times
    df = pd.read_sql_query("""
        SELECT 
            strftime('%Y-%m-%d %H:%M', timestamp) as time_period, 
            generation_time
        FROM model_generations 
        ORDER BY timestamp
    """, conn)
    
    if df.empty:
        print("No model generation data found")
        return
    
    # Convert to datetime for better plotting
    df['time_period'] = pd.to_datetime(df['time_period'])
    
    # Plot generation times over time
    plt.figure(figsize=(12, 6))
    plt.plot(df['time_period'], df['generation_time'], marker='.', linestyle='-', alpha=0.6)
    plt.title('Model Generation Times')
    plt.xlabel('Time')
    plt.ylabel('Generation Time (seconds)')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # Add rolling average
    if len(df) >= 5:  # Only if we have enough data
        window_size = min(5, len(df))
        df['rolling_avg'] = df['generation_time'].rolling(window=window_size).mean()
        plt.plot(df['time_period'], df['rolling_avg'], color='red', linewidth=2, 
                 label=f'{window_size}-point Rolling Average')
        plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'generation_times.png')
    plt.close()
    
    # Query for model type distribution and performance
    df = pd.read_sql_query("""
        SELECT 
            model, 
            COUNT(*) as count,
            AVG(generation_time) as avg_time,
            MIN(generation_time) as min_time,
            MAX(generation_time) as max_time
        FROM model_generations 
        GROUP BY model
    """, conn)
    
    if not df.empty:
        plt.figure(figsize=(10, 6))
        bars = plt.bar(df['model'], df['avg_time'], yerr=df['max_time']-df['avg_time'], 
                      capsize=5, alpha=0.7, color='green')
        plt.title('Average Generation Time by Model Type')
        plt.xlabel('Model')
        plt.ylabel('Average Generation Time (seconds)')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{height:.2f}s', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'model_performance_comparison.png')
        plt.close()

def generate_system_charts():
    """Generate charts related to system metrics"""
    print("Generating system performance charts...")
    
    # Query for system metrics
    df = pd.read_sql_query("""
        SELECT 
            timestamp,
            data
        FROM events 
        WHERE event_type = 'system_metrics'
        ORDER BY timestamp
    """, conn)
    
    if df.empty:
        print("No system metrics data found")
        return
    
    # Parse JSON data
    metrics = []
    for _, row in df.iterrows():
        try:
            data = json.loads(row['data'])
            data['timestamp'] = row['timestamp']
            metrics.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    
    if not metrics:
        print("No valid system metrics data found")
        return
    
    # Create DataFrame from metrics
    metrics_df = pd.DataFrame(metrics)
    metrics_df['timestamp'] = pd.to_datetime(metrics_df['timestamp'])
    
    # Create subplots for CPU, memory, and disk usage
    fig, axs = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    
    # CPU usage
    if 'cpu_percent' in metrics_df.columns:
        axs[0].plot(metrics_df['timestamp'], metrics_df['cpu_percent'], 
                   marker='.', linestyle='-', color='red')
        axs[0].set_title('CPU Usage Over Time')
        axs[0].set_ylabel('CPU Usage (%)')
        axs[0].grid(True, alpha=0.3)
    
    # Memory usage
    if 'memory_percent' in metrics_df.columns:
        axs[1].plot(metrics_df['timestamp'], metrics_df['memory_percent'], 
                   marker='.', linestyle='-', color='blue')
        axs[1].set_title('Memory Usage Over Time')
        axs[1].set_ylabel('Memory Usage (%)')
        axs[1].grid(True, alpha=0.3)
    
    # Disk usage
    if 'disk_percent' in metrics_df.columns:
        axs[2].plot(metrics_df['timestamp'], metrics_df['disk_percent'], 
                   marker='.', linestyle='-', color='green')
        axs[2].set_title('Disk Usage Over Time')
        axs[2].set_ylabel('Disk Usage (%)')
        axs[2].grid(True, alpha=0.3)
    
    plt.xlabel('Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / 'system_metrics.png')
    plt.close()

# Generate charts based on selected type
if args.type in ['all', 'impressions']:
    generate_impressions_charts()

if args.type in ['all', 'performance']:
    generate_performance_charts()

if args.type in ['all', 'system']:
    generate_system_charts()

# Close connection
conn.close()

print(f"Charts have been generated and saved to {output_dir}/")
print("To view the charts, navigate to this directory in File Explorer.") 