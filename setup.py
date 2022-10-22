#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of everylotbot

from setuptools import setup

with open('everylot/__init__.py') as i:
    version = next(r for r in i.readlines() if '__version__' in r).split('=')[1].strip('"\' \n')

setup(
    name='everylotmasto',
    version=version,
    description='everylotmasto',
    long_description='''every lot mastodon edition''',
    keywords='',
    author='fitnr',
    author_email='fitnr@fakeisthenewreal',
    packages=['everylot'],
    license='GPL-3.0',
    include_package_data=False,
    install_requires=[
        'requests',
        'Mastodon.py',
        'pyyaml'
        #'twitter_bot_utils>=0.11.5,<=0.12',
    ],
    entry_points={
        'console_scripts': [
            'mastolot=everylot.masto:main',
        ],
    },
)
