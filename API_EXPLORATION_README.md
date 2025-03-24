# AdServ API Exploration Tools

This directory contains tools to help explore, test, and visualize the AdServ API structure and endpoints.

## Available Tools

### 1. API Endpoint Explorer (`explore_endpoints.py`)

A tool to discover and test API endpoints of the running ad service. It makes requests to common API endpoint patterns and reports the results.

**Usage:**
```bash
python explore_endpoints.py http://localhost:5000  # Replace with your server URL
```

**Features:**
- Tests common REST API endpoints with GET requests
- Tests potential POST endpoints with sample query data
- Displays response status, content type, and response data
- Color-coded output based on HTTP status codes

### 2. API Visualizer (`visualize_api.py`)

Generates visual representations of the API structure discovered by the endpoint explorer.

**Usage:**
```bash
python visualize_api.py http://localhost:5000  # Replace with your server URL
```

**Outputs:**
- `adserv_api_structure.png` - Network diagram showing the API endpoint tree structure
- `adserv_api_status_codes.png` - Bar chart showing the HTTP status codes distribution
- `adserv_api_structure.dot` - GraphViz DOT file for enhanced visualization (if Graphviz is not installed)

**Enhanced Visualization:**
For better visualizations, install Graphviz from https://graphviz.org/download/

Once installed, the script will automatically generate an enhanced visualization:
- `adserv_api_structure_dot.png` - Higher quality visualization with better node layouts

### 3. Setup Tools (`setup_exploration_tools.py`)

Installs the required dependencies for exploration tools.

**Usage:**
```bash
python setup_exploration_tools.py
```

**Dependencies installed:**
- requests
- rich
- prettytable
- matplotlib
- networkx
- graphviz (Python package)

### 4. API Endpoint Tester (`test_api_endpoint.py`)

A command-line tool to test specific AdServ API endpoints with custom data. This tool allows you to send various HTTP requests and view detailed responses.

**Usage:**
```bash
python test_api_endpoint.py <url> [-m METHOD] [-d DATA] [-H HEADER] [-t TIMEOUT]
```

**Examples:**
```bash
# GET request to health endpoint
python test_api_endpoint.py http://localhost:5000/api/health

# POST request with inline JSON data
python test_api_endpoint.py http://localhost:5000/api/ads/match -m POST -d '{"query": "gaming laptop"}'

# POST request with JSON file
python test_api_endpoint.py http://localhost:5000/api/ads/match -m POST -d sample_query.json

# Request with custom headers
python test_api_endpoint.py http://localhost:5000/api -H "Authorization: Bearer token123"
```

**Features:**
- Supports all HTTP methods (GET, POST, PUT, DELETE)
- Can accept JSON data from command line or from a file
- Displays detailed response information including headers and timing
- Formats JSON responses with syntax highlighting
- Custom timeout and header support

## API Structure

Based on exploratory testing, the AdServ API has the following structure:

- Root endpoint (`/`) - Returns basic service information
- Health check (`/api/health`) - Service health status
- Ad matching (`/api/ads/match`) - Main endpoint for ad matching functionality
  - Accepts POST requests with JSON data
  - Requires a query parameter for ad matching

## Understanding HTTP Status Codes

- **2xx (Success)** - The request was successfully received, understood, and accepted
  - 200 OK - Standard success response
- **3xx (Redirection)** - Further action needs to be taken to complete the request
  - 302 Found - Temporary redirection
- **4xx (Client Error)** - The request contains bad syntax or cannot be fulfilled
  - 404 Not Found - The requested resource does not exist
  - 405 Method Not Allowed - The HTTP method is not supported for this endpoint

## Next Steps

After exploring the API structure, you can:

1. Test specific endpoints with custom data using cURL or similar tools
2. Integrate API calls into your application
3. Develop automated tests for critical API functions
4. Create API documentation based on your findings 