# -*- coding: utf-8 -*-
import importlib

from jd_union_slider.jd_union.login import JdLogin


def main():
    settings = importlib.import_module(name='settings', package='jd_union_slider').__dict__
    jd = JdLogin(settings)
    jd.run()


if __name__ == '__main__':
    main()
