from setuptools import setup

import amari.__init__ as init

readme = ""
with open("README.rst") as file:
    readme = file.read()

setup(
    name="amari",
    version=init.__version__,
    url="https://github.com/TheF1ng3r/amari.py",
    project_urls={"Documentation": "https://amaripy.readthedocs.io/en/latest/"},
    description="An asynchronous API wrapper for the Amari API.",
    long_description=readme,
    author="TheF1ng3r",
    license="MIT",
    install_requires="aiohttp>=3.6.0,<3.8.0",
    python_requires=">=3.8.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["amari"],
)
