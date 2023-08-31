import ckan.plugins as p

from logging import getLogger
from ckanext.distributedharvest.commands.harvester import distributed_harvester

log = getLogger(__name__)
class DistributedHarvest(p.SingletonPlugin):

    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.IClick)


    ## IActions
    def get_actions(self):
        module_root = 'ckanext.distributedharvest.logic.action'
        action_functions = _get_logic_functions(module_root)

        return action_functions


    ## IAuthFunctions
    def get_auth_functions(self):

        module_root = 'ckanext.distributedharvest.logic.auth'
        auth_functions = _get_logic_functions(module_root)

        return auth_functions

    def get_commands(self):
        return [
            distributed_harvester
        ]

def _get_logic_functions(module_root, logic_functions = {}):

        module_name = 'update'
        module_path = '%s.%s' % (module_root, module_name)
        
        try:
            module = __import__(module_path)
        except ImportError:
            log.debug('No auth module for action "{0}"'.format(module_name))
            module = None

        for part in module_path.split('.')[1:]:
            module = getattr(module, part)

        for key, value in list(module.__dict__.items()):
            if not key.startswith('_') and  (hasattr(value, '__call__')
                        and (value.__module__ == module_path)):
                logic_functions[key] = value

        return logic_functions


