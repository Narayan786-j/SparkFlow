'''
import logging.config

logging.config.fileConfig('utils/logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)
'''

import logging
import logging.config
import os

config_path = os.path.join(os.path.dirname(__file__), 'logging.conf')
logging.config.fileConfig(config_path, disable_existing_loggers=False)

logger = logging.getLogger('appLogger')
