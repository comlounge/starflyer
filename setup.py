from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='starflyer',
      version=version,
      description="Starflyer web framework",
      long_description="""super\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='COM.lounge',
      author_email='info@comlounge.net',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "wsgiutils",
        "logbook",
        "werkzeug",
        "routes",
        "jinja2",
      ],
      entry_points="""
      """,
      )
