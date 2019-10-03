
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