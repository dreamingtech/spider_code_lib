# -*- coding: utf-8 -*-
# dev settings
from . import *

# 使用 redis 和 mysql 测试库
REDIS_CONFIG = SETTINGS_DATABASE.get('redis_settings_dev')
REDIS_URL = 'redis://:{password}@{host}:{port}/{db}'.format(**REDIS_CONFIG)

MYSQL_CONFIG = SETTINGS_DATABASE.get('mysql_settings_dev')

LOG_LEVEL = 'DEBUG'
# LOG_LEVEL = 'INFO'
