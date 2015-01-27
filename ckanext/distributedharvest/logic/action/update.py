import hashlib

import logging
import datetime

from pylons import config
from paste.deploy.converters import asbool
from sqlalchemy import and_

from ckan.lib.search.index import PackageSearchIndex
from ckan.plugins import PluginImplementations
from ckan.logic import get_action
from ckanext.harvest.interfaces import IHarvester
from ckan.lib.search.common import SearchIndexError, make_connection


from ckan.model import Package
from ckan import logic

from ckan.logic import NotFound, check_access


from ckanext.distributedharvest.queue import get_distributed_gather_publisher

from ckanext.harvest.queue import resubmit_jobs

from ckanext.harvest.model import HarvestSource, HarvestJob, HarvestObject
from ckanext.harvest.logic import HarvestJobExists

from ckanext.harvest.logic.action.get import harvest_source_show, harvest_job_list, _get_sources_for_user
from ckanext.harvest.logic.action.update import _caluclate_next_run, _make_scheduled_jobs

log = logging.getLogger(__name__)



def distributed_harvest_jobs_run(context,data_dict):
    log.info('Harvest job run: %r', data_dict)

    check_access('distributed_harvest_jobs_run',context,data_dict)

    session = context['session']

    source_id = data_dict.get('source_id',None)
    routing_key = data_dict.get('gather_routing_key',None)
    exchange_name = data_dict.get('exchange_name',None)
    fetch_routing_key = data_dict.get('fetch_routing_key',None)
    

    if not source_id:
        _make_scheduled_jobs(context, data_dict)

    context['return_objects'] = False

    # Flag finished jobs as such
    jobs = harvest_job_list(context,{'source_id':source_id,'status':u'Running'})
    if len(jobs):
        package_index = PackageSearchIndex()
        for job in jobs:
            if job['gather_finished']:
                objects = session.query(HarvestObject.id) \
                          .filter(HarvestObject.harvest_job_id==job['id']) \
                          .filter(and_((HarvestObject.state!=u'COMPLETE'),
                                       (HarvestObject.state!=u'ERROR'))) \
                          .order_by(HarvestObject.import_finished.desc())

                if objects.count() == 0:
                    job_obj = HarvestJob.get(job['id'])
                    job_obj.status = u'Finished'

                    last_object = session.query(HarvestObject) \
                          .filter(HarvestObject.harvest_job_id==job['id']) \
                          .filter(HarvestObject.import_finished!=None) \
                          .order_by(HarvestObject.import_finished.desc()) \
                          .first()
                    if last_object:
                        job_obj.finished = last_object.import_finished
                    job_obj.save()
                    # Reindex the harvest source dataset so it has the latest
                    # status
                    if 'extras_as_string'in context:
                        del context['extras_as_string']
                    context.update({'validate': False, 'ignore_auth': True})
                    package_dict = logic.get_action('package_show')(context,
                            {'id': job_obj.source.id})

                    if package_dict:
                        package_index.index_package(package_dict)

    # resubmit old redis tasks
    resubmit_jobs()

    # Check if there are pending harvest jobs
    jobs = harvest_job_list(context,{'source_id':source_id,'status':u'New'})
    if len(jobs) == 0:
        log.info('No new harvest jobs.')
        raise Exception('There are no new harvesting jobs')

    # Send each job to the gather queue
    publisher = get_distributed_gather_publisher(exchange_name, routing_key)
    sent_jobs = []
    for job in jobs:
        context['detailed'] = False
        source = harvest_source_show(context,{'id':job['source_id']})
        if source['active']:
            job_obj = HarvestJob.get(job['id'])
            job_obj.status = job['status'] = u'Running'
            job_obj.save()
            publisher.send({'harvest_job_id': job['id'],
                            'exchange_name': exchange_name,
                            'fetch_routing_key': fetch_routing_key
                            })
            log.info('Sent job %s to the gather queue' % job['id'])
            sent_jobs.append(job)

    publisher.close()
    return sent_jobs
















