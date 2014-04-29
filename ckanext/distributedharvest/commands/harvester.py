import sys
from pprint import pprint

from ckan import model
from ckan.logic import get_action, ValidationError

from ckan.lib.cli import CkanCommand





class DistributedHarvester(CkanCommand):
    '''Harvests parallel remotely mastered metadata
   
    Usage:

      distributed-harvester run_distributed_harvester
        - runs distributed harvest jobs
        
      distributed-harvester run_distributed_harvester_with_param
        - runs distributed harvest jobs

      harvester distributed_gather_consumer_with_param
        - starts the consumer for the gathering queue
        
      harvester distributed_gather_consumer
        - starts the consumer for the gathering queue

      harvester distributed_fetch_consumer
        - starts the consumer for the fetching queue

      harvester distributed_fetch_consumer_with_param
        - starts the consumer for the fetching queue

      harvester purge_queues
        - removes all jobs from fetch and gather queue

      harvester purge_queues_with_param
        - removes all jobs from fetch and gather queue

      The commands should be run from the ckanext-distributedharvest directory and expect
      a development.ini file to be present. The option ckan.harvest.mq.type needs to be 
      declared with amqp. 
      Most of the time you will specify the config explicitly though::

        paster distributed-harvester sources --config=../ckan/development.ini

    '''
    
    EXCHANGE_NAME = 'ckan.distributed.harvester'
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 9
    min_args = 0

    def __init__(self,name):

        super(DistributedHarvester,self).__init__(name)

        self.parser.add_option('-j', '--no-join-datasets', dest='no_join_datasets',
            action='store_true', default=False, help='Do not join harvest objects to existing datasets')

        self.parser.add_option('--segments', dest='segments',
            default=False, help=
'''A string containing hex digits that represent which of
 the 16 harvest object segments to import. e.g. 15af will run segments 1,5,a,f''')

    def command(self):
        self._load_config()

        # We'll need a sysadmin user to perform most of the actions
        # We will use the sysadmin site user (named as the site_id)
        context = {'model':model,'session':model.Session,'ignore_auth':True}
        self.admin_user = get_action('get_site_user')(context,{})


        print ''

        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]
        if cmd == 'run_distributed_harvester':
            self.run_harvester()
        elif cmd == 'run_distributed_harvester_with_param':
            self.run_harvester_with_param() 
        elif cmd == 'distributed_gather_consumer':
            self.start_distributed_gather_consumer()
        elif cmd == 'distributed_fetch_consumer':
            self.start_distributed_fetch_consumer()  
        elif cmd == 'distributed_gather_consumer_with_param':
            self.start_distributed_gather_consumer_with_param()
        elif cmd == 'distributed_fetch_consumer_with_param':
            self.start_distributed_fetch_consumer_with_param()        
        elif cmd == 'purge_queues':
            self.purge_queues()
        elif cmd == 'purge_queues_with_param':
            self.purge_queues_with_param()          
        else:
            print 'Command %s not recognized' % cmd


    def _load_config(self):
        super(DistributedHarvester, self)._load_config()


    def start_distributed_gather_consumer(self):
        if len(self.args) >= 2:
            harvester_title = unicode(self.args[1])
        else:
            print 'Please provide the title of the harvester'
            sys.exit(1)
                      
        gather_queue_name = harvester_title  + '_gather_queue' 
        gather_routing_key = harvester_title + '_gather_routing_key' 
        exchange_name = self.EXCHANGE_NAME 
 
        import logging
        logging.getLogger('amqplib').setLevel(logging.INFO)
        from ckanext.distributedharvest.queue import get_distributed_gather_consumer, distributed_gather_callback
        consumer = get_distributed_gather_consumer(exchange_name, gather_queue_name, gather_routing_key)
        consumer.basic_consume(distributed_gather_callback, queue=gather_queue_name, no_ack=False)
        consumer.start_consuming()

        
    def start_distributed_gather_consumer_with_param(self):
        if len(self.args) >= 2:
            gather_queue_name = unicode(self.args[1])
        else:
            print 'Please provide a name for the gather_queue'
            sys.exit(1)
        if len(self.args) >= 3:
            gather_routing_key = unicode(self.args[2])
        else:
            print 'Please provide a routing key for the gather_queue'
            sys.exit(1)
        
        if len(self.args) >= 4:
            exchange_name = unicode(self.args[3])
        else:
            print 'Please provide the name of the exchange'
            sys.exit(1)
 
        import logging
        logging.getLogger('amqplib').setLevel(logging.INFO)
        from ckanext.distributedharvest.queue import get_distributed_gather_consumer, distributed_gather_callback
        consumer = get_distributed_gather_consumer(exchange_name, gather_queue_name, gather_routing_key)
        consumer.basic_consume(distributed_gather_callback, queue=gather_queue_name, no_ack=False)
        consumer.start_consuming()
 

    def start_distributed_fetch_consumer(self):
        
        if len(self.args) >= 2:
            harvester_title = unicode(self.args[1])
        else:
            print 'Please provide the title of the harvester'
            sys.exit(1)

        
        fetch_queue_name = harvester_title  + '_fetch_queue' 
        fetch_routing_key = harvester_title + '_fetch_routing_key' 
        exchange_name = self.EXCHANGE_NAME 

        import logging
        logging.getLogger('amqplib').setLevel(logging.INFO)
        from ckanext.distributedharvest.queue import get_distributed_fetch_consumer, distributed_fetch_callback
        consumer = get_distributed_fetch_consumer(exchange_name, fetch_queue_name, fetch_routing_key)
        consumer.basic_consume(distributed_fetch_callback, queue=fetch_queue_name, no_ack=False)
        consumer.start_consuming()
       
       
       
    def start_distributed_fetch_consumer_with_param(self):
        
        if len(self.args) >= 2:
            fetch_queue_name = unicode(self.args[1])
        else:
            print 'Please provide a name for the fetch_queue'
            sys.exit(1)
        if len(self.args) >= 3:
            fetch_routing_key = unicode(self.args[2])
        else:
            print 'Please provide a routing key for the fetch_queue'
            sys.exit(1)
        if len(self.args) >= 4:
            exchange_name = unicode(self.args[3])
        else:
            print 'Please provide the name of the exchange'
            sys.exit(1)

        import logging
        logging.getLogger('amqplib').setLevel(logging.INFO)
        from ckanext.distributedharvest.queue import get_distributed_fetch_consumer, distributed_fetch_callback
        consumer = get_distributed_fetch_consumer(exchange_name, fetch_queue_name, fetch_routing_key)
        consumer.basic_consume(distributed_fetch_callback, queue=fetch_queue_name, no_ack=False)
        consumer.start_consuming()       
 

    def run_harvester_with_param(self):
        if len(self.args) >= 2:
            source_id = unicode(self.args[1])
        else:
            print 'Please provide the source-id'
            sys.exit(1)
        if len(self.args) >= 3:
            gather_routing_key = unicode(self.args[2])
        else:
            print 'Please provide the routing key of the gather_queue'
            sys.exit(1)
        if len(self.args) >= 4:
            fetch_routing_key = unicode(self.args[3])
        else:
            print 'Please provide the routing key of the fetch_queue'
            sys.exit(1)    
        if len(self.args) >= 5:
            exchange_name = unicode(self.args[4])
        else:
            print 'Please provide the name of the exchange'
            sys.exit(1)

        context = {'model': model, 'user': self.admin_user['name'], 'session':model.Session}
        jobs = get_action('distributed_harvest_jobs_run')(context,{'gather_routing_key':gather_routing_key, 'source_id':source_id, 'exchange_name':exchange_name, 'fetch_routing_key':fetch_routing_key})



    def run_harvester(self):
        if len(self.args) >= 2:
            source_id = unicode(self.args[1])
        else:
            print 'Please provide the source-id'
            sys.exit(1)
            
        if len(self.args) >= 3:
            harvester_title = unicode(self.args[2])
        else:
            print 'Please provide the title of the harvester'
            sys.exit(1)       
            
        gather_routing_key = harvester_title  + '_gather_routing_key' 
        fetch_routing_key = harvester_title + '_fetch_routing_key' 
        exchange_name = self.EXCHANGE_NAME 

        context = {'model': model, 'user': self.admin_user['name'], 'session':model.Session}
        jobs = get_action('distributed_harvest_jobs_run')(context,{'gather_routing_key':gather_routing_key, 'source_id':source_id, 'exchange_name':exchange_name, 'fetch_routing_key':fetch_routing_key})


    def purge_queues(self):
        if len(self.args) >= 2:
            harvester_title = unicode(self.args[1])
        else:
            print 'Please provide the title of the harvester'
            sys.exit(1)
        
        gather_queue_name = harvester_title + '_gather_queue' 
        fetch_queue_name = harvester_title  + '_fetch_queue'
          
        from ckanext.distributedharvest.queue import purge_distributed_queues
        purge_distributed_queues(gather_queue_name, fetch_queue_name)
            
            
    def purge_queues_with_param(self):
        if len(self.args) >= 2:
            gather_queue_name = unicode(self.args[1])
        else:
            print 'Please provide the name of the gather queue'
            sys.exit(1)
        if len(self.args) >= 3:
            fetch_queue_name = unicode(self.args[2])
        else:
            print 'Please provide the name of the fetch queue'
            sys.exit(1)

          
        from ckanext.distributedharvest.queue import purge_distributed_queues
        purge_distributed_queues(gather_queue_name, fetch_queue_name)

