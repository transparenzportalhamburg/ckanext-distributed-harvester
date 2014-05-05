import logging
import datetime
import json

import pika

from ckan.lib.base import config
from ckan.plugins import PluginImplementations
from ckan import model

from ckanext.harvest.model import HarvestJob, HarvestObject,HarvestGatherError
from ckanext.harvest.interfaces import IHarvester

log = logging.getLogger(__name__)
assert not log.disabled

__all__ = ['get_distributed_gather_publisher', 'get_distributed_gather_consumer', \
           'get_distributed_fetch_publisher', 'get_distributed_fetch_consumer']


PORT = 5672
USERID = 'guest'
PASSWORD = 'guest'
HOSTNAME = 'localhost'
VIRTUAL_HOST = '/'
MQ_TYPE = 'amqp'

EXCHANGE_TYPE = 'direct'


def get_connection():
    '''
    Initiate connection with the RabbitMQ server.
    '''
    backend = config.get('ckan.harvest.mq.type', MQ_TYPE)
    if backend in ('amqp', 'ampq'):  # "ampq" is for compat with old typo    
        try:
            port = int(config.get('ckan.harvest.mq.port', PORT))
        except ValueError:
            port = PORT
        
        # RabbitMQ server username
        userid = config.get('ckan.harvest.mq.user_id', USERID)
        # RabbitMQ server user's password
        password = config.get('ckan.harvest.mq.password', PASSWORD)
        # RabbitMQ server host 
        hostname = config.get('ckan.harvest.mq.hostname', HOSTNAME)
        # RabbitMQ server virtualhost 
        virtual_host = config.get('ckan.harvest.mq.virtual_host', VIRTUAL_HOST)
    
        credentials = pika.PlainCredentials(userid, password)
        parameters = pika.ConnectionParameters(host=hostname,
                                               port=port,
                                               virtual_host=virtual_host,
                                               credentials=credentials,
                                               frame_max=10000)
        log.debug("pika connection using %s" % parameters.__dict__)
    
        return pika.BlockingConnection(parameters)
    raise Exception('not a valid queue type %s' % backend)



def purge_distributed_queues(gather_queue_name, fetch_queue_name):
    '''
    Purges given persistent queues.
    
    @param gather_queue_name    name of the gather queue
    @param fetch_queue_name     name of the fetch queue
    '''
    backend = config.get('ckan.harvest.mq.type', MQ_TYPE)
    connection = get_connection()
    if backend in ('amqp', 'ampq'):
        channel = connection.channel()
        channel.queue_purge(queue=gather_queue_name)
        channel.queue_purge(queue=fetch_queue_name)
        return
    raise Exception('not a valid queue type %s' % backend)

    
class Publisher(object):
    '''
    Constructor. Initiate connection with the RabbitMQ server.

    @param exchange    name of the exchange to send messages to
    @param connection  connection to the RabbitMQ server 
    @param channel     connection to the RabbitMQ server
    @param routing_key message routing key
    '''
    def __init__(self, connection, channel, exchange, routing_key):
        self.connection = connection
        self.channel = channel
        self.exchange = exchange
        self.routing_key = routing_key

    def send(self, body, **kw):
        '''
        Publish message to exchange using routing key
    
        @param body        message to publish
        '''
        return self.channel.basic_publish(self.exchange,
                                          self.routing_key,
                                          json.dumps(body),
                                          properties=pika.BasicProperties(
                                             delivery_mode = 2, # make message persistent
                                          ),
                                          **kw)
    def close(self):
        '''
        Close connection.
        '''
        self.connection.close()



def get_publisher(exchange_name, routing_key):
    '''
    Returns a publisher object.
    
    @param exchange    name of the exchange to send messages to
    @param routing_key message routing key    
    '''
    connection = get_connection()
    backend = config.get('ckan.harvest.mq.type', MQ_TYPE)
    if backend in ('amqp', 'ampq'):
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange_name, durable=True)
        return Publisher(connection,
                         channel,
                         exchange_name,
                         routing_key=routing_key)
    raise Exception('not a valid queue type %s' % backend)


class FakeMethod(object):
    ''' This is to act like the method returned by AMQP'''
    def __init__(self, message):
        self.delivery_tag = message

def get_consumer(exchange_name, queue_name, routing_key):
    '''
    Returns a reference to a RabbitMQ server channel.
    
    @param exchange    name of the exchange to send messages to
    @param queue_key   name of the queue to receive messages from    
    @param routing_key message routing key
    '''
    connection = get_connection()
    backend = config.get('ckan.harvest.mq.type', MQ_TYPE)

    if backend in ('amqp', 'ampq'):
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange_name, durable=True)
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(queue=queue_name, exchange=exchange_name, routing_key=routing_key)
        return channel
    raise Exception('not a valid queue type %s' % backend)



