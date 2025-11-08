from setuptools import setup, find_packages

setup(
    name="promirror",
    version="1.0.0",
    packages=find_packages(exclude=['tests', 'MLM2PRO-OGS-Connector']),
    install_requires=[
        "numpy>=1.26.0",
        "opencv-python-headless>=4.9.0",
        "mediapipe>=0.10.0",
        "aiohttp>=3.9.0",
        "aiofiles>=23.2.0",
        "websockets>=12.0",
        "yt-dlp>=2024.04.09",
    ],
    entry_points={
        'console_scripts': [
            'promirror=promirror.main:main',
        ],
    },
)
