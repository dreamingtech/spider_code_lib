# -*- coding: utf-8 -*-
# pro settings
from . import *

# 使用 redis 和 mysql 测试库
REDIS_CONFIG = SETTINGS_DATABASE.get('redis_settings_pro')
MYSQL_CONFIG = SETTINGS_DATABASE.get('mysql_settings_pro')

REDIS_URL = 'redis://:{password}@{host}:{port}/{db}'.format(**REDIS_CONFIG)

# LOG_LEVEL = 'DEBUG'
LOG_LEVEL = 'INFO'

