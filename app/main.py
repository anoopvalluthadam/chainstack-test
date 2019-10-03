
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
    con = db.get_connection()
    user = db.get_user_details(username, password, con)

    
    if user and safe_str_cmp(user[1].encode('utf-8'), password.encode('utf-8')):

        current_user = {
            'userid': user[0],
            'type': user[2]
        }
        user = User(current_user, user[0], user[1])
        return user

def identity(payload):
    user_id = payload['identity']
    print(user_id)
    return user_id

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'

jwt = JWT(app, authenticate, identity)

@app.route('/health')
def health():
    return 'I am working fine...'


@app.route('/create_user', methods = ['POST'])
@jwt_required()
def create_user():

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

    _id = str(uuid.uuid1())
    userid = request.headers.get('userid')
    # TO-DO: Check for the current user deletion - do not allow
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

        # TO-DO Add basic validations for all these entries

        status = db.create_vm(name, userid, memory, hdd, vcpus, _id)

        print('Status from VM creation method', status)
        if status == 1:

            # Now time to Update the queue for the service to pick up and 
            # process the VM creation

            client = cache.create_redis_client()
            result = cache.insert(_id, client)
            print(result)


            result = {'success': True, 'message': 'VM creation in progress'}
        else:
            result = {'success': False, 'message': 'Something went wrong!'}

    return result, status_code

@app.route('/get_used_resources', methods = ['GET'])
@jwt_required()
def get_used_resources():

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

    status_code = 200
    vm_id = request.headers.get('vm_id')
    if current_identity['type'] == 'user':
        result = {
            'success': False,
            'message': 'Only admin can use this API'
        }
    else:
        available_resource = cache.available_resource()
        print(available_resource)
        remaining_resource = db.init_vm(vm_id, available_resource)

        # update the cache
        cache.update_cache(remaining_resource)

    return remaining_resource, status_code


@app.route('/set_resource_limit', methods = ['POST'])
@jwt_required()
def set_resource_limit():

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




if __name__ == '__main__':
    app.run()