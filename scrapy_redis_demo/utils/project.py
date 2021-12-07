# -*- coding: utf-8 -*-
# get scrapy project settings
# modified from scrapy.utils.project.get_project_settings
import os
import pickle
import warnings

from scrapy.utils.conf import init_env
from scrapy.settings import Settings
from scrapy.exceptions import ScrapyDeprecationWarning


ENVVAR = 'SCRAPY_SETTINGS_MODULE'
DATADIR_CFG_SECTION = 'datadir'


def get_project_settings(settings_name="default", priority="project"):
    """
    根据 scrapy.cfg 中的 settings_name 获取 项目目录中的 settings.py 中的设置
    :param settings_name: scrapy.cfg 中 [settings] 中的 名称, 如 default
    :param priority:
    :return:
    """
    project = os.environ.get('SCRAPY_PROJECT', settings_name)
    init_env(project)

    settings = Settings()
    settings_module_path = os.environ.get(ENVVAR)
    if settings_module_path:
        settings.setmodule(settings_module_path, priority=priority)

    pickled_settings = os.environ.get("SCRAPY_PICKLED_SETTINGS_TO_OVERRIDE")
    if pickled_settings:
        warnings.warn("Use of environment variable "
                      "'SCRAPY_PICKLED_SETTINGS_TO_OVERRIDE' "
                      "is deprecated.", ScrapyDeprecationWarning)
        settings.setdict(pickle.loads(pickled_settings), priority=priority)

    scrapy_envvars = {k[7:]: v for k, v in os.environ.items() if
                      k.startswith('SCRAPY_')}
    valid_envvars = {
        'CHECK',
        'PICKLED_SETTINGS_TO_OVERRIDE',
        'PROJECT',
        'PYTHON_SHELL',
        'SETTINGS_MODULE',
    }
    setting_envvars = {k for k in scrapy_envvars if k not in valid_envvars}
    if setting_envvars:
        setting_envvar_list = ', '.join(sorted(setting_envvars))
        warnings.warn(
            'Use of environment variables prefixed with SCRAPY_ to override '
            'settings is deprecated. The following environment variables are '
            'currently defined: {}'.format(setting_envvar_list),
            ScrapyDeprecationWarning
        )
    settings.setdict(scrapy_envvars, priority=priority)

    return settings

