import redis

def create_redis_client():
    r = redis.Redis(host='localhost', port=6379, db=0)
    return r

def insert(data, r):

    return r.lpush('vm_queue', data)

def get(r):
    return r.lpop('vm_queue')

def update_cache(data):
    client = create_redis_client()
    client.set('memory', str(data['memory']))
    client.set('hdd', str(data['hdd']))
    client.set('vcpus', str(data['vcpus'])
)
    client.close()


def available_resource():
    client = create_redis_client()
    memory = int(client.get('memory'))
    hdd = int(client.get('hdd'))
    vcpus = int(client.get('vcpus'))

    client.close()
    return {
        'memory': memory,
        'hdd': hdd,
        'vcpus': vcpus
    }


if __name__ == '__main__':
    client = create_redis_client()
    data = insert('test', client)
    print(data)

    data = get(client)
    print(data)
    data = get(client)
    print(data)

    client.close()