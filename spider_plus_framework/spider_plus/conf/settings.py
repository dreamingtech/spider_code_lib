from .default_settings import *    # 全部导入默认配置文件的属性

# 执行爬虫时执行的是 main.py, 是在用户的爬虫项目中的 settings.py 的同级目录下执行的, 所以会优先导入用户自定义的 settings 中的配置, 这里的设置后覆盖掉前面 default_settings 中的设置
from settings import *