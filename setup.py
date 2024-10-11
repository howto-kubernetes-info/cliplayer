from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cliplayer",
    version="0.1.4",
    author="Stephan Gitz",
    author_email="pypi@systremix.de",
    description="The cliplayer helps to script shell based lectures and screencast tutorials",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/howto-kubernetes-info/cliplayer",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'cliplayer': ['config/*.cfg'],
    },
    entry_points={
        'console_scripts': [
            'cliplayer=cliplayer.cliplayer:main',
        ],
    },
    install_requires=[
        'pexpect>=4.9.0'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
    python_requires='>=3.7',
)
