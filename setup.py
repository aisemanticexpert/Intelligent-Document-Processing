"""
Financial IDR Pipeline - Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="financial-idr",
    version="1.0.0",
    author="Rajesh Kumar Gupta",
    author_email="contact@semanticdataservices.com",
    description="Intelligent Document Recognition for Financial Documents with Knowledge Graph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aisemanticexpert/Intelligent-Document-Processing-",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.0",
        "rdflib>=6.2.0",
    ],
    extras_require={
        "nlp": ["spacy>=3.5.0"],
        "neo4j": ["neo4j>=5.0.0"],
        "llm": ["openai>=1.0.0", "anthropic>=0.8.0"],
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0", "black>=23.0.0", "flake8>=6.0.0"],
        "all": [
            "spacy>=3.5.0",
            "neo4j>=5.0.0",
            "openai>=1.0.0",
            "anthropic>=0.8.0",
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "financial-idr=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["ontology/*.ttl", "config/*.yaml"],
    },
)
