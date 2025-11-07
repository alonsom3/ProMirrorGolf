from setuptools import setup, find_packages

setup(
    name="promirror",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "opencv-python>=4.8.0",
        "mediapipe>=0.10.0",
    ],
    entry_points={
        'console_scripts': [
            'promirror=promirror.main:main',
        ],
    },
)
