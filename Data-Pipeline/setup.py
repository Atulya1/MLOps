from setuptools import setup, find_packages

setup(
    name="data_pipeline",
    version="0.1.0",
    packages=find_packages(),      # <-- will pick up both scripts, data, logs, tests
    package_dir={"": "."},         # <-- root is Data-Pipeline/
)