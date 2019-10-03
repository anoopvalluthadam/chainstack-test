import psycopg2


def get_connection():
    connection = psycopg2.connect(
        host='localhost', user='anoop', password='', database='chainstack',
        port="5432")

    return connection


def get_user_details(userid, password, con):
    cur = con.cursor()

    query = (
        "SELECT * from users where "
        + "userid='{}' AND password='{}' AND status='active'".format(
            userid, password)
    )

    cur.execute(query)
    rows = cur.fetchall()
    if rows:
        return rows[0]
    else:
        return []

def create_user(userid, password, type_):

    con = get_connection()
    cur = con.cursor()

    query = (
        "INSERT INTO users (userid,password,type, status) "
        + "VALUES ('{}', '{}', '{}', 'active')".format(userid, password, type_)
    )
    try:
        cur.execute(query)
        con.commit()
    except Exception as error:
        print('Error: ', error)
        con.close()
        return error

    return 1

def list_users():
    con = get_connection()
    cur = con.cursor()

    query = ("SELECT * from users")

    cur.execute(query)
    rows = cur.fetchall()
    if rows:
        users = []
        for row in rows:
            users.append(
                {
                    'userid': row[0],
                    'type': row[2],
                    'status': row[3]
                }
            )
        return users
        
    else:
        return []


def delete_user(userid):
    con = get_connection()
    cur = con.cursor()

    try:
        query = (
            "DELETE from USERS where userid='{}'".format(userid)
        )
        cur.execute(query)
        con.commit()
    except Exception as error:
        print('Error while deletion of a user: ', error)
        return None

    return cur.rowcount


def create_vm(name, userid, memory, hdd, vcpus, _id):
    con = get_connection()
    cur = con.cursor()

    query = (
        "INSERT INTO resource_allocation "
        + "(userid,memory,hdd,vcpus,status,name,id)"
        + " VALUES ('{}', {}, {}, {}, 'halted', '{}', '{}')".format(
            userid, memory, hdd, vcpus, name, _id)
    )
    print(query)
    try:
        cur.execute(query)
        con.commit()
    except Exception as error:
        print('Error: ', error)
        con.close()
        return error

    return 1


def get_used_resources():
    con = get_connection()
    cur = con.cursor()

    query = (
        "SELECT SUM(memory), SUM(hdd), SUM(vcpus) from resource_allocation"
        + " where status='running'"
    )

    cur.execute(query)
    rows = cur.fetchall()
    if rows:
        rows = rows[0]
        if not any(rows):
            rows = (0, 0, 0)
        return rows
    else:
        return [(0, 0, 0)]


def init_vm(vm_id, userid, available_resource):
    con = get_connection()
    cur = con.cursor()

    query = (
        "SELECT * from resource_allocation where id='{}'".format(vm_id)
    )
    print(query)
    cur.execute(query)
    rows = cur.fetchall()[0]
    
    memory = int(rows[1])
    hdd = int(rows[2])
    vcpus = int(rows[3])

    # TO-DO: Souldn't not allow a user to start a VM which is already started
    # Very important validation
    # Setp 0: get the VM details which user is gonna start:
    query = (
        "SELECT * from resource_allocation"
        + " WHERE id='{}'".format(vm_id)
    )
    cur.execute(query)
    vm_details = cur.fetchall()
    vm_details = vm_details[0]
    vm_details = {
        'memory': vm_details[1],
        'hdd': vm_details[2],
        'vcpus': vm_details[3],
        'status': vm_details[4]
    }
    if vm_details['status'] == 'running':
        return {'message': 'already running'}


    if (
        memory < available_resource['memory'] and 
        hdd < available_resource['hdd'] and
        vcpus < available_resource['vcpus']
    ):

        # Step 1:
        # Get total rsources used by this user
        # check if there is any resource limits set for this user first, if so
        # do a validation for that first
        # 
        query = (
            "SELECT SUM(memory), SUM(hdd), SUM(vcpus)"
            + " from resource_allocation"
            + " WHERE userid='{}' AND status='running'".format(userid)
        )
        print(query)

        cur.execute(query)
        total_resouces_used = cur.fetchall()
        if not total_resouces_used:
            total_resouces_used = [(0, 0, 0)]
        else:
            total_resouces_used = total_resouces_used[0]
            print('------> ', total_resouces_used)
            if not any(total_resouces_used):
                total_resouces_used = (0, 0, 0)

        # Step 2:
        # Get resource allocated for this user, if there is any! 
        query = (
            "SELECT memory, hdd, vcpus from resource_limits"
            + " WHERE userid='{}'".format(userid)
        )
        cur.execute(query)
        resource_limits_details = cur.fetchall()

        print('Current status about the quota...')
        print(total_resouces_used, resource_limits_details)
        print('-' * 20)

        # Step 3:
        # Validation for resource limit:
        if resource_limits_details:
            resource_limits_details = resource_limits_details[0]
            # Find the total resouces if we start the new VM
            new_memory = total_resouces_used[0] + int(vm_details['memory'])
            new_hdd = total_resouces_used[1] + int(vm_details['hdd'])
            new_vcpus = total_resouces_used[2] + int(vm_details['vcpus'])

            resource_limit_condition = (
                new_memory <= resource_limits_details[0] and
                new_hdd <= resource_limits_details[1] and
                new_vcpus <= resource_limits_details[2]
            )

            if not resource_limit_condition:
                try:
                    # Add a validation for not update if it is running
                    query = (
                        "UPDATE  resource_allocation "
                        + " SET comment='{}'".format(
                            'resource limit reached for the user')
                        + " WHERE id='{}'".format(vm_id)
                    )
                    cur.execute(query)
                    con.commit()
                except Exception as error:
                    print('Error while initialising the VM: ', error)
                    return {'message': 'Error in the VM init, contact admin'}
                return {'message': 'Resource limit reached'}

        try:
            # Add a validation for not update if it is running
            query = (
                "UPDATE  resource_allocation SET status='running',"
                + " comment='running'"
                + " WHERE id='{}'".format(vm_id)
            )
            cur.execute(query)
            con.commit()
        except Exception as error:
            print('Error while initialising the VM: ', error)
            return {'message': 'Error in the VM init, contact admin'}

        memory = available_resource['memory'] - memory
        hdd = available_resource['hdd'] - hdd
        vcpus = available_resource['vcpus'] - vcpus

        return {
            'memory': memory,
            'hdd': hdd,
            'vcpus': vcpus,
            'message': 'success'
        }
    else:
        try:
            # Add a validation for not update if it is running
            query = (
                "UPDATE  resource_allocation "
                + " SET comment='{}'".format(
                    'resource limit reached in the Node / Cluster')
                + " WHERE id='{}'".format(vm_id)
            )
            cur.execute(query)
            con.commit()
        except Exception as error:
            print('Error while initialising the VM: ', error)
            return {'message': 'Error in the VM init, contact admin'}
        return {'message': 'Resource limit reached in the Node, contact admin'}

