#------------------------------------------------------------------------------
# Name:        outPipe.py
# Purpose:     Pipeline for console output
#
# Author:      N/A
#
# Created:     N/A
# Copyright:   (c) N/A
# Licence:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>

from io_export_cryblend import exceptions
from logging import basicConfig, info, debug, warning, DEBUG
import bpy
import os


class OutPipe():
    def __init__(self):
        self.out_path = bpy.path.ensure_ext("%s/%s/%s/%s" % (self.get_cry_root_path(), "Objects", self.get_project_path(), "Debug"), ".txt")
        if (not os.path.exists(os.path.dirname(self.out_path))):
            os.makedirs(os.path.dirname(self.out_path))

        if (not os.path.exists(self.out_path)):
            self.out_file = open(self.out_path, "w")
        else:
            self.out_file = open(self.out_path, "a")

    def pump(self, message, message_type='info'):
        if message_type == 'info':
            self.out_file.write("[Info] CryBlend: {!r}\n".format(message))
            print("[Info] CryBlend: {!r}".format(message))

        elif message_type == 'debug':
            self.out_file.write("[Debug] CryBlend: {!r}\n".format(message))
            print("[Debug] CryBlend: {!r}".format(message))

        elif message_type == 'warning':
            self.out_file.write("[Warning] CryBlend: {!r}\n".format(message))
            print("[Warning] CryBlend: {!r}".format(message))

        elif message_type == 'error':
            self.out_file.write("[Error] CryBlend: {!r}\n".format(message))
            print("[Error] CryBlend: {!r}".format(message))

        elif message_type == 'test':
            self.out_file.write("[Test] CryBlend: {!r}\n".format(message))
            print("[Test] CryBlend: {!r}".format(message))

        else:
            raise exceptions.CryBlendException("No such message type {!r}".
                                    format(message_type))


    def get_cry_root_path(self):
        return "C:/Users/Dan/Documents/!!Blender/Programming/CryEngine3.4.5/Game"


    def get_cryblend_root_path(self):
        return os.path.dirname(__file__)


    def get_project_path(self):
        return "!test/char1"

oP = OutPipe()

def cbPrint(msg, message_type='info'):
    oP.pump(msg, message_type)

# this is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
