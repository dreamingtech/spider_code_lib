# -*- coding: utf-8 -*-
# 登录的基类
import base64
import importlib
import json
import os
import random
import re
import subprocess
import time
from io import BytesIO

import requests
import selenium
import numpy as np
import win32api
import win32gui
from PIL import Image
from selenium.webdriver import Chrome, ChromeOptions, ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from pynput.mouse import Controller as Mouse
from pynput.keyboard import Controller as KeyBoard
from win32con import WM_INPUTLANGCHANGEREQUEST

from jd_union_slider.utils import get_logger
from jd_union_slider.utils.pynput import Pynput
from jd_union_slider.utils.lianzhong import LianZhong

logger = get_logger(re.split(r"[/.\\]", __file__)[-2])


class BaseLogin(object):

    def __init__(self, settings, use_pynput=False):
        """
        :param settings: settings.py 中的配置信息
        :param use_pynput: 是否使用 pynput 输入和控制鼠标
        :return:
        """
        self.CHROME = settings['CHROME']

        # 如果使用 pynput 输入, 就实例化鼠标和键盘
        self.use_pynput = use_pynput
        if use_pynput:
            self.mouse = Mouse()
            self.keyboard = KeyBoard()
            # 如果使用 pynput 输入, 加载并设置为英文键盘
            self.load_keyboard_layout()
            self.set_keyboard_layout()
        else:
            self.mouse = None
            self.keyboard = None

        # 第一级到第三级 iframe 的 xy 坐标
        # 如果存在一层或多层嵌套的 iframe, 需要一层层计算获取元素位置
        self.p_iframe_xy = None
        self.pp_iframe_xy = None
        self.ppp_iframe_xy = None

        # chrome 浏览器包括标签栏, 地址栏, 收藏夹栏在内的高度
        # 在 use_pynput 的时候才需要获取到 top_bar_height 的值, 以用来计算元素的真实位置坐标
        self.top_bar_height = 0

        # 子类中重写
        self.username = None

        # 手动打开 chrome 的脚本
        self.script = None
        # selenium browser 对象
        self.browser = None
        # chrome options
        self.options = None

        # 所有的键盘布局
        # {'00000401': 'Arabic (101)', '00000402': 'Bulgarian (Typewriter)'}
        self.keyboard_layout = {}

        # 联众验证码识别服务
        self.lianzhong = LianZhong(user=settings['USER_LIAN_ZHONG'])

        self.ease_functions = importlib.import_module(name='utils.ease_functions', package='jd_union_slider').__dict__

    def get_tracks(self, distance, seconds, func_name):
        """
        获取鼠标拖动轨迹
        :param distance:
        :param seconds:
        :param func_name:
        :return:
        """
        tracks = [0]
        offsets = [0]
        for t in np.arange(0.0, seconds, 0.1):
            ease_func = self.ease_functions.get(func_name)
            offset = round(ease_func(t / seconds) * distance)
            tracks.append(offset - offsets[-1])
            offsets.append(offset)
        return offsets, tracks

    def get_element_center(self, element: WebElement):
        """
        计算元素的中心点坐标
        腾讯广告 丧心病狂的三层 iframe 结构
        :param element: 要计算的元素
        :return:
        """
        if self.p_iframe_xy is None:
            self.p_iframe_xy = {"x": 0, "y": 0}
        if self.pp_iframe_xy is None:
            self.pp_iframe_xy = {"x": 0, "y": 0}
        if self.ppp_iframe_xy is None:
            self.ppp_iframe_xy = {"x": 0, "y": 0}

        x_middle = element.location["x"] + 0.5 * element.size["width"] + self.p_iframe_xy["x"] + self.pp_iframe_xy[
            "x"] + self.ppp_iframe_xy["x"]
        y_middle = element.location["y"] + 0.5 * element.size["height"] + self.p_iframe_xy["y"] + self.pp_iframe_xy[
            "y"] + self.ppp_iframe_xy["y"] + self.top_bar_height

        return {"x": x_middle, "y": y_middle}

    def get_top_bar_height(self):
        """
        要计算元素在屏幕中的真实位置, 必须要获取以下 2 个值
        1. 获取 chrome 上方包括标签栏，地址栏, 书签栏的高度
        获取 chrome 上方包括标签栏，地址栏, 书签栏的高度
        全屏时 html 元素的高度 - 最大化时 html 元素的高度 - 任务栏的高度
        2. 获取任务栏高度
        全屏下 window_size - 最大化时 window_size,
        但是最大化时窗口位置为 {'x': -8, 'y': -8}, 即开始位置为 {'x': -8, 'y': -8}, 结束位置则为 {'x': 1920+8, 'y': 1080+8}
        所以要用最大化时获取到的窗口大小 减去 16 才得到真正的窗口大小, 也即 加上 -16
        :return:
        """
        # 先设置窗口为 800 * 600，以免最初窗口处于全屏状态
        self.browser.set_window_size(800, 600)
        time.sleep(1)
        # 设置窗口全屏
        self.browser.fullscreen_window()
        time.sleep(1)
        # 全屏时 window 的高度
        window_heigh_f = self.get_window_height()
        # 全屏时 html 的高度
        html_f = self.browser.find_element_by_tag_name("html")
        # 注意，必须要使用这种赋值的方式，不能在下面计算 top_bar_height 时直接使用 html_f.size["height"] 的值来计算
        # 因为 html_f 和 html_m 是同一个元素，最大化窗口后再取值，二者的值就完全相同相同了
        html_f_height = html_f.size["height"]
        time.sleep(0.5)

        # 设置窗口最大化
        self.browser.maximize_window()
        time.sleep(1)
        # 获取最大化时窗口的高度
        window_height_m = self.get_window_height()
        # 获取最大化时 html 的高度
        html_m = self.browser.find_element_by_tag_name("html")
        html_m_height = html_m.size["height"]

        # 任务栏的高度, 等于全屏时的高度 - 最大化时的高度
        taskbar_height = window_heigh_f - window_height_m

        # chrome 上方包括标签栏，地址栏, 书签栏的高度
        # 约等于 103
        self.top_bar_height = html_f_height - html_m_height - taskbar_height

    def get_window_height(self):
        """
        获取 window 的高度
        :return:
        """
        window_size = self.browser.get_window_size()
        window_position = self.browser.get_window_position()
        # maximize 最大化窗口时真正的高度, 必须要加上窗口起始位置，也可用于 全屏时
        window_height = window_size["height"] + window_position["y"] * 2
        return window_height

    def try_wait_do(self, by: str, ele_sign, retry: int = 5, wait_time: int = 3, action=None, params=None):
        """
        使用 selenium 或 appium 执行操作
        :param by:
        :param ele_sign:
        :param retry: 重试的次数
        :param wait_time: 每次重试的等待时间
        :param action:
        :param params:
        :return:
        """
        if not by.startswith('find_element_by'):
            by = f'find_element_by_{by}'

        self.browser: selenium.webdriver.Chrome

        for i in range(retry):

            logger.info(f'try to find element: {ele_sign} for [{i + 1}th/{retry}] time')

            try:
                # 在 指定的 wait_time 中, 循环尝试查找 某个/某些 元素, 如果找到了, 执行下一步的操作
                if WebDriverWait(self.browser, wait_time).until(lambda x: getattr(x, by)(ele_sign)):
                    # 如果 element_action 不为空, 就对 某个/某些元素 执行对应的操作, 并把操作的结果返回
                    if action:
                        if params:
                            return getattr(getattr(self.browser, by)(ele_sign), action)(params)
                        return getattr(getattr(self.browser, by)(ele_sign), action)()
                    # 如果 element_action 为空, 就返回查找到的 某个/某些 元素
                    return getattr(self.browser, by)(ele_sign)
            except Exception as e:
                logger.error(
                    f"find element(s) error. "
                    f"element: {ele_sign}, "
                    f"error type: {type(e).__name__}, "
                    f"error: {str(e)}."
                )

    def close_windows_process(self, process_name="chrome.exe"):
        """
        在 windows 中关闭 某个进程
        :return:
        """
        logger.info(f'try to close process: {process_name}')

        # 使用 /F /T 参数, 会引起浏览器关闭异常, 再次打开时会弹出提示
        # close_cmd = 'taskkill /F /IM 360se.exe /T'
        # close_cmd = 'taskkill /IM 360se.exe'
        close_cmd = f'taskkill /IM {process_name}'
        for i in range(50):
            result = subprocess.getstatusoutput(close_cmd)
            logger.info(f'close process: {process_name} output: {result}')

            time.sleep(1)
            if '没有找到进程' in result[-1] and process_name in result[-1]:
                logger.info(f'successfully closed process: {process_name}. continue...')
                break
            # 360 浏览器有时候无法正常关闭, 需要使用 /F 选项
            # close process: 360se.exe output: (1, '错误: 无法终止进程 "360se.exe", 其 PID 为 9380。\n原因: 只能强行终止这个进程(带 /F 选项)。')
            # error closing process 360se.exe, retrying...
            elif '只能强行终止这个进程' in result[-1] and process_name in result[-1]:
                close_cmd = f'taskkill /F /IM {process_name} /T'
                result = subprocess.getstatusoutput(close_cmd)
                logger.info(f'force close process: {process_name} output: {result}')
            else:
                logger.warning(f'error closing process {process_name}, retrying...')
                time.sleep(2)
                self.close_windows_process(process_name)
        else:
            logger.warning(f'retied for 50 times, process {process_name} not closed')

    def close_existing_chrome(self):
        """
        关闭已经手动打开的 chrome 浏览器,
        因为 华为每次在 正常的 chrome 中登录后, 即使清空所有的 cookies, 再次打开登录页依然处于登录状态
        又如 收益-东方头条, 每次在正常的 chrome 中登录, 即使清空所有的 cookies, 再次登录其它账号后, 还是显示上一个账号的信息
        为了保险起见, 每次都使用 无痕模式打开浏览器登录, 登录一个就退出 一个
        保证每次都没有 手动打开的浏览器在运行
        使用 chrome 的 开发协议关闭 手动打开远程调试端口的 chrome 浏览器
        https://chromedevtools.github.io/devtools-protocol/
        http://127.0.0.1:9222/json/close/5AE435FA41CBB680049B74D143BE4EE4
        http://127.0.0.1:9222/json/list
        :return:
        """
        # 如果 9222 端口不可用, 就退出
        if not self.check_9222_port():
            return

        # 如果浏览器已经打开, 就通过 request 发送请求关闭所有的 chrome
        for i in range(20):
            try:
                tab_infos = requests.get(url="http://127.0.0.1:9222/json/list")
                tab_infos.json()
            except Exception as e:
                logger.error(
                    f"error get chrome tab list. "
                    f"error type: {type(e).__name__}, error: {str(e)}"
                )
                return
            # 遍历并关闭所有的 chrome 标签
            for tab_info in tab_infos.json():
                _id = tab_info.get("id")
                title = tab_info.get("title")

                try:
                    response_close = requests.get(url=f"http://127.0.0.1:9222/json/close/{_id}")
                    logger.info(f"close chrome tab [{title}] result [{response_close.text}]")

                except Exception as e:
                    logger.warning(
                        f"error close chrome tab. "
                        f"title: [{title}], error type: [{type(e).__name__}], error: [{str(e)}]"
                    )

        else:
            logger.warning('retried for 20 times, chrome still not closed')

    def close_all(self):
        """
        关闭 chrome 相关的所有进程
        """
        # 使用 close_existing_chrome 来关闭 chrome, 以避免出现打开浏览器时提示 浏览器异常关闭
        self.close_existing_chrome()
        # selenium 打开的 chrome 正在运行时, 不会影响到 手动打开浏览器
        # 如果不区分 auto, semi, 和 manual, 都使用 手动打开的浏览器进行登录, 就要先关闭所有的 chromedriver.exe
        self.close_windows_process(process_name="chromedriver.exe")
        self.close_windows_process(process_name="chrome.exe")

    def get_options(self):
        """
        获取 ChromeOptions
        """
        self.options = ChromeOptions()
        # 最大化窗口
        # self.options.add_argument("start-maximized")
        # 禁用扩展程序
        self.options.add_argument("--disable-extensions")
        # 打开 9222 端口
        # 通过远程 debug 端口连接到手动打开的 chrome
        # 在 cmd 中启用 chrome remote-debug, 注意启动之前一定要先关闭所有的 chrome 浏览器
        # chrome.exe --remote-debugging-port=9222
        # 访问 http://127.0.0.1:9222/json 来确保服务启动成功
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    def get_browser(self):
        """
        使用 selenium 打开 chrome
        使用 selenium 连接 手动打开的 chrome
        :return:
        """
        logger.info("open/connect to chrome browser")
        # 把对应版本的 chromedriver.exe 放在 settings_xxx.py 中 sys.path.append 的路径中
        # 这样, 就可以不用指定完整的路径, 也不用把 几个兆 的文件保存在 git 中了
        self.browser = Chrome(
            executable_path='{driver_path}'.format(**self.CHROME),
            chrome_options=self.options,
        )
        self.browser.set_page_load_timeout(time_to_wait=60)

    def check_9222_port(self):
        """
        1. 检查 chrome 进程是否存在, 如果不存在, 启动, 如果存在, 检测 9222 端口是否能够连通
        2. 如果 9222 端口可以访问, 就继续. 如果 9222 端口不能访问, 关闭 所有 chrome, 重新启动, 直到能够访问 9222 端口
        检测 9222 端口, 保证手动打开的 chrome 一直在运行着
        在 selenium 打开 chrome 之前, 检测 9222 端口是否打开,
        如果没有, 关闭所有的 chrome 进程, 先手动打开 chrome, 再使用 selenium 打开 chrome
        :return:
        """
        logger.info("check chrome 9222 port.")
        try:
            response = requests.get(url="http://127.0.0.1:9222/json", timeout=8)
            json.loads(response.content)
            return True
        except Exception as e:
            logger.error(
                f"unable to connect localhost 9222. "
                f"error type: {type(e).__name__}, error: {str(e)}"
            )
            return False

    def get_script(self):
        """
        获取 打开 chrome 的 script
        :return:
        """
        # 每个用户的 chrome 临时文件都放在一个目录中
        # 去除掉 非英文和数字
        username_raw = re.sub(r'\W', '', self.username)

        # user_dir = rf'D:\Chrome\report_cost\huawei\129834021'
        user_dir = rf'D:\Chrome\{username_raw}'
        if not os.path.isdir(user_dir):
            os.makedirs(user_dir)

        chrome_path = '{chrome_path}'.format(**self.CHROME)
        sb = '--remote-debugging-port=9222 --disable-plugins --start-maximized'

        self.script = rf'"{chrome_path}" {sb} --user-data-dir={user_dir}'

    def open_chrome_manually(self):
        """
        使用代码手动打开浏览器
        """
        logger.info("open chrome browser manually")

        # 重试 5 次
        for i in range(5):
            # 检测 9222 端口是否可用
            if not self.check_9222_port():
                logger.warning("chrome remote service is unreachable, restart chrome")
                subprocess.Popen(self.script, shell=True)
                time.sleep(3)
            # 如果检测到了 9222 端口, 就先使用 selenium 连接, 退出
            else:
                # 华为在删除所有的 cookie 之后, 再次刷新, 打开登录页后依然处理登录状态,
                # 所以这里打开 无痕页面, 就能解决此问题了
                logger.info("chrome remote service is available")
                return True
        else:
            logger.warning("retried for 5 times, chrome is not open, please check")

        return False

    def get_image_size(self, image, save=False):
        """
        获取图片的尺寸
        :param image: base64 image 或 二进制的 image
        :param save: 是否保存到本地
        :return:
        """
        # 如果是 base64 格式的, 就转换先解析成 bytes 类型的
        if isinstance(image, str) and image.startswith("data:image/"):
            try:
                image = base64.b64decode(image.split(',', maxsplit=1)[-1])
            except Exception as e:
                print("error decode base64 image. error: {}".format(e))
                return

        if isinstance(image, bytes):
            if save is True:
                suffix = random.randint(1000, 9999)
                with open("img_{}.png".format(suffix), "wb") as f:
                    f.write(image)
            try:
                img_data = BytesIO(image)
                img_real = Image.open(img_data)
                img_size = img_real.size
                if img_size and len(img_size) == 2:
                    img_size_d = {"width": img_size[0], "height": img_size[-1]}
                    return img_size_d
                else:
                    logger.warning("img_size obtained from PIL is empty, check check")
            except Exception as e:
                logger.error(
                    f"error get image_size. "
                    f"error type: {type(e).__name__}, error: {str(e)}"
                )
        else:
            raise Exception(f"unsupported image type: {type(image)}, check check.")

    def load_keyboard_layout(self):
        """
        有时候系统中未加载英文键盘, 需要手动加载
        """
        r_load = win32api.LoadKeyboardLayout('00000409', 1)
        if hex(r_load & (2**16 - 1)) == '0x409':
            logger.info('load en keyboard layout succeed')

        r_load = win32api.LoadKeyboardLayout('00000804', 1)
        if hex(r_load & (2**16 - 1)) == '0x804':
            logger.info('load cn keyboard layout succeed')

    def set_keyboard_layout(self, lan='en'):
        """
        设置键盘布局为英文
        输入 pynput 输入用户名和密码之前, 修改键盘布局为 英文
        """
        logger.info('set keyboard layout')
        # 获取前景窗口句柄
        hwnd = win32gui.GetForegroundWindow()

        # 获取当前窗口的标题
        title = win32gui.GetWindowText(hwnd)

        logger.info(f'front most window title: {title}')

        layout = 0x0409
        if lan == 'cn':
            layout = 0x0804

        result = win32api.SendMessage(
            hwnd,
            WM_INPUTLANGCHANGEREQUEST,
            0,
            layout)

        if result == 0:
            logger.info(f'set {lan} keyboard layout succeed')

    def input_and_login(self, ele_user, ele_pass, ele_btn, username, password):
        """
        执行输入用户名和密码并且登录的操作
        :param ele_user: 用户名中心位置坐标
        :param ele_pass: 密码中心位置坐标
        :param ele_btn: 登录按钮中心位置坐标
        :param username: 用户名
        :param password: 密码
        :return:
        """
        if self.use_pynput:
            # 检查 系统输出法, 如果不是英文状态的, 切换到英文

            # 使用 pynput 输入用户名和密码进行登录
            self.pynput_input_and_login(
                e_user=ele_user,
                e_pass=ele_pass,
                e_btn=ele_btn,
                username=username,
                password=password,
            )
        else:
            # 使用 selenium 输入用户名和密码进行登录
            self.selenium_input_and_login(
                e_user=ele_user,
                e_pass=ele_pass,
                e_btn=ele_btn,
                username=username,
                password=password,
            )

    def pynput_input_and_login(self, e_user, e_pass, e_btn, username, password):
        """
        使用 pynput 输入用户名和密码, 并点击登录按钮
        :param e_user: 用户名输入框元素
        :param e_pass: 密码输入框元素
        :param e_btn: 登录按钮元素
        :param username: 用户名
        :param password: 密码
        :return:
        """
        username_center = self.get_element_center(e_user)
        # 点击 username 输入框，输入用户名
        Pynput.mouse_click(self.mouse, username_center)
        Pynput.keyboard_input(self.keyboard, username)

        time.sleep(random.uniform(1, 2))

        password_center = self.get_element_center(e_pass)
        # 点击 password 输入框，输入用户名
        Pynput.mouse_click(self.mouse, password_center)
        Pynput.keyboard_input(self.keyboard, password)

        time.sleep(random.uniform(1, 2))

        login_btn_center = self.get_element_center(e_btn)
        # 点击登录按钮
        Pynput.mouse_click(self.mouse, login_btn_center)
        time.sleep(random.uniform(1, 2))

    def selenium_input_and_login(self, e_user, e_pass, e_btn, username, password):
        """
        使用 selenium 输入用户名和密码并点击登录按钮
        :param e_user:
        :param e_pass:
        :param e_btn:
        :param username:
        :param password:
        :return:
        """
        e_user.clear()
        e_user.send_keys(username)
        time.sleep(random.uniform(1, 2))

        e_pass.clear()
        e_pass.send_keys(password)
        time.sleep(random.uniform(1, 2))

        e_btn.click()
        time.sleep(random.uniform(1, 2))

    def drag_slider_btn(self, btn, offset, duration=10, ease_func="ease_out_elastic"):
        """
        拖动 滑动滑动
        :param btn:
        :param offset:
        :param duration:
        :param ease_func:
        :return:
        """
        if self.use_pynput:
            # slide_trace = get_trace(slide_x)
            offsets, tracks = self.get_tracks(offset, duration, ease_func)
            # 必须要在点击之后再获取 slider 的位置
            slider_btn_center = self.get_element_center(btn)
            # mouse_drag(mouse, slider_center, slide_trace)
            Pynput.mouse_drag_by_trace(self.mouse, slider_btn_center, tracks)
        else:
            actions = ActionChains(self.browser)
            actions.drag_and_drop_by_offset(source=btn, xoffset=offset, yoffset=0)
            actions.perform()
            actions.release()
        time.sleep(3)

    def do_login(self):
        """
        执行真正的登录逻辑
        """
        raise NotImplementedError

    def run(self):
        # 关闭所有可能存在的 chrome 和 driver
        self.close_all()
        # 获取手动打开 chrome 的脚本
        self.get_script()
        # 手动打开 chrome
        self.open_chrome_manually()
        # 获取 chrome options
        self.get_options()
        # 连接到已打开的 chrome 中
        self.get_browser()
        # 执行某个网站真正的登录逻辑
        self.do_login()

        if self.use_pynput:
            self.set_keyboard_layout(lan='cn')
