from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="autothumb",
    version="0.1.0",
    author="AutoThumb Team",
    description="Générateur automatique de thumbnails YouTube avec IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/autothumb",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1.7",
        "rich>=13.7.0",
        "anthropic>=0.39.0",
        "Pillow>=10.4.0",
        "ffmpeg-python>=0.2.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.10.0",
    ],
    entry_points={
        "console_scripts": [
            "autothumb=autothumb.cli.main:cli",
        ],
    },
)
