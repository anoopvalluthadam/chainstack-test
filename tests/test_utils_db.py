import os,sys,inspect
import json
from mock import patch
import mock

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


def test_get_user_details():

    connection = mock.Mock()
    connection.cursor().fetchall.return_value = []
    result = db.get_user_details('userid', 'password', connection)

    assert not result
    