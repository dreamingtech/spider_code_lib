# -*- coding: utf-8 -*-
# 京东联盟缺口滑块验证码处理
import re

from jd_union_slider.utils import get_logger
from jd_union_slider.base.base_login import BaseLogin

logger = get_logger(re.split(r"[/.\\]", __file__)[-2])


class JdLogin(BaseLogin):

    def __init__(self, settings, use_pynput=True):
        """
        京东要使用 pynput 登录, 所以 use_pynput 为 True
        """
        super(JdLogin, self).__init__(settings, use_pynput)

        self.USER_JD_UNION = settings['USER_JD_UNION']
        # username 作为实例属性, 方便登录过程中使用
        self.username = '{username}'.format(**self.USER_JD_UNION)

    def get_main(self):
        """
        打开主页
        """
        # 京东联盟 我的推广主页
        url_union = "https://union.jd.com/overview"
        # 打开登录页
        self.browser.get(url_union)

    def check_login_status(self):
        """
        检测是否登录成功
        :return:
        """
        user_name = self.try_wait_do(
            by="xpath",
            ele_sign="//span[@class='back-hover']",
            wait_time=5,
            retry=1,
            action="get_attribute",
            params="textContent",
        )
        if user_name == "{username}".format(**self.USER_JD_UNION):
            return True
        return False

    def check_iframe(self):
        """
        检查是否存在 登录的 iframe
        """
        iframe = self.try_wait_do(
            by="id",
            ele_sign="indexIframe",
            # wait_time=10
        )
        if iframe:
            # 必须要在 switch_to.frame 之前获取 iframe 的属性, 切换到 indexIframe 之后就不能再获取此元素了
            # iframe 是相对于 html 窗口的 (0, 0) 点的
            # {'x': 1204, 'y': 129}
            self.p_iframe_xy = iframe.location

            # self.browser.switch_to.frame("indexIframe")
            self.browser.switch_to.frame(iframe)
            return True

        return False

    def check_captcha(self):
        """
        检测是否出现了滑动验证码
        """
        # style_value = self.browser.find_element_by_id("JDJRV-wrap-paipaiLoginSubmit").get_attribute("style")
        style_value = self.try_wait_do(
            by="id",
            ele_sign="JDJRV-wrap-paipaiLoginSubmit",
            action="get_attribute",
            params="style",
        )

        # 'width: 307px; top: 0px; left: 16.5px; height: 1.94444px; display: block;'
        if "display: block" in style_value:
            return True
        return False

    def get_slide_distance(self):
        """
        获取拖动的距离
        """
        img_big = self.try_wait_do(
            by="xpath",
            ele_sign="//div[@class='JDJRV-bigimg']/img",
            # wait_time=10,
        )

        if not img_big:
            logger.warning('img big not found, check check !')
            return

        # 获取 image 的 src
        img_big_base64 = img_big.get_attribute("src")

        img_slider = self.try_wait_do(
            by="xpath",
            ele_sign="//div[@class='JDJRV-smallimg']/img",
            # wait_time=10,
        )

        if not img_slider:
            logger.warning('img slider not found, check check !')
            return

        img_slider_base64 = img_slider.get_attribute("src")

        # {'height': 39, 'width': 39}
        img_slider_size_html = img_slider.size
        # {'height': 50, 'width': 50}
        img_slider_size_real = self.get_image_size(img_slider_base64)

        # 元素页面大小与实际大小的比例
        ratio = img_slider_size_html["height"] / img_slider_size_real["height"]

        # 验证码识别结果
        # {"data":{"recognition":"196,83","captchaId":"20201019:000000000046647129986"},"message":"","code":0}
        # {"message":"佣工超时未处理","code":9000102}
        captcha_response = self.lianzhong.crack_captcha(image=img_big_base64)

        # 拖动的距离
        slide_x = int(captcha_response.split(",")[0]) * ratio

        return slide_x

    def do_login(self):

        self.get_main()

        if self.check_login_status():
            logger.info("already login, user: {username}".format(**self.USER_JD_UNION))
            return

        logger.info("user: {username} not login, do login".format(**self.USER_JD_UNION))

        if self.use_pynput:
            self.get_top_bar_height()
            logger.info(f"chrome_topbar_height: {self.top_bar_height}")

        logger.info("iframe exists, continue login")

        iframe = self.check_iframe()
        if not iframe:
            logger.warning('iframe not found, check check !')
            return

        username_ele = self.try_wait_do(
            by="id",
            ele_sign="loginname",
            # wait_time=10
        )

        # username 是相对于 iframe 的 (0, 0) 点的
        # username.clear 和 password.clear 必须要放在 mouse 和 keyboard 实例化之前，否则不能成功
        username_ele.clear()

        password_ele = self.try_wait_do(
            by="id",
            ele_sign="nloginpwd",
            # wait_time=10
        )
        password_ele.clear()

        login_btn_ele = self.try_wait_do(
            by="id",
            ele_sign="paipaiLoginSubmit",
            # wait_time=10
        )

        self.input_and_login(
            ele_user=username_ele,
            ele_pass=password_ele,
            ele_btn=login_btn_ele,
            username="{username}".format(**self.USER_JD_UNION),
            password="{password}".format(**self.USER_JD_UNION),
        )

        # 有时候不出现验证码, 直接登录成功
        if self.check_login_status():
            logger.info("login success without captcha")
            return

        # 检测是否出现了验证码
        if not self.check_captcha():
            logger.warning("captcha not found, check check")
            return

        logger.info("captcha found, do recognition.")

        slider_btn = self.try_wait_do(
            by="xpath",
            ele_sign="//div[@class='JDJRV-slide-inner JDJRV-slide-btn']",
            # wait_time=10,
        )

        if not slider_btn:
            logger.warning('slider btn not found, check check !')
            return

        distance = self.get_slide_distance()
        if not distance or not isinstance(distance, float):
            logger.warning('erro get slide distance')
            return

        # 拖动滑块
        self.drag_slider_btn(slider_btn, distance, duration=8, ease_func="ease_out_elastic")
