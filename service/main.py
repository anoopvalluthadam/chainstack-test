import random
import asyncio
import json
import aioredis
from aiohttp import ClientSession

async def sync_cache(client, session, host):

    access_token = None
    url = host + 'auth'
    data = {
        "username": "anoop@gmail.com",
        "password": "1234"
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps(data)
    async with session.post(url, data=data, headers=headers) as response:
        access_token = await response.json()
        access_token = access_token.get('access_token', None)
        
    # get from persistant storage
    url = host + 'get_used_resources'
    headers = {
        "Authorization": "JWT {}".format(access_token)
    }
    used_resources = {}
    async with session.get(url, headers=headers) as response:
        used_resources = await response.json()
        used_resources = used_resources.get('used_resources', {})

    total_resources = {}
    url = host + 'get_init_resources'
    async with session.get(url, headers=headers) as response:
        total_resources = await response.json()
        total_resources = total_resources.get('total_resources', {})

    available = {
        'memory': total_resources['memory'] - used_resources['memory'],
        'hdd': total_resources['hdd'] - used_resources['hdd'],
        'vcpus': total_resources['vcpus'] - used_resources['vcpus']
    }
    print(available)
    # Update the cache
    headers = {
        "Authorization": "JWT {}".format(access_token),
        'memory': str(available['memory']),
        'hdd': str(available['hdd']),
        'vcpus': str(available['vcpus'])
    }
    url = host + 'update_cache'
    used_resources = {}
    async with session.post(url, headers=headers) as response:
        result = await response.read()
        print(result)



async def get_client():
    redis = await aioredis.create_redis(('localhost', 6379))
    return redis

async def get(client):
    return await client.lpop('vm_queue')

async def fetch(url, vm_id, session):
    async with session.get(url) as response:
        delay = response.headers.get("DELAY")
        date = response.headers.get("DATE")
        print("{}:{} with delay {}".format(date, response.url, delay))
        return await response.read()


async def bound_fetch(sem, vm_id, url, session):
    # Getter function with semaphore.
    async with sem:
        await fetch(url, vm_id, session)


async def run(r):
    url = "http://localhost:5000/"
    tasks = []
    # create instance of Semaphore
    sem = asyncio.Semaphore(1000)


    async with ClientSession() as session:
        client = await get_client()
        await sync_cache(client, session, url)

        while True:
            vm_id = await get(client)
            tasks = []
            print(vm_id)
            if not vm_id:
                print('Gonna take a nap...')
                await asyncio.sleep(2)
            else:
                print('Have something in the queue ', vm_id)
                task = asyncio.ensure_future(
                    bound_fetch(sem, vm_id, url, session)
                )
                tasks.append(task)

                responses = asyncio.gather(*tasks)
                await responses


if __name__ == '__main__': 
    number = 10000
    loop = asyncio.get_event_loop()

    future = asyncio.ensure_future(run(number))
    loop.run_until_complete(future)