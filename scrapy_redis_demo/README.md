## scrapy-redis 生成请求, 抓取 和 保存数据相分离

## 生成请求并保存到 redis 中

- dev 环境生成 project_demo hao123 请求
  - python exe_gen_seeds.py -p demo_dev -s hao123

- pro 环境生成 project_demo hao123 请求
  - python exe_gen_seeds.py -p demo_pro -s hao123

- pro 环境生成 project_news eastday 请求
  - python exe_gen_seeds.py -p news_dev -s eastday


## 运行爬虫

### 运行 project_demo 爬虫

- dev 环境运行 project_demo 所有爬虫
  - python exe_run_spider.py -p demo_dev

- pro 环境运行 project_demo 所有爬虫
  - python exe_run_spider.py -p demo_pro

- pro 环境运行 project_demo jianshu 爬虫
  - python exe_run_spider.py -p demo_pro -s jianshu

### 运行 project_news 爬虫

- dev 环境运行 project_news 所有爬虫
  - python exe_run_spider.py -p news_dev

- pro 环境运行 project_news 所有爬虫
  - python exe_run_spider.py -p news_pro

- pro 环境运行 project_news eastday 爬虫
  - python exe_run_spider.py -p news_pro -s eastday

## 建表

```sql
CREATE TABLE `demo` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `url` varchar(255) NOT NULL COMMENT 'url',
  `url_id` varchar(32) DEFAULT NULL COMMENT 'url_md5',
  `content` int(10) NOT NULL COMMENT '响应长度',
  `crawl` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '抓取时间',
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk` (`url_id`),
  KEY `url` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='demo';

CREATE TABLE `news` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `url` varchar(255) NOT NULL COMMENT 'url',
  `url_id` varchar(32) DEFAULT NULL COMMENT 'url_md5',
  `content` int(10) NOT NULL COMMENT '响应长度',
  `crawl` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '抓取时间',
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk` (`url_id`),
  KEY `url` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='demo';
```

## 从 redis 读取 items 批量保存到 mysql 中

- dev 环境运行
  - python exe_redis_to_mysql.py -p demo_dev

- pro 环境运行
  - python exe_redis_to_mysql.py -p demo_pro

```

python exe_gen_seeds.py -p demo_pro -s jianshu

2021-12-07 19:32:25 INFO    [exe_gen_seeds:151]: get arg parser from cmd
2021-12-07 19:32:25 INFO    [exe_gen_seeds:169]: parse params from arg parser
2021-12-07 19:32:25 INFO    [exe_gen_seeds:123]: start to gen requests for spider: [jianshu]
2021-12-07 19:32:25 INFO    [exe_gen_seeds:103]: do gen jianshu seeds
2021-12-07 19:32:25 INFO    [exe_gen_seeds:143]: total [1] seeds generated for spider: [jianshu]

python exe_gen_seeds.py -p demo_pro -s hao123

2021-12-07 19:32:42 INFO    [exe_gen_seeds:151]: get arg parser from cmd
2021-12-07 19:32:42 INFO    [exe_gen_seeds:169]: parse params from arg parser
2021-12-07 19:32:42 INFO    [exe_gen_seeds:123]: start to gen requests for spider: [hao123]
2021-12-07 19:32:42 INFO    [exe_gen_seeds:103]: do gen hao123 seeds
2021-12-07 19:32:42 INFO    [exe_gen_seeds:143]: total [1] seeds generated for spider: [hao123]

python exe_gen_seeds.py -p news_pro -s eastday

2021-12-07 19:32:58 INFO    [exe_gen_seeds:151]: get arg parser from cmd
2021-12-07 19:32:58 INFO    [exe_gen_seeds:169]: parse params from arg parser
2021-12-07 19:32:58 INFO    [exe_gen_seeds:123]: start to gen requests for spider: [eastday]
2021-12-07 19:32:58 INFO    [exe_gen_seeds:103]: do gen eastday seeds
2021-12-07 19:32:58 INFO    [exe_gen_seeds:143]: total [1] seeds generated for spider: [eastday]

python exe_gen_seeds.py -p news_pro -s sogou

2021-12-07 19:33:12 INFO    [exe_gen_seeds:151]: get arg parser from cmd
2021-12-07 19:33:12 INFO    [exe_gen_seeds:169]: parse params from arg parser
2021-12-07 19:33:12 INFO    [exe_gen_seeds:123]: start to gen requests for spider: [sogou]
2021-12-07 19:33:12 INFO    [exe_gen_seeds:103]: do gen sogou seeds
2021-12-07 19:33:12 INFO    [exe_gen_seeds:143]: total [1] seeds generated for spider: [sogou]

python exe_redis_to_mysql.py -p news_pro

2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:204]: get arg parser from cmd
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:222]: parse params from arg parser
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:195]: start to save items to mysql
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:117]: save items of to table [news]. length: [2]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:133]: no items in redis_key: [items:news], continue to next
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:145]: save items to mysql: [mysql_settings_dev]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:191]: save [2] item to table [news] affected rows: [4]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:145]: save items to mysql: [mysql_settings_pro]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:191]: save [2] item to table [news] affected rows: [0]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:117]: save items of to table [demo]. length: [2]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:133]: no items in redis_key: [items:demo], continue to next
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:145]: save items to mysql: [mysql_settings_dev]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:191]: save [2] item to table [demo] affected rows: [4]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:145]: save items to mysql: [mysql_settings_pro]
2021-12-07 19:42:12 INFO    [exe_redis_to_mysql:191]: save [2] item to table [demo] affected rows: [0]

```
