# Ad Service System

## Quick Start Guide

1. **Prerequisites**
   - Python 3.8 or higher
   - PowerShell (Windows) or Bash (Linux/Mac)
   - SQLite (will be installed automatically if missing)

2. **Initial Setup**
   ```powershell
   # Clone or extract the newstruc folder
   cd newstruc

   # Set environment variables (Required)
   $env:AD_SERVICE_ROOT = (Get-Location).Path

   # Run setup script
   .\setup.ps1
   ```

3. **Start the Service**
   ```powershell
   # Start with interactive menu
   .\start_ad_service.ps1

   # Or start directly
   .\start_ad_service.ps1 -action start
   ```

4. **Access the Service**
   - Chat Interface: http://localhost:8501
   - Ad Manager: http://localhost:8502
   - Metrics Dashboard: http://localhost:8503

## Directory Structure
```
newstruc/
├── companies/           # Company configurations and ads
├── ad_service/         # Core service code
├── config/            # System configuration
├── charts/           # Generated analytics charts
├── logs/            # Service logs
└── .streamlit/      # Streamlit configuration
```

## Configuration

1. **Company Setup**
   - Place company configurations in `companies/{company_name}/config/`
   - Add ad campaigns in `companies/{company_name}/ads/`

2. **System Configuration**
   - Main config: `config/config.yaml`
   - Environment variables: `.env`

## Common Operations

1. **View Recent Ad Impressions**
   ```powershell
   .\start_ad_service.ps1 -action metrics
   ```

2. **Check Service Status**
   ```powershell
   .\start_ad_service.ps1 -action status
   ```

3. **Stop Service**
   ```powershell
   .\start_ad_service.ps1 -action stop
   ```

## Troubleshooting

1. If the service fails to start:
   - Check Python version: `python --version`
   - Verify environment variable: `echo $env:AD_SERVICE_ROOT`
   - Check logs in `logs/` directory

2. If ads aren't loading:
   - Verify company configurations in `companies/` directory
   - Check ad campaign files format
   - Review service logs for errors

## Support

For additional help:
- Run `.\start_ad_service.ps1 -action menu` for all available commands
- Check documentation in `docs/` directory
- Review service logs in `logs/` directory

## System Overview

This system is an integrated ad service application that consists of several key components:

1. **Chat Interface**: A Streamlit-based conversational interface where users can interact with an AI assistant. The system displays relevant ads based on user queries.

2. **Ad Manager UI**: Admin interface for creating, viewing, and managing ads.

3. **Metrics Collection**: Comprehensive tracking of user interactions, ad impressions, and system performance.

4. **Database**: SQLite database (`metrics.db`) that stores all collected metrics.

## How to Access Components

### Starting the Service

To start the entire service (including all components):

```powershell
cd C:\almostworks
python ad_service/start_service.py
```

This will start:
- The chat interface at http://localhost:8501
- The metrics dashboard at http://localhost:8000/metrics

### Accessing Individual Components

1. **Chat Interface**: 
   - URL: http://localhost:8501 
   - This is where end users interact with the AI assistant and see relevant ads

2. **Ad Manager UI**:
   - URL: http://localhost:8501/ad_manager
   - Admin interface for creating and managing ads
   - To create a new ad, use the "Create New Ad" tab and fill in the required fields

3. **Metrics Dashboard**:
   - URL: http://localhost:8000/metrics
   - Visual dashboard showing real-time metrics

## Working with Metrics

### Using the Query Script

The system includes a PowerShell script (`query_metrics_db.ps1`) for directly querying the metrics database:

```powershell
cd C:\almostworks
.\query_metrics_db.ps1 -query "YOUR_SQL_QUERY_HERE"
```

### Common Queries

1. **Recent Ad Impressions**:
   ```
   .\query_metrics_db.ps1 -query "SELECT * FROM ad_impressions ORDER BY timestamp DESC LIMIT 10;"
   ```

2. **Model Generation Performance**:
   ```
   .\query_metrics_db.ps1 -query "SELECT AVG(generation_time) as avg_time, MIN(generation_time) as min_time, MAX(generation_time) as max_time FROM model_generations;"
   ```

3. **Daily Ad Impressions Count**:
   ```
   .\query_metrics_db.ps1 -query "SELECT strftime('%Y-%m-%d', timestamp) as date, count(*) as impression_count FROM ad_impressions GROUP BY date ORDER BY date DESC;"
   ```

4. **System Performance Metrics**:
   ```
   .\query_metrics_db.ps1 -query "SELECT * FROM events WHERE event_type = 'system_metrics' ORDER BY timestamp DESC LIMIT 5;"
   ```

## How Everything Connects

### Data Flow

1. **User Interaction**:
   - User submits a query through the chat interface
   - The query is processed by the language model (GPT-3.5-turbo)
   - The system records the query and response in the `model_generations` table

2. **Ad Delivery**:
   - The ad delivery system analyzes the user's query
   - It matches the query against available ads' keywords/categories
   - Relevant ads are selected based on relevance score and system configuration
   - Selected ads are displayed to the user
   - The system records the impression in the `ad_impressions` table

3. **Metrics Collection**:
   - All interactions are continuously logged to the `metrics.db` SQLite database
   - System metrics are also collected at regular intervals

### System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Chat Interface │────>│  Ad Delivery     │────>│  Ad Manager     │
│  (Streamlit)    │<────│  System          │<────│  (Configuration) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                       │
        │                        │                       │
        │                        ▼                       │
        │               ┌──────────────────┐            │
        └──────────────>│  Metrics         │<───────────┘
                        │  Collection      │
                        └──────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  SQLite DB       │
                        │  (metrics.db)    │
                        └──────────────────┘
```

## Stopping the Service

To stop the running service:

```powershell
Get-Process -Name python | Where-Object {$_.CommandLine -like "*start_service.py*"} | Stop-Process
```

## License

This project is proprietary. All rights reserved. 