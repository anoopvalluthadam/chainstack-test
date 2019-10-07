```
Architecture

+--------------+                                                    +--------------+
|              |                                                    |              |
|              |                                                    |              |
|              |           +------------------------------------+   |              |
|              |           |               Queue                |   |              |
|              +----------->                                    +-->+              |
|  API Layer   |           +------------------------------------+   |   Service    |
|              |                                                    |              |
|              |                                                    |              |
|              |                        +---------------------------+              |
|              |                        |                           |              |
|              |                        |                           |              |
|              |                        |                           +------+-------+
+-------+------+                        |                                  |
        |                               |                                  |
        |                               |                                  |
        |                               |                                  |
        |                         +-----v------+            +------------+ |
        |                         |            |            |            | |
        |                         |            |            |            | |
        |                         |            |            |            +<+
        |                         |            |            |   Cache    |
        |                         |     DB     |            |            |
        |                         |            |            |            |
        |                         |            |            |            |
        |                         |            |            +------+-----+
        |                         +------------+                   ^
        |                                                          |
        |                                                          |
        |                                                          |
        +----------------------------------------------------------+
```

# API Documentation: 
https://documenter.getpostman.com/view/3471667/SVtR1VZe?version=latest


# How install dependencies
Make sure redis and postgress is installed in the system

Create DB
```sh
pg_dump -U anoop chainstack < chainstack.pgsql
```

```sh 
virtualenv -p python3 VENV3
 source VENV3/bin/activate
 pip install -r requirements.txt
 
```

# How to run the API
```sh
cd app
python main.py
```
# How to run the service
```sh
cd service
python main.py
```
# How to run the testcases
```sh
cd tests
pytest
```