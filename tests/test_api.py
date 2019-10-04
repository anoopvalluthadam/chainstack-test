import os,sys,inspect
import json
from mock import patch

# This is to make sure that ROOT dir added to the SYS path so that all the
# modules are accessible thought the project to make sure the reuse of the code
currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from app.main import create_app
from app.utils import db

from app.utils.db import create_user

import pytest


@pytest.fixture
def app():
    app = create_app()
    return app


@pytest.fixture
def admin_access_token(client):
    body = {
        "username": "testadmin@gmail.com",
        "password": "ThisIsATestToKen@#$%&Admin"
    }
    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }
    response = client.post("/auth", data=json.dumps(body), headers=headers)

    return response.json['access_token']


@pytest.fixture
def user_access_token(client):
    body = {
        "username": "testuser@gmail.com",
        "password": "ThisIsATestToKen@#$%&User"
    }
    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }
    response = client.post("/auth", data=json.dumps(body), headers=headers)

    return response.json['access_token']


def test_example(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_auth(client):
    body = {
        "username": "testadmin@gmail.com",
        "password": "ThisIsATestToKen@#$%&Admin"
    }
    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }
    response = client.post("/auth", data=json.dumps(body), headers=headers)
    assert response.status_code == 200
    assert response.json['access_token']

@patch('app.utils.db.create_user')
def test_create_user(create_user, client, admin_access_token):

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype,
        'Authorization': 'JWT {}'.format(admin_access_token),
        'userid': 'test@gmail.com',
        'password': 'test',
        'type': 'user'
    }
    response = client.post(
        "/create_user", headers=headers)

    assert response.status_code == 200
    

@patch('app.utils.db.list_users')
def test_list_users(list_users, client, admin_access_token):

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype,
        'Authorization': 'JWT {}'.format(admin_access_token)
    }
    list_users.return_value = {}
    response = client.get("/list_users", headers=headers)

    assert response.status_code == 200


@patch('app.utils.db.delete_user')
def test_delete_user(delete_user, client, admin_access_token):

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype,
        'Authorization': 'JWT {}'.format(admin_access_token),
        'userid': 'test'
    }
    delete_user.return_value = {}
    response = client.delete("/delete_user", headers=headers)
    assert response.status_code == 200


@patch('app.utils.db.create_vm')
@patch('app.utils.cache_utils.create_redis_client')
@patch('app.utils.cache_utils.insert')
def test_create_vm(
    insert, create_redis_client, create_vm, client, admin_access_token):

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype,
        'Authorization': 'JWT {}'.format(admin_access_token),
        'userid': 'test',
        'memory': 100,
        'vcpus': 10,
        'hdd': 200,
        'name': 'Test'
    }
    create_vm.return_value = 1
    response = client.post("/create_vm", headers=headers)
    assert response.status_code == 200


@patch('app.utils.db.init_vm')
@patch('app.utils.cache_utils.available_resource')
@patch('app.utils.cache_utils.update_cache')
def test_init_vm(
    update_cache, available_resource, init_vm, client, admin_access_token):

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype,
        'Authorization': 'JWT {}'.format(admin_access_token),
        'userid': 'test',
        'vm_id': '100'
    }
    
    init_vm.return_value = {'message': 'success'}

    response = client.post("/init_vm", headers=headers)
    assert response.status_code == 200


@patch('app.utils.db.list_resources')
def test_init_vm(
    list_resources, client, admin_access_token):

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype,
        'Authorization': 'JWT {}'.format(admin_access_token)
    }
    
    list_resources.return_value = []

    response = client.post("/list_resources", headers=headers)
    assert response.status_code == 200
    