def distributed_gather_callback(channel, method, header, body):
    '''Executes gather stage of each harvester.'''
    try:
        id = json.loads(body)['harvest_job_id']
        exchange_name = json.loads(body)['exchange_name']
        fetch_routing_key = json.loads(body)['fetch_routing_key']
        log.debug('Received harvest job id: %s' % id)
    except KeyError:
        log.error('No harvest job id received')
        channel.basic_ack(method.delivery_tag)
        return False

    # Get a publisher for the fetch queue
    publisher = get_distributed_fetch_publisher(exchange_name, fetch_routing_key)

    job = HarvestJob.get(id)

    if not job:
        log.error('Harvest job does not exist: %s' % id)
        channel.basic_ack(method.delivery_tag)
        return False

    # Send the harvest job to the plugins that implement
    # the Harvester interface, only if the source type
    # matches
    harvester_found = False
    for harvester in PluginImplementations(IHarvester):
        if harvester.info()['name'] == job.source.type:
            harvester_found = True
            # Get a list of harvest object ids from the plugin
            job.gather_started = datetime.datetime.utcnow()

            try:
                harvest_object_ids = harvester.gather_stage(job)
            except (Exception, KeyboardInterrupt):
                channel.basic_ack(method.delivery_tag)
                harvest_objects = model.Session.query(HarvestObject).filter_by(
                    harvest_job_id=job.id
                )
                for harvest_object in harvest_objects:
                    model.Session.delete(harvest_object)
                model.Session.commit()
                raise
            finally:
                job.gather_finished = datetime.datetime.utcnow()
                job.save()

            if not isinstance(harvest_object_ids, list):
                log.error('Gather stage failed')
                publisher.close()
                channel.basic_ack(method.delivery_tag)
                return False

            if len(harvest_object_ids) == 0:
                log.info('No harvest objects to fetch')
                publisher.close()
                channel.basic_ack(method.delivery_tag)
                return False

            log.debug('Received from plugin gather_stage: {0} objects (first: {1} last: {2})'.format(
                        len(harvest_object_ids), harvest_object_ids[:1], harvest_object_ids[-1:]))
            for id in harvest_object_ids:
                # Send the id to the fetch queue
                publisher.send({'harvest_object_id':id})
            log.debug('Sent {0} objects to the fetch queue'.format(len(harvest_object_ids)))

    if not harvester_found:
        msg = 'No harvester could be found for source type %s' % job.source.type
        err = HarvestGatherError(message=msg,job=job)
        err.save()
        log.error(msg)

    model.Session.remove()
    publisher.close()
    channel.basic_ack(method.delivery_tag)


def distributed_fetch_callback(channel, method, header, body):
    '''Executes fetch stage of each harvester.'''
    try:
        id = json.loads(body)['harvest_object_id']
        log.info('Received harvest object id: %s' % id)
    except KeyError:
        log.error('No harvest object id received')
        channel.basic_ack(method.delivery_tag)
        return False


    obj = HarvestObject.get(id)
    if not obj:
        log.error('Harvest object does not exist: %s' % id)
        channel.basic_ack(method.delivery_tag)
        return False

    obj.retry_times += 1
    obj.save()

    if obj.retry_times >= 5:
        obj.state = "ERROR"
        obj.save()
        log.error('Too many consecutive retries for object {0}'.format(obj.id))
        channel.basic_ack(method.delivery_tag)
        return False

    # Send the harvest object to the plugins that implement
    # the Harvester interface, only if the source type
    # matches
    for harvester in PluginImplementations(IHarvester):
        if harvester.info()['name'] == obj.source.type:
            fetch_and_import_stages(harvester, obj)

    model.Session.remove()
    channel.basic_ack(method.delivery_tag)

def fetch_and_import_stages(harvester, obj):
    obj.fetch_started = datetime.datetime.utcnow()
    obj.state = "FETCH"
    obj.save()
    success_fetch = harvester.fetch_stage(obj)
    obj.fetch_finished = datetime.datetime.utcnow()
    obj.save()
    if success_fetch:
        # If no errors where found, call the import method
        obj.import_started = datetime.datetime.utcnow()
        obj.state = "IMPORT"
        obj.save()
        success_import = harvester.import_stage(obj)
        obj.import_finished = datetime.datetime.utcnow()
        if success_import:
            obj.state = "COMPLETE"
        else:
            obj.state = "ERROR"
        obj.save()
    else:
        obj.state = "ERROR"
        obj.save()
    if obj.report_status:
        return
    if obj.state == 'ERROR':
        obj.report_status = 'errored'
    elif obj.current == False:
        obj.report_status = 'deleted'
    elif len(model.Session.query(HarvestObject)
           .filter_by(package_id = obj.package_id)
           .limit(2)
           .all()) == 2:
        obj.report_status = 'updated'
    else:
        obj.report_status = 'added'
    obj.save()

def get_distributed_gather_consumer(exchange_name, queue_name, routing_key):
    '''
    Initiate connection with the RabbitMQ server for the the gather consumer.
    
    @param exchange    name of the exchange to send messages to
    @param queue_key   name of the queue to receive messages from    
    @param routing_key message routing key
    '''
    consumer = get_consumer(exchange_name, queue_name, routing_key)
    log.debug('Gather queue consumer registered')
    return consumer


def get_distributed_fetch_consumer(exchange_name, queue_name, routing_key):
    '''
    Initiate connection with the RabbitMQ server for the the fetch consumer.
    
    @param exchange    name of the exchange to send messages to
    @param queue_key   name of the queue to receive messages from    
    @param routing_key message routing key
    '''
    consumer = get_consumer(exchange_name, queue_name,routing_key)
    log.debug('Fetch queue consumer registered')
    return consumer


def get_distributed_gather_publisher(exchange_name, routing_key):
    '''
    Initiate connection with the RabbitMQ server for the the gather publisher.
    
    @param exchange    name of the exchange to send messages to
    @param routing_key message routing key
    '''
    return get_publisher(exchange_name, routing_key)

def get_distributed_fetch_publisher(exchange_name, routing_key):
    '''
    Initiate connection with the RabbitMQ server for the the fetch publisher.
    
    @param exchange    name of the exchange to send messages to
    @param routing_key message routing key
    '''
    return get_publisher(exchange_name, routing_key)

