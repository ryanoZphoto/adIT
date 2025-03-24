# AdServ: Architecture Overview

## Introduction

AdServ is a sophisticated AI-powered advertising service designed to deliver contextually relevant ads within conversational AI platforms. The system utilizes OpenAI's language models to understand user queries, match them with suitable advertisements from a vector database, and integrate personalized ad content into conversations.

## System Architecture

Based on the observed file structure and server output, the system appears to be organized into the following core components:

### 1. Ad Matching System

Located in `ad_service/ad_matching/`, this component is responsible for finding relevant ads based on user queries:

- **ad_repository.py**: Manages the storage and retrieval of ads from the vector database
- **query_analyzer.py**: Analyzes user queries to extract intent, context, and keywords
- **ranking_engine.py**: Ranks matched ads based on relevance, user preferences, and advertiser priorities
- **ad_matcher.py**: Orchestrates the matching process between user queries and available ads

### 2. Ad Delivery System

Located in `ad_service/ad_delivery/`, this component handles the delivery of matched ads:

- **delivery_pipeline.py**: Orchestrates the end-to-end process from query to ad delivery
- **ad_delivery_manager.py**: Manages when and how ads are delivered

### 3. Ad Generation and Formatting

Located in `ad_service/services/` and other directories:

- **ad_generator.py**: Generates dynamic, contextually appropriate ad copy using AI
- **ad_formatter.py**: Formats ads appropriately for different platforms and contexts

### 4. Analytics and Tracking

Located in `ad_service/analytics/`:

- **dashboard.py**: Provides visualization of ad performance metrics
- **alert_manager.py**: Manages alerts for system issues or performance thresholds

### 5. Web Interface (GUI)

Located in `ad_service/gui/`:

- **pages/**: Different pages of the web interface (analytics, etc.)
- **components/**: Reusable UI components:
  - **sidebar.py**: Navigation sidebar
  - **header.py**: Page header
  - **debug_panel.py** and **debug.py**: Debugging tools
  - **analytics_dashboard.py**: Analytics visualization
  - **chat.py**: Chat interface for testing ad delivery

### 6. Testing Suite

Located in `ad_service/tests/`:

- **test_ad_delivery_manager.py**
- **test_ad_formatter.py**
- **test_ad_generator.py**
- **test_ad_tracker.py**
- **test_delivery_pipeline.py**

## API Endpoints

The service exposes various API endpoints:

- `/api/health`: Health check endpoint
- `/`: Main entry point (redirects to another route)
- Likely additional endpoints for ad matching, delivery, and analytics

## Technologies Used

Based on the observed structure, the system appears to use:

1. **Flask**: Web framework for the API and dashboard
2. **OpenAI API**: For language understanding and ad generation
3. **Vector Database**: Likely Pinecone based on configuration
4. **PostgreSQL**: For structured data storage
5. **Redis**: Likely used for caching

## Data Flow

The typical data flow through the system is likely:

1. User query is received via API
2. Query is analyzed for context and intent
3. Relevant ads are retrieved from the vector database
4. Ads are ranked based on relevance and other factors
5. Selected ad is formatted for the appropriate context
6. Ad is delivered back to the user
7. Impression is tracked for analytics

## Development Environment

The server is running in development mode with automatic reloading, suggesting an active development environment. The system appears to be well-structured with clear separation of concerns, comprehensive testing, and a focus on maintainability.

## Next Steps for Exploration

To better understand the system:

1. Use the `explore_endpoints.py` script to discover available API endpoints
2. Examine the API responses to understand data structures
3. Check the configuration files to understand system settings
4. Review the test cases to understand expected behaviors

---

This document provides a high-level overview of the AdServ architecture based on observed file structure and server behavior. For more detailed information, consult the specific module documentation or codebase. 