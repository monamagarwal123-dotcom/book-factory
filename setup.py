from setuptools import setup, find_packages

setup(
    name="book-factory",
    version="0.1.0",
    description="AI Children's Book Factory - Generate KDP-ready books with Gemini/Grok",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyyaml",
        "Pillow",
        "requests",
        "python-dotenv",
        "google-generativeai",
        "google-genai",
        "openai",
        "anthropic",
        "reportlab",
    ],
    entry_points={
        "console_scripts": [
            "book-factory=cli:main",
        ],
    },
    python_requires=">=3.9",
)
