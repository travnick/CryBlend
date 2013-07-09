#-------------------------------------------------------------------------------
# Name:        exceptions.py
# Purpose:     holds custom exception classes
#
# Author:      Mikołaj Milej
#
# Created:     23/06/2013
# Copyright:   (c) Mikołaj Milej 2013
# License:     GPLv2+
#-------------------------------------------------------------------------------

# <pep8-80 compliant>

class CryBlendException(RuntimeError):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return what()

    def what(self):
        return self._message


class BlendNotSavedException(CryBlendException):
    def __init__(self):
        message = "Blend file has to be saved before exporting."

        CryBlendException.__init__(self, message)


class TextureAndBlendDiskMismatch(CryBlendException):
    def __init__(self, blend_path, texture_path):
        message = """ 
Blend file and all textures have to be placed on the same disk.
It's impossible to create relative paths if they are not.
Blend file: {!r}
Texture file: {!r}""".format(blend_path, texture_path)

        CryBlendException.__init__(self, message)


class NoRcSelectedException(CryBlendException):
    def __init__(self):
        message = "Please find Resource Compiler first."

        CryBlendException.__init__(self, message)
