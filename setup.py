from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-distributed-harvest',
	version=version,
	description="A ckan extension to execute distributed Harvest jobs",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Fachliche Leitstelle Transparenzportal, Hamburg, Germany; Esra Uenal FOKUS, Fraunhofer Berlin, Germany',
	author_email='transparenzportal@kb.hamburg.de',
	url='http://transparenz.hamburg.de/',
	license='AGPL',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.distributedharvest'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins] 
        distributed_harvest=ckanext.distributedharvest.plugin:DistributedHarvest
		
		[paste.paster_command]
		distributed-harvester = ckanext.distributedharvest.commands.harvester:DistributedHarvester

	""",
)
