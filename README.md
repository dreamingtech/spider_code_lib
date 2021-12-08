# spider_code_lib

- spider code snippets, projects, knowleages, etc.

## get_scrapy_settings

- 通过修改 scrapy get_project_settings, 可以通过传参来读取不同的配置文件, 从而整合多个爬虫项目, 或区分 dev, pro 环境, 

## run_scrapy_spider_from_file

- 从文件运行 scrapy spider

## scrapy_demo

- 基于改写的 get_project_settings 和 run_scrapy_spider_from_file 的多项目多爬虫展示代码

## scrapy_redis_demo/exe_gen_seeds.py

- 重写 scrapy-redis 的 Scheduler 和 Spider, 生成请求并保存到 redis 中

## scrapy_redis_demo/exe_redis_to_mysql.py

- 从 redis 中读取 scrapy items 并使用 aiomysql 异步批量保存到 mysql 中

## scrapy_redis_demo

- `生成请求`, `解析请求` 和 `保存数据` 分离的 scrapy-redis 分布式爬虫

## redis_queue

- 基于 redis list 的先进先出队列, 用于更新多项目多账号的 cookie

## ctrf_handler

- 基于 TimedRotatingFileHandler 改写的 CurrentTimedRotatingFileHandler

## bloom_filter

- 内存型和 redis 型布隆过滤器

# Todos

- [ ] README.md 文件的完善
- [ ] 出配套的视频说明
