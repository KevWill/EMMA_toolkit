from distutils.core import setup
from setuptools import find_packages

setup(name='emma_toolkit',
      version='1.0',
      description='EMMA toolkit',
      author='Kevin Willemsen',
      author_email='willemsen@emma.nl',
      install_requires=['requests>=2', 'requests_oauthlib'],
      classifiers=['Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',],
      url = 'https://github.com/KevWill/EMMA_toolkit',
      download_url = 'https://github.com/KevWill/EMMA_toolkit',
      packages = find_packages(),
      keywords = ['EMMA_toolkit'],
     )