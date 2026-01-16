from setuptools import setup, find_packages

setup(
    name="crytonix",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "crytonix=crytonix.main:main",
        ],
    },
)
