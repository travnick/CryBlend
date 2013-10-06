#------------------------------------------------------------------------------
# Name:        Configuration
# Purpose:     Converter to DDS
#
# Author:      Mikołaj Milej
#
# Created:     02/10/2013
# Copyright:   (c) Mikołaj Milej 2013
# Licence:     GPLv2+
#------------------------------------------------------------------------------


import bpy
from io_export_cryblend.outPipe import cbPrint
import os
import pickle


CONFIG_PATH = bpy.utils.user_resource('CONFIG', path='scripts', create=True)
CONFIG_FILENAME = 'cryblend.cfg'
CONFIG_FILEPATH = os.path.join(CONFIG_PATH, CONFIG_FILENAME)
_DEFAULT_CONFIGURATION = {'RC_LOCATION': r'',
                          'TEXTURES_DIR': r''}


def load_config(current_configuration):
    new_configuration = {}
    new_configuration.update(_DEFAULT_CONFIGURATION)
    new_configuration.update(current_configuration)

    if os.path.isfile(CONFIG_FILEPATH):
        try:
            with open(CONFIG_FILEPATH, 'rb') as f:
                new_configuration.update(pickle.load(f))
                cbPrint('Configuration file loaded.')
        except:
            cbPrint("[IO] can not read: %s" % CONFIG_FILEPATH, 'error')

    return new_configuration


def save_config():
    cbPrint("Saving configuration file.", 'debug')
    if os.path.isdir(CONFIG_PATH):
        try:
            with open(CONFIG_FILEPATH, 'wb') as f:
                pickle.dump(CONFIG, f, -1)
                cbPrint("Configuration file saved.")
        except:
            cbPrint("[IO] can not write: %s" % CONFIG_FILEPATH, 'error')
    else:
        cbPrint("Configuration file path is missing %s" % CONFIG_PATH, 'error')


CONFIG = load_config({})