def get_init_resources():
    con = get_connection()
    cur = con.cursor()

    query = (
        "SELECT * from resources"
    )
    cur.execute(query)
    total_resources = cur.fetchall()
    total_resources = total_resources[0]

    return total_resources


def set_resource_limits(userid, memory, hdd, vcpus):

    con = get_connection()
    cur = con.cursor()
    try:
        # Add a validation for not update if it is running
        query = (
            "UPDATE  resource_limits SET memory={}, ".format(memory)
            + "hdd={}, vcpus={}".format(hdd, vcpus)
            + " WHERE userid='{}'".format(userid)
        )
        cur.execute(query)
        con.commit()
    except Exception as error:
        print('Error while  set_resource_limits step 1: ', error)
        return None

    query = (
        "INSERT INTO resource_limits (userid,memory,hdd,vcpus) "
        + " SELECT '{}', {}, {}, {}".format(userid, memory, hdd, vcpus)
        + " WHERE NOT EXISTS "
        + "(SELECT 1 FROM resource_limits WHERE userid='{}')".format(
            userid
        )
    )
    try:
        cur.execute(query)
        con.commit()
    except Exception as error:
        print('Error while  set_resource_limits step 2: ', error)
        con.close()
        return error

def list_resources(userid, _all):
    
    con = get_connection()
    cur = con.cursor()

    if _all:
        query = (
           "SELECT * FROM resource_allocation"
        )
    else:
        query = (
           "SELECT * FROM resource_allocation WHERE userid='{}'".format(
               userid
           )
        )
    cur.execute(query)
    resources_allocation_details = cur.fetchall()

    result = []
    for res in resources_allocation_details:
        result.append(
            {
                'userid': res[0],
                'memory': int(res[1]),
                'hdd': int(res[2]),
                'vcpus': int(res[3]),
                'state': res[4],
                'name': res[5],
                'id': res[6],
                'comment': res[7]
            }
        )

    return result
    
def delete_resources(vm_id):
    con = get_connection()
    cur = con.cursor()

    query = (
        "SELECT * from resource_allocation where id='{}'".format(vm_id)
    )

    cur.execute(query)
    rows = cur.fetchall()
    if rows:
        rows = rows[0]
    else:
        return None
    
    try:
        query = (
            "DELETE from resource_allocation where id='{}'".format(vm_id)
        )
        cur.execute(query)
        con.commit()
    except Exception as error:
        print('Error while deletion of a user: ', error)
        return None

    return rows
    

if __name__ == '__main__':
    con = get_connection()
    # get_user_details('anoop@gmail.com', '1234', con)
    # create_user('user2@gmail.com', '1234', 'user')
    # users = list_users()
    # print(users)
    # create_vm('name', 'userid', 10, 10, 10)
    # print(get_used_resources())
    # print(get_init_resources())

    # print(get_init_resources('aafcb764-e507-11e9-aa0b-acde48001122'))
    # set_resource_limits('userid', 1200, 120, 5)
    print(list_resources('user1@gmail.com', True))