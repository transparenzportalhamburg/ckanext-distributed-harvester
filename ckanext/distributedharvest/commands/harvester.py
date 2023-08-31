import click
import logging

from ckan import model
from ckan.logic import get_action
from ckanext.distributedharvest.queue import get_distributed_gather_consumer, distributed_gather_callback, get_distributed_fetch_consumer
from ckanext.harvest.queue import fetch_callback as distributed_fetch_callback
from ckanext.harvest.queue import get_connection_amqp as get_connection
from ckanext.distributedharvest.queue import purge_distributed_queues
from ckanext.harvest.model import HarvestSource, HarvestJob


EXCHANGE_NAME = 'ckan.distributed.harvester'
GATHER_STAGE = "GATHER"
FETCH_STAGE = "FETCH"


def harvest_source_from_title(title):
    all = model.Session.query(HarvestSource).filter(
        HarvestSource.title.ilike(title)).all()
    if not all:
        raise Exception('Harvest source with title %s does not exist' % title)
    if len(all) > 1:
        raise Exception('Found multiple harvest sources with title %s' % title)
    return all[0]


def set_all_harvest_jobs_to_finished(source_id):
    hos = model.Session.query(HarvestJob).filter(
        HarvestJob.source_id == source_id).filter(HarvestJob.status != 'Finished').all()
    for h in hos:
        h.status = 'Finished'
        h.save()


def create_job(source, user):
    context = {
        "model": model,
        "session": model.Session,
        "user": user['name']
    }
    get_action("harvest_job_create")(context, {
        "source_id": source.id,
        "run": False
    })


@click.group(short_help=u"Perform distributed harvester related operations.")
def distributed_harvester():
    pass


def get_gather_queue_name(harvester_title):
    return f'{harvester_title}_gather_queue'


def get_fetch_queue_name(harvester_title):
    return f'{harvester_title}_fetch_queue'


def get_gather_routing_key(harvester_title):
    return f'{harvester_title}_gather_routing_key'


def get_fetch_routing_key(harvester_title):
    return f'{harvester_title}_fetch_routing_key'


@distributed_harvester.command()
@click.argument('harvester_title', required=True)
def start_distributed_gather_consumer(harvester_title):
    ''' Starts gather consumer.'''

    queue_name = get_gather_queue_name(harvester_title)
    routing_key = get_gather_routing_key(harvester_title)
    exchange_name = EXCHANGE_NAME

    logging.getLogger('amqplib').setLevel(logging.INFO)
    
    consumer = get_distributed_gather_consumer(exchange_name, queue_name, routing_key)
    consumer.basic_consume(on_message_callback=distributed_gather_callback, queue=queue_name)
    consumer.start_consuming()


@distributed_harvester.command()
@click.argument('harvester_title', required=True)
def start_distributed_fetch_consumer(harvester_title):
    ''' Starts fetch consumer.'''

    queue_name = get_fetch_queue_name(harvester_title)
    routing_key = get_fetch_routing_key(harvester_title)
    exchange_name = EXCHANGE_NAME

    logging.getLogger('amqplib').setLevel(logging.INFO)
    
    consumer = get_distributed_fetch_consumer(exchange_name, queue_name, routing_key)
    consumer.basic_consume(on_message_callback=distributed_fetch_callback, queue=queue_name)    
    consumer.start_consuming()
    

@distributed_harvester.command()
@click.argument('harvester_title', required=True)
@click.option('--prepare-jobs', default=True)
def run_harvester(harvester_title, prepare_jobs):
    ''' Starts harvest job.'''

    source = harvest_source_from_title(harvester_title)

    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    admin_user = get_action('get_site_user')(context, {})

    if prepare_jobs:
        set_all_harvest_jobs_to_finished(source.id)
        model.Session.commit()
        create_job(source, admin_user)

    gather_routing_key = get_gather_routing_key(harvester_title)
    fetch_routing_key = get_fetch_routing_key(harvester_title)
    exchange_name = EXCHANGE_NAME

    context = {'model': model,
               'user': admin_user['name'], 
               'session': model.Session}
    
    get_action('distributed_harvest_jobs_run')(context, {'gather_routing_key': gather_routing_key,
                                                         'source_id': source.id, 
                                                         'exchange_name': exchange_name, 
                                                         'fetch_routing_key': fetch_routing_key})


@distributed_harvester.command()
@click.argument('harvester_title', required=True)
def purge_queues(harvester_title):
    ''' Purges given queues.'''

    gather_queue_name = get_gather_queue_name(harvester_title)
    fetch_queue_name = get_fetch_queue_name(harvester_title)

    purge_distributed_queues(gather_queue_name, fetch_queue_name)
