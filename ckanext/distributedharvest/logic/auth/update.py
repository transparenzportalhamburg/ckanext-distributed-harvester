from ckan.plugins import toolkit as pt
from ckanext.harvest.logic.auth import user_is_sysadmin


def distributed_harvest_jobs_run(context, data_dict):
    '''
        Authorization check for running the pending harvest jobs

        Only sysadmins can do it
    '''
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': pt._('Only sysadmins can run harvest jobs')}
    else:
        return {'success': True}

