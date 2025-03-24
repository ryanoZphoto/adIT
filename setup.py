from setuptools import setup, find_packages

setup(
    name="ad_service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core dependencies
        "flask>=2.0.1",
        "flask-restful>=0.3.9",
        "openai>=1.3.0",
        "pinecone-client>=2.2.1",
        
        # Data processing
        "numpy>=1.23.5",
        "pandas>=1.5.3",
        
        # Monitoring and metrics
        "prometheus-client>=0.16.0",
        
        # UI and visualization
        "streamlit>=1.24.0",
        "plotly>=4.14.0",
        
        # Documentation
        "mkdocs>=1.6.0",
        "mkdocs-material>=9.6.5",
        
        # Utilities
        "python-dateutil>=2.8.2",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
        "rich>=12.6.0",
        "redis>=5.0.0",
        "requests>=2.31.0",
        "urllib3>=2.0.7"
    ],
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=6.0.0',
            'black>=23.0.0',
            'isort>=5.0.0',
            'flake8>=7.0.0',
            'mypy>=1.0.0'
        ]
    }
) 
