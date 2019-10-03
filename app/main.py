
import uuid

from flask import Flask
from flask import request
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp

from utils import db
from utils import cache_utils as cache



class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id


def authenticate(username, password):
    """
    AUthenticate and generate Token
    """
    con = db.get_connection()
    user = db.get_user_details(username, password, con)

    
    if (
        user and
        safe_str_cmp(user[1].encode('utf-8'), password.encode('utf-8'))
    ):

        # This will be used everywhere for authentication and role checking
        current_user = {
            'userid': user[0],
            'type': user[2]
        }

        user = User(current_user, user[0], user[1])
        return user

def identity(payload):
    """
    Getting the identity for the current user
    """
    user_id = payload['identity']
    return user_id

# Usual Flask stuff
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'

jwt = JWT(app, authenticate, identity)


@app.route('/health')
def health():
    """
    Health check API for the service
    """
    return 'I am working fine...'


@app.route('/create_user', methods = ['POST'])
@jwt_required()
def create_user():
    """
    User creation, olny for admins
    """

    status_code = 200

    if current_identity == 'user':
        result = {
            'success': False,
            'message': 'Unauthorised to perform this operation'
        }
        status_code = 401
    else:
        userid = request.headers.get('userid')
        password = request.headers.get('password')
        type_ = request.headers.get('type')
        result = db.create_user(userid, password, type_)

        if 'already exists' in str(result):
            result = {'success': True, 'message': 'User already exists'}
        else:
            result = {'success': True, 'message': 'User created Successfully'}

    return result, status_code


@app.route('/list_users', methods = ['GET'])
@jwt_required()
def list_users():
    """
    List all the users in the system, only for admins
    """
    status_code = 200

    if current_identity['type'] == 'user':
        result = {
            'success': False,
            'message': 'Unauthorised to perform this operation'
        }
        status_code = 401
    else:
        users = db.list_users()
        result = {'success': True, 'users': users}

    return result, status_code


@app.route('/delete_user', methods = ['DELETE'])
@jwt_required()
def delete_user():
    """
    Delete user permanently, only admins can perform this operation
    """
    # TO-DO: Check for the current user deletion - do not allow
    status_code = 200

    if current_identity['type'] == 'user':
        result = {
            'success': False,
            'message': 'Unauthorised to perform this operation'
        }
        status_code = 401
    else:
        userid = request.headers.get('userid')
        message = db.delete_user(userid)
        result = {'success': True, 'message': 'Deleted the user'}
    return result, status_code


@app.route('/create_vm', methods = ['POST'])
@jwt_required()
def create_vm():
    """
    Create a VM - which will make the entry in the DB and the Queue
    another service will get the ID from the queue and process the VM for 
    """
    # Generate a unique ID for each VM
    _id = str(uuid.uuid1())

    userid = request.headers.get('userid')

    status_code = 200
    # Validation for a normal user
    if (
        current_identity['type'] == 'user' 
        and userid !=  current_identity['userid']
    ):
            result = {
                'success': False,
                'message': 'You can\'t create VMs for other users'
            }
    else:
        memory = request.headers.get('memory')
        hdd = request.headers.get('hdd')
        vcpus = request.headers.get('vcpus')
        name = request.headers.get('name')

        # TO-DO Add basic validations for all these entries like numberix, 
        # range etc

        status = db.create_vm(name, userid, memory, hdd, vcpus, _id)

        print('Status from VM creation method', status)
        if status == 1:

            # Now time to Update the queue for the service to pick up and 
            # process the VM creation

            client = cache.create_redis_client()
            result = cache.insert(_id + ':' + userid , client)
            print('Updated the queue successfully...')
            result = {'success': True, 'message': 'VM creation in progress'}
        else:
            result = {'success': False, 'message': 'Something went wrong!'}

    return result, status_code


@app.route('/get_used_resources', methods = ['GET'])
@jwt_required()
def get_used_resources():
    """
    Get Used resources so that we can understand what is the current
    system load, it is used mainly internal services
    """
    status_code = 200
    if current_identity['type'] == 'user':
        result = {
            'success': False,
            'message': 'Only admin can use this API'
        }
    else:
        result = db.get_used_resources()
        details = {
            'memory': int(result[0]),
            'hdd': int(result[1]),
            'vcpus': int(result[2])
        }

        result = {'success': True, 'used_resources': details}

    return result, status_code


