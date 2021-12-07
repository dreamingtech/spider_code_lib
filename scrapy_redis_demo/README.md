## scrapy 多爬虫多项目管理

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


