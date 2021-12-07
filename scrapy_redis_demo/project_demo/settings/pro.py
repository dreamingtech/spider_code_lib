# -*- coding: utf-8 -*-
# pro settings
from . import *

# 使用 redis 和 mysql 测试库
REDIS_CONFIG = SETTINGS_DATABASE.get('redis_settings_pro')
REDIS_URL = 'redis://:{password}@{host}:{port}/{db}'.format(**REDIS_CONFIG)

# 在线上环境运行时, 可能要同时保存到 dev 和 pro 数据库
MYSQL_CONFIGS = {
    'mysql_settings_dev': SETTINGS_DATABASE.get('mysql_settings_dev'),
    'mysql_settings_pro': SETTINGS_DATABASE.get('mysql_settings_pro'),
}

# LOG_LEVEL = 'DEBUG'
LOG_LEVEL = 'INFO'

