from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-distributedharvest',
	version=version,
	description="distributed harvester",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Esra',
	author_email='esra.uenal@fokus.fraunhofer.de',
	url='',
	license='',
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
