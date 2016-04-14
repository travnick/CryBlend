#------------------------------------------------------------------------------
# Name:        configuration.py
# Purpose:     Stores CryBlend configuration settings
#
# Author:      Mikołaj Milej,
#              Angelo J. Miner, Daniel White, David Marcelis, Duo Oratar,
#              Oscar Martin Garcia, Özkan Afacan
#
# Created:     02/10/2013
# Copyright:   (c) Mikołaj Milej 2013
# Licence:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>


import bpy
from io_export_cryblend.outpipe import cbPrint
from io_export_cryblend.utils import get_filename
import os
import pickle


class __Configuration:
    __CONFIG_PATH = bpy.utils.user_resource('CONFIG',
                                            path='scripts',
                                            create=True)
    __CONFIG_FILENAME = 'cryblend.cfg'
    __CONFIG_FILEPATH = os.path.join(__CONFIG_PATH, __CONFIG_FILENAME)
    __DEFAULT_CONFIGURATION = {'RC_PATH': r'',
                               'TEXTURE_RC_PATH': r'',
                               'GAME_DIR': r''}

    def __init__(self):
        self.__CONFIG = self.__load({})

    @property
    def rc_path(self):
        return self.__CONFIG['RC_PATH']

    @rc_path.setter
    def rc_path(self, value):
        self.__CONFIG['RC_PATH'] = value

    @property
    def texture_rc_path(self):
        if (not self.__CONFIG['TEXTURE_RC_PATH']):
            return self.rc_path

        return self.__CONFIG['TEXTURE_RC_PATH']

    @texture_rc_path.setter
    def texture_rc_path(self, value):
        self.__CONFIG['TEXTURE_RC_PATH'] = value

    @property
    def game_dir(self):
        return self.__CONFIG['GAME_DIR']

    @game_dir.setter
    def game_dir(self, value):
        self.__CONFIG['GAME_DIR'] = value

    def configured(self):
        path = self.__CONFIG['RC_PATH']
        if len(path) > 0 and get_filename(path) == "rc":
            return True

        return False

    def save(self):
        cbPrint("Saving configuration file.", 'debug')

        if os.path.isdir(self.__CONFIG_PATH):
            try:
                with open(self.__CONFIG_FILEPATH, 'wb') as f:
                    pickle.dump(self.__CONFIG, f, -1)
                    cbPrint("Configuration file saved.")

                cbPrint('Saved {}'.format(self.__CONFIG_FILEPATH))

            except:
                cbPrint(
                    "[IO] can not write: {}".format(
                        self.__CONFIG_FILEPATH), 'error')

        else:
            cbPrint("Configuration file path is missing {}".format(
                    self.__CONFIG_PATH),
                    'error')

    def __load(self, current_configuration):
        new_configuration = {}
        new_configuration.update(self.__DEFAULT_CONFIGURATION)
        new_configuration.update(current_configuration)

        if os.path.isfile(self.__CONFIG_FILEPATH):
            try:
                with open(self.__CONFIG_FILEPATH, 'rb') as f:
                    new_configuration.update(pickle.load(f))
                    cbPrint('Configuration file loaded.')
            except:
                cbPrint("[IO] can not read: {}".format(self.__CONFIG_FILEPATH),
                        'error')

        return new_configuration


Configuration = __Configuration()
