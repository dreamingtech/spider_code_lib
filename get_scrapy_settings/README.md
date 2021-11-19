## scrapy get_project_settings 的作用和改进

### get_project_settings 的作用

- 从此 scrapy 官方文档中可以得知此方法的作用
  - https://docs.scrapy.org/en/latest/topics/practices.html#run-scrapy-from-a-script
  - use get_project_settings to get a Settings instance with your project settings.
  - 即读取相当的 settings.py 配置文件

- 新建 scrapy 项目, 调试, 获得 get_project_settings 的作用

- scrapy startproject test_settings
- cd test_settings
- scrapy genspider test baidu.com


- 查看 get_project_settings 的源码


