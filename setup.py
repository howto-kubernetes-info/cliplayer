import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cliplayer",
    version="0.1.0",
    author="Stephan Gitz",
    author_email="stephan@howto-kubernetes.info",
    description="The cliplayer helps to script shell based lectures and screencast tutorials",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/howto-kubernetes-info/cliplayer",
    packages=setuptools.find_packages(),
    scripts=['bin/cliplayer'],
    install_requires=[
        'pynput',
        'pyyaml',
        'pexpect'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
    python_requires='>=3.6',
)