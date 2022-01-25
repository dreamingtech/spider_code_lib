# -*- coding: utf-8 -*-
# 联众验证码识别服务 api
import re
from io import BytesIO

import requests

from jd_union_slider.utils import get_logger

logger = get_logger(re.split(r"[/.\\]", __file__)[-2])


class LianZhong(object):

    def __init__(self, user: dict, **kwargs):
        self.user = user

    def crack_captcha(self, image, captcha_type=1318):
        """
        调用联众接口识别图片
        :param image:
        :param captcha_type:
        :return:
        """
        if isinstance(image, bytes):
            logger.info("bytes image, use v1 to crack captcha")
            crack_result = self.crack_captcha_v1(image, captcha_type)
        elif isinstance(image, str) and image.startswith("data:image/"):
            logger.info("base64 image, use v2 to crack captcha")
            crack_result = self.crack_captcha_v2(image, captcha_type)
        else:
            logger.warning("unsupported image type: {}".format(type(image)))
            raise Exception(f"unsupported image type for lianzhong: {type(image)}")

        return crack_result

    def crack_captcha_v1(self, img_content, captcha_type=1318):
        """
        通过传入 image bytes content 来识别验证码
        只需要使用 BytesIO 处理成可读对象, 再使用 lianzhong v1 识别即可
        BytesIO(img_content)
        也可以进一步包装成 BufferedReader 对象
        BufferedReader(BytesIO(img_content))
        参考:
        各种转码 bytes、string、base64、numpy array、io、BufferedReader
        https://www.cnblogs.com/zhuminghui/p/11359858.html
        https://requests.readthedocs.io/zh_CN/latest/user/quickstart.html#post-multipart-encoded
        :param img_content:
        :param captcha_type:
        :return:
        """
        url = "http://v1-http-api.jsdama.com/api.php?mod=php&act=upload"

        # files = {'upload': ("img_2162.png", open("img_2162.png", 'rb'), 'image/png')}
        # files = {'upload': open('img_2162.png', 'rb')}
        files = {'upload': BytesIO(img_content)}
        data = {
            "user_name": '{username}'.format(**self.user),
            "user_pw": '{password}'.format(**self.user),
            "yzmtype_mark": captcha_type,
            # "yzm_minlen": 0,
            # "yzm_maxlen": 0,
            # "zztool_token": None,
        }

        headers = {
            "Host": "v1-http-api.jsdama.com",
            # "Connection": "keep-alive",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0",
            # 'Upgrade-Insecure-Requests': '1'
        }

        # {"result":true,"data":{"id":46822023143,"val":"514,52"}}
        # {"data":{"val":"506,56","id":46827711525},"result":true}
        # {"result":false,"data":"请联系软件作者升级软件，接口zztool_token参数需传入正确的软件token。将于2021年1月1日强制要求传递 zztool_token。"}
        response = requests.post(url=url, headers=headers, data=data, files=files, verify=False)
        logger.info(f'v1 check resp: {response.content.decode("utf-8")}')
        return response.json().get('data', {}).get('val')

    def crack_captcha_v2(self, img_base64, captcha_type=1318):
        """
        联众验证码识别 v2, 通过传入 image 的 base64 字符串进行验证码识别
        :param img_base64:
        :param captcha_type:
        :return:
        """
        url = "https://v2-api.jsdama.com/upload"

        # 切出来 img_base64 的数据部分
        # data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAWgAAA
        img_base64 = img_base64.split(',', maxsplit=1)[-1]

        data = {
            "softwareId": "{software_id}".format(**self.user),
            "softwareSecret": "{secret}".format(**self.user),
            "username": "{username}".format(**self.user),
            "password": "{password}".format(**self.user),
            "captchaData": img_base64,
            "captchaType": captcha_type,
            "captchaMinLength": 0,
            "captchaMaxLength": 0,
            "workerTipsId": 0
        }
        headers = {
            "Host": "v2-api.jsdama.com",
            # "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0",
            "Content-Type": "text/json",
        }

        # {"data":{"recognition":"196,83","captchaId":"20201019:000000000046647129986"},"message":"","code":0}
        response = requests.post(url=url, headers=headers, json=data)
        logger.info(f'v2 check resp: {response.content.decode("utf-8")}')

        return response.json().get("data", {}).get("recognition")
