"""
Setup script for TwitRec
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='twitrec',
    version='1.0.0',
    author='TwitRec Team',
    description='Мощный и красивый CLI инструмент для автоматической записи Twitch стримов',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/TwitRec',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Video :: Capture',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
    install_requires=[
        'requests>=2.31.0',
        'rich>=13.7.0',
        'streamlink>=6.5.0',
        'python-dotenv>=1.0.0',
        'click>=8.1.7',
        'twitchAPI>=4.1.0',
    ],
    entry_points={
        'console_scripts': [
            'twitrec=main:main',
        ],
    },
    include_package_data=True,
)
