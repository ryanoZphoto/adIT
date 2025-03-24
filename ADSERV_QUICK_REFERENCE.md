# AdServ Quick Reference Guide

## Running the Application

**Start the Flask server:**
```
python ad_service/main.py
```

**Access the web interface:**
```
http://localhost:5000/ or http://your-ip:5000/
```

**Health check:**
```
curl http://localhost:5000/api/health
```

## Exploration Tools

**Explore API endpoints:**
```
python explore_endpoints.py http://localhost:5000
```

**Generate architecture diagrams:**
```
python generate_architecture_diagram.py
```

**Install dependencies for exploration tools:**
```
python setup_exploration_tools.py
```

## Testing

**Run all tests:**
```
python ad_service/tests/run_tests.py
```

**Generate test report:**
```
python ad_service/tests/generate_test_report.py
```

## API Usage

**Match an ad to a query:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "query": "I need a new laptop for gaming",
  "user_id": "user123",
  "session_id": "session456"
}' http://localhost:5000/api/ads/match
```

**Expected response format:**
```json
{
  "ad_id": "ad_12345",
  "content": "Experience ultimate gaming with our new XYZ Gaming Laptop...",
  "relevance_score": 0.89,
  "metadata": {
    "advertiser": "XYZ Computers",
    "campaign_id": "campaign_789",
    "category": "electronics"
  }
}
```

## Configuration

The application configuration is managed through:

1. **Environment variables** - Set in `.env` file
2. **Configuration files** - Located in `ad_service/config/`

Key configurations:

- OpenAI API settings
- Pinecone vector database settings
- Database connections
- Redis cache settings
- Feature flags

## Folder Structure

```
ad_service/
├── ad_matching/     # Ad matching logic
├── ad_delivery/     # Ad delivery pipeline
├── analytics/       # Analytics and reporting
├── api/             # API endpoints
├── config/          # Configuration
├── gui/             # Web interface
│   ├── components/  # UI components
│   └── pages/       # Page definitions
├── services/        # Core services
└── tests/           # Testing suite
```

## Common Operations

### Adding a New Ad

To add a new ad to the system:

1. Prepare ad metadata and content
2. Generate embedding using OpenAI API
3. Store in vector database (Pinecone)
4. Register in the ad repository

### Monitoring Performance

Access analytics dashboard:
```
http://localhost:5000/analytics
```

Key metrics to monitor:
- Click-through rates
- Relevance scores
- Response times
- Conversion rates

### Debugging

Use the debug panel in the web interface:
```
http://localhost:5000/debug
```

Debug logs location:
```
logs/adserv.log
```

## Error Handling

Common error codes:

- `400` - Bad request (check payload format)
- `401` - Unauthorized (check API keys)
- `404` - Resource not found
- `500` - Server error (check logs)

## Best Practices

1. **Performance**:
   - Use cached embeddings where possible
   - Batch similar requests
   - Monitor response times

2. **Quality**:
   - Regularly test ad relevance
   - Review ad content quality
   - Check for prompt injections

3. **Monitoring**:
   - Set up alerts for service issues
   - Monitor API rate limits
   - Track performance metrics

## API Exploration and Visualization

### Exploring API Endpoints

To discover and test the available API endpoints:

```bash
python explore_endpoints.py http://localhost:5000  # Replace with your server URL
```

This will make requests to common API endpoints and report their status and response data.

### Visualizing API Structure

Generate visual representations of the API structure:

```bash
python visualize_api.py http://localhost:5000  # Replace with your server URL
```

This creates:
- `adserv_api_structure.png` - A network diagram showing the API structure
- `adserv_api_status_codes.png` - A bar chart of HTTP status code distribution

For enhanced visualizations, install Graphviz from https://graphviz.org/download/ 