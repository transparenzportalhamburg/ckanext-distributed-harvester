import types
from logging import getLogger

from sqlalchemy.util import OrderedDict

from ckan import logic
from ckan import model
import ckan.plugins as p
from ckan.lib.plugins import DefaultDatasetForm
from ckan.lib.navl import dictization_functions

from ckanext.distributedharvest import logic as harvest_logic

from ckanext.harvest.model import setup as model_setup
from ckanext.harvest.model import HarvestSource, HarvestJob, HarvestObject



log = getLogger(__name__)
assert not log.disabled


class DistributedHarvest(p.SingletonPlugin):

    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)


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


def _get_logic_functions(module_root, logic_functions = {}):

        module_name = 'update'
        module_path = '%s.%s' % (module_root, module_name)
        
        try:
            module = __import__(module_path)
        except ImportError:
            log.debug('No auth module for action "{0}"'.format(module_name))
            

        for part in module_path.split('.')[1:]:
            module = getattr(module, part)

        for key, value in module.__dict__.items():
            if not key.startswith('_') and  (hasattr(value, '__call__')
                        and (value.__module__ == module_path)):
                logic_functions[key] = value

        return logic_functions

