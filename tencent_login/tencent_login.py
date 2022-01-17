# -*- coding: utf-8 -*-
# https://ad.qq.com 登录逻辑
import random
import re
import time
import logging

import requests
import scrapy
import execjs
from requests.utils import dict_from_cookiejar


class TencentLogin(object):

    def __init__(self, user_info, *args, **kwargs):
        # 用户信息
        self.user_info = user_info
        # 腾讯登录时产生的临时参数
        # 把所有临时参数都保存到一个字典中, 方便格式化字符串时使用
        self.params = {}

        # 临时变量
        self.r_ssl_check_data = []

        # 保存出错信息, 方便发送邮件和重试时使用
        self.fail_mapping = {}

        self.session = requests.session()

        self.logger = self.get_logger(re.split(r"[/.\\]", __file__)[-2])

    @staticmethod
    def get_logger(log_name):

        logger = logging.getLogger(log_name)
        logger.setLevel(logging.INFO)
        s_handler = logging.StreamHandler()
        s_handler.setLevel(logging.INFO)
        s_handler_formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)-7s [%(name)s:%(lineno)3d]: %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        s_handler.setFormatter(s_handler_formatter)
        logger.addHandler(s_handler)
        return logger

    @staticmethod
    def _js_get_token(p_skey):
        """
        https://imgcache.qq.com/c/=/open/connect/widget/pc/login/pt_adapt.js,qlogin_v2.js?v=20181229
        :param p_skey:
        :return:
        """
        js_tk = '''
            function getToken(pKey) {
              // var str = Q.getCookie('p_skey') || ''
              var hash = 5381;
              for (var i = 0, len = pKey.length; i < len; ++i) {
                hash += (hash << 5) + pKey.charCodeAt(i);
              }
              return hash & 0x7fffffff;
            }
        '''
        ctx = execjs.compile(js_tk)
        token = ctx.call('getToken', p_skey)
        return token

    @staticmethod
    def _js_get_uuid():
        """
        https://imgcache.qq.com/c/=/open/connect/widget/pc/login/pt_adapt.js,qlogin_v2.js?v=20181229
        var getUuid = (function() {
        :return:
        """
        js_uuid = """
            function getUuid() {
              var uid = "";
              return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
                var r = Math.random() * 16 | 0
                  , v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
              }).toUpperCase();
            }
        """
        ctx = execjs.compile(js_uuid)
        uuid = ctx.call('getUuid')
        return uuid

    def _js_get_ticket_tk(self):
        """
        https://i.gtimg.cn/qzone/biz/gdt/adp_account_fe/tap/pages/index.c3d56b092aa2e77f56d9.js?max_age=31536000:formatted
        g_tk: ajax_getACSRFToken()
        :return:
        """
        tk_js = """
            function getToken (X) {
                // for (var H = 5381, W = X.get("gdt_protect") || X.get("skey"), V = 0, q = W.length; V < q; ++V)
                for (var H = 5381, W = X["gdt_protect"] || X["skey"], V = 0, q = W.length; V < q; ++V)
                    H += (H << 5) + W.charCodeAt(V);
                return 2147483647 & H
            }
        """
        ctx = execjs.compile(tk_js)
        tk = ctx.call('getToken', dict_from_cookiejar(self.session.cookies))
        return tk

    @staticmethod
    def _js_get_uuid_lower():
        """
        https://i.gtimg.cn/qzone/biz/gdt/adp_account_fe/tap/pages/index.c3d56b092aa2e77f56d9.js?max_age=31536000:formatted
        搜索 g_trans_id 或 trace_id
        :return:
        """
        js_uuuid = '''
            function getUuid () {
                function s4() {
                    return Math.floor(65536 * (1 + Math.random())).toString(16).substring(1)
                }
                return "".concat(s4() + s4(), "-").concat(s4(), "-").concat(s4(), "-").concat(s4(), "-").concat(s4()).concat(s4()).concat(s4())
            }
        '''
        ctx = execjs.compile(js_uuuid)
        uuuid = ctx.call('getUuid')
        return uuuid

    def get_main(self):
        """
        代码登录, 打开主页
        :return:
        """
        self.logger.info('get_main')
        u_main = 'https://ad.qq.com/'

        h_main = {
            'Host': 'ad.qq.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        requests.get(url=u_main, headers=h_main)

    def sso_login(self):
        self.logger.info('sso_login')

        u_sso_login = 'https://sso.e.qq.com/login/hub?sso_redirect_uri=https%3A%2F%2Fad.qq.com%2F&service_tag=10'

        h_sso_login = {
            'Host': 'sso.e.qq.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://ad.qq.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        r_sso_login = self.session.get(
            url=u_sso_login,
            headers=h_sso_login
        )
        r_sso_login_s = scrapy.http.TextResponse(
            url=r_sso_login.url,
            headers=r_sso_login.headers,
            body=r_sso_login.content,
            status=r_sso_login.status_code,
        )

        # 获取此 id
        client_id = r_sso_login_s.xpath('//input[@id="qqAppid"]/@value').extract_first()
        self.params.update(dict(client_id=client_id))

    def get_graph(self):
        self.logger.info('get_graph')

        u_graph = 'https://graph.qq.com/oauth2.0/show'
        p_graph = {
            'which': 'Login',
            'display': 'pc',
            'response_type': 'code',
            'client_id': self.params['client_id'],
            'redirect_uri': 'https://sso.e.qq.com/login/callback',
            'scope': 'get_user_info',
        }

        h_graph = {
            'Host': 'graph.qq.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://sso.e.qq.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        r_graph = self.session.get(
            url=u_graph,
            headers=h_graph,
            params=p_graph,
        )
        r_graph_s = scrapy.http.TextResponse(
            url=r_graph.url,
            headers=r_graph.headers,
            body=r_graph.content,
            status=r_graph.status_code,
        )

        open_api = r_graph_s.xpath('//input[@name="api_choose"]/@value').extract_first()
        # openapi = re.search(r'value="([^"]*?)"', r_graph.content.decode("utf-8")).group(1)
        s_url_define = re.search(r"var s_url = '([^']*?)'", r_graph.content.decode("utf-8")).group(1)
        s_url_origin = re.search(r";\s+s_url = '([^']*?)'", r_graph.content.decode("utf-8")).group(1)
        u_feed_back = re.search(r"var feed_back_link = '([^']*?)'", r_graph.content.decode("utf-8")).group(1)

        self.params.update(dict(
            open_api=open_api,
            s_url_define=s_url_define,
            s_url_origin=s_url_origin,
            u_feed_back=u_feed_back,
        ))

    def get_xui_ptlogin2(self):
        self.logger.info('get_xui_ptlogin2')

        u_x_login = '{s_url_origin}{s_url_define}&pt_3rd_aid={client_id}&pt_feedback_link={u_feed_back}.appid{client_id}'.format(**self.params)

        h_x_login = {
            'Host': 'xui.ptlogin2.qq.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://graph.qq.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        r_x_login = self.session.get(
            url=u_x_login,
            headers=h_x_login,
        )
        r_x_login_s = scrapy.http.TextResponse(
            url=r_x_login.url,
            headers=r_x_login.headers,
            body=r_x_login.content,
            status=r_x_login.status_code,
        )

        pt_feedback_link = r_x_login_s.xpath('//a[@id="feedback_web"]/@href').extract_first()
        ptui_version = re.search(r'ptui_version:\s*encodeURIComponent\("(\d+)"\)', r_x_login.content.decode("utf-8"), flags=re.S).group(1)
        pt_3rd_aid = re.search(r'pt_3rd_aid:\s*encodeURIComponent\("(\d+)"\)', r_x_login.content.decode("utf-8"), flags=re.S).group(1)
        appid = re.search(r'appid:\s*encodeURIComponent\("(\d+)"\)', r_x_login.content.decode("utf-8"), flags=re.S).group(1)
        lang = re.search(r'lang:\s*encodeURIComponent\("(\d+)"\)', r_x_login.content.decode("utf-8"), flags=re.S).group(1)
        style = re.search(r'style:\s*encodeURIComponent\("(\d+)"\)', r_x_login.content.decode("utf-8"), flags=re.S).group(1)
        daid = re.search(r'daid:\s*encodeURIComponent\("(\d+)"\)', r_x_login.content.decode("utf-8"), flags=re.S).group(1)

        self.params.update(dict(
            pt_feedback_link=pt_feedback_link,
            ptui_version=ptui_version,
            pt_3rd_aid=pt_3rd_aid,
            appid=appid,
            lang=lang,
            style=style,
            daid=daid,
            # 因为下一步要使用这个值, 把它也从 cookie 中取出来
            pt_login_sig=dict_from_cookiejar(self.session.cookies).get('pt_login_sig'),
        ))

    def ssl_ptlogin2_check(self):
        self.logger.info('ssl_ptlogin2_check')

        u_ssl_check = 'https://ssl.ptlogin2.qq.com/check'
        h_ssl_check = {
            'Host': 'ssl.ptlogin2.qq.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://xui.ptlogin2.qq.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        p_ssl_check = {
            'regmaster': '',
            'pt_tea': '2',
            'pt_vcode': '1',
            'uin': '{username}'.format(**self.user_info),
            'appid': '{appid}'.format(**self.params),
            'js_ver': '{ptui_version}'.format(**self.params),
            'js_type': '1',
            'login_sig': '{pt_login_sig}'.format(**self.params),
            'u1': '{s_url_define}'.format(**self.params),
            # 'r': '0.5314159269446745',
            'r': random.random(),
            # 'pt_uistyle': '40',
            'pt_uistyle': '{style}'.format(**self.params),
        }
        r_ssl_check = self.session.get(
            url=u_ssl_check,
            headers=h_ssl_check,
            params=p_ssl_check,
        )

        self.r_ssl_check_data = re.findall(r"'([^']*?)'", r_ssl_check.content.decode("utf-8"), flags=re.S)
        if not self.r_ssl_check_data or not isinstance(self.r_ssl_check_data, list):
            self.fail_mapping[2] = 'unknown ssl_check_response'

        if self.r_ssl_check_data[0] != '0':
            self.fail_mapping[2] = 'unknown ssl_check_response'

    def ssl_ptlogin2_login(self):
        self.logger.info('ssl_ptlogin2_login')

        u_ssl_login = 'https://ssl.ptlogin2.qq.com/login'
        h_ssl_login = {
            'Host': 'ssl.ptlogin2.qq.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://xui.ptlogin2.qq.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        with open('./tencent.js', 'r', encoding='utf-8') as j:
            js = j.read()

        ctx = execjs.compile(js)
        p = ctx.call(
            'encryptPassword',
            '{username}'.format(**self.user_info),
            '{password}'.format(**self.user_info),
            self.r_ssl_check_data[1],
        )

        p_ssl_login = {
            'u': '{username}'.format(**self.user_info),
            # 'verifycode': '!RLE',
            'verifycode': self.r_ssl_check_data[1],
            # 'pt_vcode_v1': '0',
            'pt_vcode_v1': self.r_ssl_check_data[0],
            'pt_verifysession_v1': self.r_ssl_check_data[3],
            # 搜索 pt_verifysession_v1, 即可以找到 p 的加密代码
            # o.p = r["default"].getEncryption(e, T.salt, o.verifycode, T.armSafeEdit.isSafe),
            'p': p,
            # 'pt_randsalt': '2',
            'pt_randsalt': self.r_ssl_check_data[4],
            # 'u1': 'https%3A%2F%2Fgraph.qq.com%2Foauth2.0%2Flogin_jump',
            'u1': '{s_url_define}'.format(**self.params),
            'ptredirect': '0',
            'h': '1',
            't': '1',
            'g': '1',
            'from_ui': '1',
            # 'ptlang': '2052',
            'ptlang': '{lang}'.format(**self.params),
            # https://qq-web.cdn-go.cn/any.ptlogin2.qq.com/v1.2.0/ptlogin/js/c_login_2.js
            # o.action = T.action.join("-") + "-" + +new Date
            # 'action': '3-4-1626085421616',
            'action': f'3-4-{int(time.time() * 1000)}',
            # 'js_ver': '21062514',
            'js_ver': '{ptui_version}'.format(**self.params),
            'js_type': '1',
            'login_sig': '{pt_login_sig}'.format(**self.params),
            # 'pt_uistyle': '40',
            'pt_uistyle': '{style}'.format(**self.params),
            'aid': '{appid}'.format(**self.params),
            # 'daid': '383',
            'daid': '{daid}'.format(**self.params),
            'pt_3rd_aid': '{pt_3rd_aid}'.format(**self.params),
            'ptdrvs': self.r_ssl_check_data[5],
            'sid': self.r_ssl_check_data[6],
        }

        r_ssl_login = self.session.get(
            url=u_ssl_login,
            headers=h_ssl_login,
            params=p_ssl_login,
        )

        if '登录成功' not in r_ssl_login.content.decode('utf-8'):
            self.logger.warning('login fail')
            self.fail_mapping[3] = 'login_fail'
            return

        r_ssl_login_data = re.findall(r"'([^']*?)'", r_ssl_login.content.decode("utf-8"), flags=re.S)

        self.params.update(dict(
            u_ssl_graph=r_ssl_login_data[2]
        ))

    def ptlogin2_check_sig(self):
        self.logger.info('ptlogin2_check_sig')

        h_ssl_graph = {
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://xui.ptlogin2.qq.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        # 这一步会设置很多 cookies
        self.session.get(
            url='{u_ssl_graph}'.format(**self.params),
            headers=h_ssl_graph,
        )
        # 下一步要使用 p_skey, 这里也计算出来放在 self.params 中
        self.params.update(dict(
            p_skey=self._js_get_token(p_skey=dict_from_cookiejar(self.session.cookies).get('p_skey', ''))
        ))

    def graph_authorize(self):

        self.logger.info('graph_authorize')

        u_auth = 'https://graph.qq.com/oauth2.0/authorize'
        h_auth = {
            'Origin': 'https://graph.qq.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://graph.qq.com/oauth2.0/show?which=Login&display=pc&response_type=code&client_id=101477621&redirect_uri=https%3A%2F%2Fsso.e.qq.com%2Flogin%2Fcallback&scope=get_user_info',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        # https://imgcache.qq.com/c/=/open/connect/widget/pc/login/pt_adapt.js,qlogin_v2.js?v=20181229
        d_auth = {
            'response_type': 'code',
            'client_id': '{client_id}'.format(**self.params),
            # 'redirect_uri': 'https%3A%2F%2Fsso.e.qq.com%2Flogin%2Fcallback',
            'redirect_uri': 'https://sso.e.qq.com/login/callback',
            'scope': 'get_user_info',
            'state': '',
            'switch': '',
            'from_ptlogin': '1',
            'src': '1',
            'update_auth': '1',
            'openapi': '{open_api}'.format(**self.params),
            'g_tk': '{p_skey}'.format(**self.params),
            # 'auth_time': '1626227985312',
            'auth_time': str(int(time.time() * 1000)),
            'ui': self._js_get_uuid(),
        }
        r_auth = self.session.post(
            url=u_auth,
            headers=h_auth,
            data=d_auth,
        )

        # 'https://graph.qq.com/oauth2.0/show?which=error&display=pc&error=100046&auth_time=1642209414066&'
        if 'code=' not in r_auth.url:
            self.logger.warning(f'error graph_authorize. resp url: {r_auth.url}')
            return

        self.params.update(dict(
            code=r_auth.url.split('code=')[-1]
        ))

    def send_code(self):
        self.logger.info('send_code')

        u_send_code = 'https://sso.e.qq.com/login/send_code'
        h_send_code = {
            'Host': 'sso.e.qq.com',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json; charset=UTF-8',
            'Origin': 'https://sso.e.qq.com',
            'Referer': 'https://sso.e.qq.com/login/hub?sso_redirect_uri=https%3A%2F%2Fadnet.qq.com%2Feros%2Flogin%2Fcall_back%3Fredirect%3Dhttps%253A%252F%252Fadnet.qq.com%252F&service_tag=14',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        j_send_code = {
            'code': '{code}'.format(**self.params),
            'login_type': 1,
            'sso_redirect_uri': 'https://ad.qq.com/',
            'account_id': '',
            'service_tag': '10',
            'reg_uri': '',
            'redirect_target': ''
        }
        r_send_code = self.session.post(
            url=u_send_code,
            headers=h_send_code,
            json=j_send_code,
        )

        if r_send_code.json().get('code') != 0:
            self.logger.warning(f'error send code. resp: {r_send_code.text}')
            return

        # https://sso.e.qq.com/login/portal?service_tag=10&sso_redirect_uri=https%3A%2F%2Fad.qq.com%2F
        u_login_portal = r_send_code.json().get('data', {}).get('redirectUrl')
        self.params.update(dict(
            u_login_portal=u_login_portal
        ))

    def login_portal(self):
        self.logger.info('login_portal')

        h_login_portal = {
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://sso.e.qq.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        r_login_portal = self.session.get(
            url='{u_login_portal}'.format(**self.params),
            headers=h_login_portal,
        )
        # 中间会经历一次跳转
        # Location: https://ad.qq.com/worktable/?source_uri=https%3A%2F%2Fad.qq.com%2F&sso_ticket=ST-70641-Dsdsy9EmmscQx1YQYdsdsIutXL5BCnnrsdoYoddSxA915Sdeh0t7uAah4

        if 'ad.qq.com/worktable' not in r_login_portal.url or 'sso_ticket=' not in r_login_portal.url:
            self.logger.warning('sso_ticket redirect error')
            return

        self.params.update(dict(
            r_login_portal_url=r_login_portal.url,
            ticket=r_login_portal.url.split('sso_ticket=')[-1],
        ))

    def check_ticket(self):
        self.logger.info('check_ticket')

        u_check_ticket = 'https://ad.qq.com/tap/v1/login/check_ticket'

        h_check_ticket = {
            'Host': 'ad.qq.com',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json; charset=UTF-8',
            'Origin': 'https://ad.qq.com',
            'Referer': '{r_login_portal_url}'.format(**self.params),
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        p_check_ticket = {
            'g_tk': self._js_get_ticket_tk(),
            'trace_id': self._js_get_uuid_lower(),
            'g_trans_id': self._js_get_uuid_lower(),
            'unicode': '1',
        }
        j_check_ticket = {
            "ticket": '{ticket}'.format(**self.params)
        }

        r_check_ticket = self.session.post(
            url=u_check_ticket,
            headers=h_check_ticket,
            params=p_check_ticket,
            json=j_check_ticket,
        )
        # '{"code":4401,"message":"处理异常"}'
        if r_check_ticket.json().get('code') != 0 or r_check_ticket.json().get('message') != 'OK':
            self.logger.warning(f'check ticket error. resp: {r_check_ticket.text}')

    def get_login_info(self):
        self.logger.info('get_login_info')

        u_login_info = 'https://ad.qq.com/tap/v1/login/login_info'
        h_login_info = {
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json; charset=UTF-8',
            'Origin': 'https://ad.qq.com',
            'Referer': 'https://ad.qq.com/worktable/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        p_login_info = {
            'g_tk': self._js_get_ticket_tk(),
            'trace_id': self._js_get_uuid_lower(),
            'g_trans_id': self._js_get_uuid_lower(),
            'unicode': '1',
        }
        r_login_info = self.session.post(
            url=u_login_info,
            headers=h_login_info,
            params=p_login_info,
            json={},
        )
        if r_login_info.json().get('code') != 0 or r_login_info.json().get('data', {}).get('qq_number') != '{username}'.format(**self.user_info):
            self.logger.warning(f'error get login_info. resp: {r_login_info.text}')
            return

        user_id = r_login_info.json().get('data', {}).get('user_id')
        self.user_info.update(dict(
            user_id=user_id
        ))
        self.logger.info(f'login user info: [{r_login_info.text}]')

    def do_login(self):
        """
        使用代码登录
        :return:
        """
        self.get_main()
        time.sleep(0.5)
        self.sso_login()
        time.sleep(0.5)
        self.get_graph()
        time.sleep(0.5)
        self.get_xui_ptlogin2()
        time.sleep(0.5)
        self.ssl_ptlogin2_check()
        time.sleep(0.5)
        self.ssl_ptlogin2_login()
        time.sleep(0.5)
        self.ptlogin2_check_sig()
        time.sleep(0.5)
        self.graph_authorize()
        time.sleep(0.5)
        self.send_code()
        time.sleep(0.5)
        self.login_portal()
        time.sleep(0.5)
        self.check_ticket()
        time.sleep(0.5)
        self.get_login_info()


def main():
    user_info = {
        # username 为纯数字 qq 号
        'username': '88888888',
        'password': 'password',
    }
    TencentLogin(user_info=user_info).do_login()


if __name__ == '__main__':
    main()
