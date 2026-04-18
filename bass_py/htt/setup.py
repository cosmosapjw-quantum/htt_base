from setuptools import setup, find_packages
setup(
    name="htt",
    version="8.3.0",
    packages=find_packages(),
    install_requires=["numpy>=1.24", "scipy>=1.10"],
)
