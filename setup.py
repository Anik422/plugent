"""Setup script for plugent."""

from setuptools import setup, find_packages

setup(
    name="plugent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "sqlalchemy>=2.0.0",
        "chromadb>=0.4.0",
        "litellm>=1.0.0",
        "python-dotenv>=1.0.0",
        "typer>=0.9.0",
    ],
    extras_require={
        "ollama": ["ollama>=0.1.0"],
        "gguf": ["ctransformers>=0.2.0"],
        "mongo": ["pymongo>=4.6.0"],
        "all": ["ollama>=0.1.0", "ctransformers>=0.2.0", "pymongo>=4.6.0"],
    },
    python_requires=">=3.10",
)