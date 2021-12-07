# -*- coding: utf-8 -*-
# pro settings
from . import *

# 使用 redis 和 mysql 测试库
REDIS_CONFIG = SETTINGS_DATABASE.get('redis_settings_pro')
REDIS_URL = 'redis://:{password}@{host}:{port}/{db}'.format(**REDIS_CONFIG)

MYSQL_CONFIGS = {
    'mysql_settings_dev': SETTINGS_DATABASE.get('mysql_settings_dev'),
    'mysql_settings_pro': SETTINGS_DATABASE.get('mysql_settings_pro'),
}

# LOG_LEVEL = 'DEBUG'
LOG_LEVEL = 'INFO'

