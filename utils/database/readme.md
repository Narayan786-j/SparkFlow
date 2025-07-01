# Laas Database Handler

Common Utility Library for database connections 

## Requirements: 

This utility has the following requirements:


```bash
SQLAlchemy
cx_oracle
contextlib
```

## Usage

```python

from startStopJobApi import utils as database

# Database Config to be used
config = {'dialect': "oracle", "sql_driver": "somedriver", "username": "some_username", "password": "somepassword",
          "host": "0.0.0.0", "port": "0000", "service": "SERVICENAME"}

# Create a instance of the DB resource class
db = database.DatabaseResource(config)


# Sample Function
def getallclusters():
    with db.session() as conn:
        data = conn.query(database.LaCluster).all()
    return data

```