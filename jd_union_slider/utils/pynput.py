# -*- coding: utf-8 -*-
# pynput 功能
import random
import time

from pynput.mouse import Button


class Pynput(object):

    @staticmethod
    def mouse_click(mouse, position):
        """
        鼠标移动到某位置点击
        :param mouse:
        :param position:
        :return:
        """
        mouse.position = (position["x"], position["y"])
        time.sleep(0.5)
        mouse.press(Button.left)
        time.sleep(0.5)
        mouse.release(Button.left)
        # 对于京东这样的自动填充密码的, 双击可以选中原用户名和密码, 再输入时就会覆盖原来的值了
        # 对于使用 邮件地址的登录, 需要 3 次点击才能全部选中
        mouse.click(Button.left, 3)

    @staticmethod
    def keyboard_input(keyboard, text: str):
        """
        键盘输入文本
        :param keyboard: pynput 实例化的 keyboard 对象
        :param text:
        :return:
        """
        for i in text:
            time.sleep(random.uniform(0, 1))
            keyboard.press(i)

    @staticmethod
    def mouse_drag(mouse, position: dict, distance: int):
        """
        从某位置拖动鼠标到另一个位置
        :param mouse: pynput 实例化的 mouse 对象
        :param position:
        :param distance:
        :return:
        """
        time.sleep(0.5)
        mouse.position = (position["x"], position["y"])
        time.sleep(0.5)
        mouse.press(Button.left)
        time.sleep(0.5)
        mouse.move(distance, 0)
        time.sleep(0.5)
        mouse.release(Button.left)

    @staticmethod
    def mouse_drag_by_trace(mouse, position: dict, trace: list):
        """
        从某位置拖动鼠标到另一个位置
        :param mouse:
        :param position:
        :param trace:
        :return:
        """
        time.sleep(0.5)
        mouse.position = (position["x"], position["y"])
        time.sleep(0.5)
        mouse.press(Button.left)
        time.sleep(0.5)
        for d in trace:
            mouse.move(d, 0)
            time.sleep(random.random() / 10)
        time.sleep(0.5)
        mouse.release(Button.left)