@app.route('/get_init_resources', methods = ['GET'])
@jwt_required()
def get_init_resources():
    """
    This is to get Node/cluster resource, how much is the total resouce
    available, mainly for internal use
    """
    status_code = 200
    if current_identity['type'] == 'user':
        result = {
            'success': False,
            'message': 'Only admin can use this API'
        }
    else:
        result = db.get_init_resources()
        details = {
            'memory': int(result[0]),
            'hdd': int(result[1]),
            'vcpus': int(result[2])
        }

        result = {'success': True, 'total_resources': details}

    return result, status_code


@app.route('/update_cache', methods = ['POST'])
@jwt_required()
def update_cache():
    """
    This API is for updating the cache DB, only for internal use
    """
    status_code = 200
    if current_identity['type'] == 'user':
        result = {
            'success': False,
            'message': 'Only admin can use this API'
        }
    else:
        
        data = {
            'memory': request.headers.get('memory'),
            'hdd': request.headers.get('hdd'),
            'vcpus': request.headers.get('vcpus')
        }
        result = cache.update_cache(data)

        result = {'success': True, 'total_resources': result}

    return result, status_code


@app.route('/init_vm', methods = ['POST'])
@jwt_required()
def init_vm():
    """
    Actual initialization of the VM is happening here
    Called by the service, with VM ID
    This will update start the VM, update the DBs and caches
    Onyl available for internal use, or admin use
    """

    status_code = 200
    vm_id = request.headers.get('vm_id')
    userid = request.headers.get('userid')

    if current_identity['type'] == 'user':
        result = {
            'success': False,
            'message': 'Only admin can use this API'
        }
    else:
        available_resource = cache.available_resource()
        print('Available resouce: ', available_resource)

        remaining_resource = db.init_vm(vm_id, userid, available_resource)
        print('remaining_resource: ', remaining_resource)

        # Update the cache with remaining resources if everything went fine
        if remaining_resource['message'] == 'success':
            # update the cache
            cache.update_cache(remaining_resource)
            result = {
                'success': True,
                'message': 'Successfully started the VM'
            }
        else:
            result = {
                'success': False,
                'message': remaining_resource['message']
            }

    return result, status_code


@app.route('/set_resource_limit', methods = ['POST'])
@jwt_required()
def set_resource_limit():
    """
    This API is for Admins to set resource limits for the users, for a user
    if resource limit is not set, then they can use unlimited resources
    """

    status_code = 200
    userid = request.headers.get('userid')
    memory = request.headers.get('memory')
    hdd = request.headers.get('hdd')
    vcpus = request.headers.get('vcpus')

    if current_identity['type'] == 'user':
        result = {
            'success': False,
            'message': 'Only admin can use this API'
        }
    else:
        db.set_resource_limits(userid, memory, hdd, vcpus)
        result = {
            'success': False,
            'message': 'Resource limit is set for the user {}'.format(userid)
        }

    return result, status_code


@app.route('/list_resources', methods = ['POST'])
@jwt_required()
def list_resources():
    """
    List created VMs and its details, both admin and user can use this API
    For admins, can list all the VMS
    For users, only the user created VMs
    """
    userid = current_identity['userid']
    user_type = current_identity['type']

    _all = False
    if user_type == 'admin':
        _all = request.headers.get('all')
        
    resources = db.list_resources(userid, _all)

    result = {
        'success': True,
        'resources': resources
    }

    return result, 200


@app.route('/delete_resources', methods = ['POST'])
@jwt_required()
def delete_resources():
    """
    Delete the resource
    Admin can delete any resource and user can delete only the one which user
    created
    Once delete the VM make sure the cache got updated with the latest resource
    details
    """
    current_userid = current_identity['userid']
    user_type = current_identity['type']

    userid = request.headers.get('userid')
    vm_id = request.headers.get('vm_id')

    result = {'success': True}
    status_code = 200
    if user_type == 'user' and userid != current_userid:
        print('User ID from token and args ', userid, current_userid)
        result['message'] = 'you cannot delete other user\'s resources'

    else:
        # Do the deletion
        d_resource_details = db.delete_resources(vm_id)
        result['message'] = 'Successfully deleted the resource {}'.format(
            vm_id
        )

        # update the Cache
        current_cache_details = cache.available_resource()
        new_cache_details = {
            'memory': (
                current_cache_details['memory'] + int(d_resource_details[1])),
            'hdd': (current_cache_details['hdd'] + int(d_resource_details[2])),
            'vcpus': (
                current_cache_details['hdd'] + int(d_resource_details[3]))
        }
        cache.update_cache(new_cache_details)
    
    return result, status_code


if __name__ == '__main__':
    app.run()