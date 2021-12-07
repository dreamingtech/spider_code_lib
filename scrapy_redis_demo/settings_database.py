# -*- coding: utf-8 -*-
# mysql 和 redis 的配置信息
# windows 放在 D:\settings 中, linux 放在 /data/spider/settings 中

# mysql 测试环境
mysql_settings_dev = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'spider',
    'password': 'spider',
    'db': 'spider',
    'charset': "utf8",
}

# mysql 线上环境
mysql_settings_pro = {
    'host': '127.0.0.2',
    'port': 3306,
    'user': 'spider',
    'password': 'spider',
    'db': 'spider',
    'charset': "utf8",
}

# redis 测试环境
redis_settings_dev = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 1,
    'password': 'spider',
}

# redis 线上环境
redis_settings_pro = {
    'host': '127.0.0.2',
    'port': 6379,
    'db': 0,
    'password': 'spider',
}
