# -*- coding: utf-8 -*-
# 发送报警邮件的配置信息
# windows 放在 D:\settings 中, linux 放在 /data/spider/settings 中

# 发件人, 发件服务器 配置
email_user = {
    "host": "smtp.163.com",
    "port": 465,
    "user": "dreamingtech@163.com",
    "password": "dreamingtech",
}

# 发件人邮箱昵称, 发件人邮箱账号
email_sender = (
    "数据预警系统", 'dreamingtech@163.com'
)

# 自己
email_receivers_me = {
    "吴佳名": "dreamingtech@163.com",
}

# 开发
email_receivers_dev = {
    "吴佳名": "dreamingtech@163.com",
    "吴二楞": "dreamingtech@163.com",
}

# 技术
email_receivers_tec = {
    "吴佳名": "dreamingtech@163.com",
    "吴二楞": "dreamingtech@163.com",
    "吴二狗": "dreamingtech@163.com",
}
