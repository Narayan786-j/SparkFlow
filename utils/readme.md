# Common utilities for all services

This directory contains all common utilities that will be used by all services

## Utility Available:

#### 1. Common database handler can be found [here](database/readme.md)
#### 2. [Exception.py](exceptions.py): Common exception class for all services
#### 3. [Logging.py](logger.py): Common file containing the logger function
#### 4. [Logging.conf](logging.conf): Configuration file for the python logger
#### 5. [Properties.py](properties.py): Property file containing all env specific variables



## Usage

```python
# Example on how to use property file values
from startStopJobApi.utils import Properties

cfg = Properties()

# Get Database Credentials
db_credentialas = cfg.oracle_database_credentials

# Get a service URL
kafkaService = cfg.core_services['services']['kafka']
----------------------------------------------------------

# Example of how to use custom exception class 
from startStopJobApi.utils import Error

if 1 == 1:
    status_code = 400
    details = "Something Went Wrong!"
    raise Error(status_code, details)
----------------------------------------------------------
# Example of how to use logging
from startStopJobApi.utils import logger


def DummyFunction():
    logger.info("Function called !")

```

## Contributing
For any changes/modifications to the Utils library please use the feature/utils branch

Please make sure to update tests as appropriate.