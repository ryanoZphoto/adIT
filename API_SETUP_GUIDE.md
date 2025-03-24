# API Setup Guide for Ad Service

This guide will help you set up the necessary API keys for the Ad Service.

## OpenAI API Setup

1. **Create an OpenAI account**:
   - Go to [OpenAI's website](https://openai.com/)
   - Sign up for an account if you don't have one

2. **Get your API key**:
   - Log in to your OpenAI account
   - Navigate to the [API keys page](https://platform.openai.com/api-keys)
   - Click "Create new secret key"
   - Give your key a name (e.g., "Ad Service")
   - Copy the key (it should start with `sk-proj-`)

3. **Update your .env file**:
   - Open the `.env` file in the project root
   - Replace the placeholder with your actual API key
   - Example: `OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456`

4. **Note on API key formats**:
   - OpenAI now uses project-specific API keys that start with `sk-proj-`
   - If you have an older key that starts with just `sk-`, you may need to generate a new key

## Pinecone API Setup

1. **Create a Pinecone account**:
   - Go to [Pinecone's website](https://www.pinecone.io/)
   - Sign up for an account if you don't have one

2. **Create a project**:
   - Log in to your Pinecone account
   - Create a new project or use an existing one
   - Note the environment (e.g., `us-east1-gcp`)

3. **Get your API key**:
   - In your Pinecone dashboard, find your API key
   - Copy the key

4. **Create an index**:
   - In your Pinecone dashboard, create a new index
   - Name it `adservice` (or choose another name and update the `.env` file)
   - Set the dimension to 1536 (to match OpenAI's text-embedding-3-large model)
   - Choose the metric as `cosine`
   - Select an appropriate pod type based on your needs

5. **Update your .env file**:
   - Open the `.env` file in the project root
   - Replace the placeholder with your actual API key
   - Update the `PINECONE_ENVIRONMENT` if different from the default
   - Update the `PINECONE_INDEX_NAME` if you chose a different name

## Testing Your API Connections

After setting up your API keys, you can test the connections:

```bash
python test_api_connections.py
```

This script will:
1. Test the connection to OpenAI's API
2. Test the connection to Pinecone's API
3. Provide detailed error messages if any issues are found

## Troubleshooting

### OpenAI API Issues

- **401 Unauthorized Error**: Your API key is invalid or expired. Generate a new key.
- **Rate Limit Exceeded**: You've hit your usage limits. Wait or upgrade your plan.
- **Invalid Model**: The model specified doesn't exist or you don't have access to it.
- **Invalid API Key Format**: Ensure your key starts with `sk-proj-` as OpenAI now uses project-specific keys.

### Pinecone API Issues

- **Authentication Error**: Your API key is incorrect.
- **Environment Error**: The environment specified doesn't match your project.
- **Index Not Found**: The index doesn't exist yet. Create it in the Pinecone dashboard.

## Security Best Practices

- Never commit your `.env` file to version control
- Rotate your API keys periodically
- Use environment-specific API keys (development, staging, production)
- Set up proper access controls and usage limits in your OpenAI and Pinecone accounts 