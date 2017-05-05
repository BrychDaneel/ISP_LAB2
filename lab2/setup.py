from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='myrm',
    version='0.2',
    packages=find_packages(),
    entry_points={
        'console_scripts':
            ['myrm = myrm.__main__:main',
             'mrm = myrm.__main__:shor_rm']
        }
    )
