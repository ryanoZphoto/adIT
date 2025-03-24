# Company Ad Directory Structure

This directory contains company-specific ad configurations and campaigns. Each company has its own directory with the following structure:

```
companies/
├── company_name/
│   ├── config/
│   │   └── company_config.json    # Company-specific settings and defaults
│   └── ads/
│       ├── campaign_1.json        # Campaign configurations
│       ├── campaign_2.json
│       └── ...
└── ...
```

## Directory Structure Explanation

### Company Directory
Each company has its own directory named after their company ID (e.g., `nike`, `adidas`, etc.)

### Config Directory
Contains company-specific configurations:
- `company_config.json`: Company details, default settings, and API access information

### Ads Directory
Contains campaign configurations:
- Each `.json` file represents a campaign
- Campaigns can contain multiple ads
- All campaign-specific settings and performance metrics are stored here

## File Formats

### company_config.json
- Company identification and contact information
- Default bid and budget settings
- API access credentials
- Notification preferences

### campaign_*.json
- Campaign details and settings
- Targeting configuration
- Individual ad configurations
- Performance metrics and settings
- Reporting preferences

## Usage

1. Create a new company directory using the company's unique identifier
2. Copy and modify the template files from `template_company/`
3. Update the configuration files with company-specific information
4. Add campaign files as needed

## Best Practices

1. Use clear, consistent naming for campaign files
2. Keep sensitive information (API keys, etc.) in secure storage
3. Regularly backup campaign configurations
4. Monitor the performance_metrics section for each campaign

## Integration

The ad delivery system will automatically load and use these configurations. Updates to campaign files will be reflected in real-time in the ad serving system. 