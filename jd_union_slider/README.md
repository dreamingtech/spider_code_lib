## 京东联盟缺口滑块验证码

- https://union.jd.com/index 滑块验证码识别

- windows 上运行
- 手动打开浏览器并开启 9222 端口, selenium 通过已打开 9222 连接浏览器
- 使用 pynput 控制系统鼠标和键盘输入
- 使用 https://www.jsdati.com/ 联众验证码识别服务识别缺口位置
- 使用 pynput 输入用户名, 密码并模拟登录
- pywin32 模块获取并切换键盘布局 
- 使用缓动函数生成移动轨迹


## TODOS

-[x] 中文输入法时无法正确输入用户名和密码, 会输入成中文
-[ ] 使用前修改 settings.__init__.py 中的 USER_LIAN_ZHONG 为自己的联众信息
