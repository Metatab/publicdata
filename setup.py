from setuptools import setup
import sys
import os

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='publicdata',
    version='0.0.2',
    url='https://github.com/CivicKnowledge/publicdata',
    license='MIT',
    author='Eric Busboom',
    author_email='eric@busboom.org',
    description='Url manipulation for extended application urls',
    packages=['publicdata'],
    zip_safe=True,
    install_requires=[
        'fs >= 2',
        'appurl',
        'rowgenerators',
        'pandas',
        'requests',
        'geoid'
        ],
    entry_points={
        'appurl.urls': [
            "censusreporter: = pandasreporter.censusreporter:CensusReporterURL"
        ],
        'rowgenerators': [
            "CRJSON+ = pandasreporter.censusreporter:CensusReporterSource"

        ]

    },
)