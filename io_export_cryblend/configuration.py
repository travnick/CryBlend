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
                               'TEXTURE_DIR': r'',
                               'SCRIPT_EDITOR': r''}

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
    def texture_dir(self):
        return self.__CONFIG['TEXTURE_DIR']

    @texture_dir.setter
    def texture_dir(self, value):
        self.__CONFIG['TEXTURE_DIR'] = value

    @property
    def script_editor(self):
        return self.__CONFIG['SCRIPT_EDITOR']

    @script_editor.setter
    def script_editor(self, value):
        self.__CONFIG['SCRIPT_EDITOR'] = value

    def save(self):
        cbPrint("Saving configuration file.", 'debug')

        if os.path.isdir(self.__CONFIG_PATH):
            try:
                with open(self.__CONFIG_FILEPATH, 'wb') as f:
                    pickle.dump(self.__CONFIG, f, -1)
                    cbPrint("Configuration file saved.")

                cbPrint('Saved %s' % self.__CONFIG_FILEPATH)

            except:
                cbPrint("[IO] can not write: %s" % self.__CONFIG_FILEPATH,
                        'error')

        else:
            cbPrint("Configuration file path is missing %s"
                    % self.__CONFIG_PATH,
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
                cbPrint("[IO] can not read: %s" % self.__CONFIG_FILEPATH,
                        'error')

        return new_configuration


Configuration = __Configuration()
