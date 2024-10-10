import setuptools
import os
from pathlib import Path

with open("README.md", "r") as fh:
    long_description = fh.read()

config_dir = Path("config")
config_files = [str(path) for path in config_dir.glob("*.cfg")]

setuptools.setup(
    name="cliplayer",
    version="0.1.3",
    author="Stephan Gitz",
    author_email="pypi@systremix.de",
    description="The cliplayer helps to script shell based lectures and screencast tutorials",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/howto-kubernetes-info/cliplayer",
    packages=setuptools.find_packages(),
    scripts=['bin/cliplayer'],
    install_requires=[
        'pexpect>=4.9.0'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
    python_requires='>=3.6',
    data_files=[('config/', config_files)],
)
