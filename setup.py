from setuptools import setup, find_packages

setup(
    name="ad_service",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.32.0",
        "openai>=1.10.0",
        "plotly>=5.13.0",
        "pandas>=2.1.1",
        "numpy>=1.26.0",
        "matplotlib>=3.8.0",
        "seaborn>=0.13.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.4.2",
    ],
    python_requires=">=3.8",
) 
