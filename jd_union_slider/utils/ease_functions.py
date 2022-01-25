# coding=utf-8
# ease 函数, 轨迹缓动函数
# https://github.com/semitable/easing-functions
# https://juejin.im/entry/6844903953595891725
# https://easings.net/cn
# https://github.com/ai/easings.net
# https://pypi.org/project/PyTweening/
# https://gist.github.com/cleure/e5ba94f94e828a3f5466

import math


def ease_out_quad(x):
    return 1 - (1 - x) * (1 - x)


def ease_out_quart(x):
    return 1 - pow(1 - x, 4)


def ease_out_expo(x):
    if x == 1:
        return 1
    else:
        return 1 - pow(2, -10 * x)


def ease_out_back(x):
    c1 = 1.70158
    c3 = c1 + 1

    result = 1 + c3 * pow(x-1, 3) + c1 * pow(x - 1, 2)
    return result


def ease_out_elastic(x):
    c4 = (2 * math.pi) / 3
    if x == 0:
        result = 0
    elif x == 1:
        result = 1
    else:
        result = pow(2, -15 * x) * math.sin((x * 5 - 0.75) * c4) + 1
    return result
