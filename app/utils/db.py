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
    )

    cur.execute(query)
    rows = cur.fetchall()
    if rows:
        return rows[0]
    else:
        return [(0, 0, 0)]


def init_vm(vm_id, available_resource):
    con = get_connection()
    cur = con.cursor()

    query = (
        "SELECT * from resource_allocation where id='{}'".format(vm_id)
    )

    cur.execute(query)
    rows = cur.fetchall()[0]
    
    memory = int(rows[1])
    hdd = int(rows[2])
    vcpus = int(rows[3])
    
    if (
        memory < available_resource['memory'] and 
        hdd < available_resource['hdd'] and
        vcpus < available_resource['vcpus']
    ):
        try:
            # Add a validation for not update if it is running
            query = (
                "UPDATE  resource_allocation SET status='running'"
                + " WHERE id='{}'".format(vm_id)
            )
            cur.execute(query)
            con.commit()
        except Exception as error:
            print('Error while initialising the VM: ', error)
            return None

        memory = available_resource['memory'] - memory
        hdd = available_resource['hdd'] - hdd
        vcpus = available_resource['vcpus'] - vcpus

        return {
            'memory': memory,
            'hdd': hdd,
            'vcpus': vcpus
        }


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
    