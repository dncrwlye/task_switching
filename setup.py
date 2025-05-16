from setuptools import setup, find_packages

setup(
    name="task_switch",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "pystray",
        "pillow"        # Add more dependencies
    ],
)


