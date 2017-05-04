from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='myrm',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts':
            ['myrm = myrm:main',
             'mrm = myrm:shor_rm']
        }
    )
