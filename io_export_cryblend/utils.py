#------------------------------------------------------------------------------
# Name:        utils
# Purpose:     utility functions to share throughout the addon
#
# Author:      Angelo J. Miner
#
# Created:     23/02/2012
# Copyright:   (c) Angelo J. Miner 2012
# Licence:     GPLv2+
#------------------------------------------------------------------------------


if "bpy" in locals():
    import imp
    imp.reload(exceptions)
else:
    import bpy
    from io_export_cryblend import exceptions


from io_export_cryblend.outPipe import cbPrint
import bpy
import fnmatch
import math
import os
import random
import subprocess
import sys
import xml.dom.minidom


# globals
toD = 180.0 / math.pi


def getcol(r, g, b, a):
    s = " "
    s += " " + str(r)
    s += " " + str(g)
    s += " " + str(b)
    s += " " + str(a)
    s += " "
    return s


def addthreenames(x, y, z):
    s = " "
    s += "" + str(x)
    s += "-" + str(y)
    s += "-" + str(z)
    s = " "
    return s


def addthree(x, y, z):
    s = " "
    s += " " + str(x)
    s += " " + str(y)
    s += " " + str(z)
    s += " "
    return s


def facevcount(fv):
    s = " "
    s += " " + str(len(fv))
    s = " "
    return s


def convert_time(frx):
    fps_base = bpy.context.scene.render.fps_base
    fps = bpy.context.scene.render.fps
    return (fps_base * frx) / fps


# the following func is from
# http://ronrothman.com/
#    public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace/
# modified to use the current ver of shipped python
def fixed_writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
        writer.write(indent + "<" + self.tagName)
        attrs = self._get_attributes()
        for a_name in sorted(attrs.keys()):
            writer.write(" %s=\"" % a_name)
            xml.dom.minidom._write_data(writer, attrs[a_name].value)
            writer.write("\"")
        if self.childNodes:
            if (len(self.childNodes) == 1
                and self.childNodes[0].nodeType
                    == xml.dom.minidom.Node.TEXT_NODE):
                writer.write(">")
                self.childNodes[0].writexml(writer, "", "", "")
                writer.write("</%s>%s" % (self.tagName, newl))
                return
            writer.write(">%s" % (newl))
            for node in self.childNodes:
                node.writexml(writer, indent + addindent, addindent, newl)
            writer.write("%s</%s>%s" % (indent, self.tagName, newl))
        else:
            writer.write("/>%s" % (newl))


def generateGUID():
    GUID = '{'
    GUID += randomSector(8)
    GUID += '-'
    GUID += randomSector(4)
    GUID += '-'
    GUID += randomSector(4)
    GUID += '-'
    GUID += randomSector(4)
    GUID += '-'
    GUID += randomSector(12)
    GUID += '}'
    return GUID


def randomSector(length):
    charOptions = list(range(ord("0"), ord("9") + 1))
    charOptions += list(range(ord("A"), ord("Z") + 1))
    charOptionsLength = len(charOptions)
    sector = ''
    counter = 0
    while counter < length:
        charAsciiCode = charOptions[random.randrange(0, charOptionsLength)]
        sector += chr(charAsciiCode)
        counter += 1
    return sector


# borrowed from obj exporter
# modified by angelo j miner
def veckey3d(v):
    return (round(v.x / 32767.0),
            round(v.y / 32767.0),
            round(v.z / 32767.0))


def veckey3d2(v):
    return (v.x,
            v.y,
            v.z)


def veckey3d21(v):
    return (round(v.x, 6),
            round(v.y, 6),
            round(v.z, 6))


def veckey3d3(vn, fn):
    facenorm = fn
    return (round((facenorm.x * vn.x) / 2),
            round((facenorm.y * vn.y) / 2),
            round((facenorm.z * vn.z) / 2))


def fix_transforms():
    ob = bpy.context.selected_objects
    ob.location.x = (ob.bound_box[0][0] + ob.bound_box[1][0])
    ob.location.x /= 2.0
    ob.location.y = (ob.bound_box[2][0] + ob.bound_box[3][0])
    ob.location.y /= 2.0
    ob.location.z = (ob.bound_box[4][0] + ob.bound_box[5][0])
    ob.location.z /= 2.0


def matrix_to_string(self, matrix):
    result = ""
    for row in matrix:
        for col in row:
            result += "{!s} ".format(col)

    return result.strip()


def get_absolute_path(file_path):
    [is_relative, file_path] = strip_blender_path_prefix(file_path)

    if is_relative:
        blend_file_path = os.path.dirname(bpy.data.filepath)
        file_path = "%s/%s" % (blend_file_path, file_path)

    return os.path.abspath(file_path)


def get_absolute_path_for_rc(file_path):
    # 'z:' is for wine (linux, mac) path
    # there should be better way to determine it
    WINE_DEFAULT_DRIVE_LETTER = "z:"

    file_path = get_absolute_path(file_path)

    if not sys.platform == 'win32':
        file_path = "%s%s" % (WINE_DEFAULT_DRIVE_LETTER, file_path)

    return file_path


def get_relative_path(filepath, start=None):
    blend_file_directory = os.path.dirname(bpy.data.filepath)
    [is_relative_to_blend_file, filepath] = strip_blender_path_prefix(filepath)

    if not start:
        if is_relative_to_blend_file:
            return filepath

        # path is not relative, so create path relative to blend file.
        start = blend_file_directory

        if not start:
            raise exceptions.BlendNotSavedException

    else:
        # make absolute path to be able make relative to 'start'
        if is_relative_to_blend_file:
            filepath = os.path.normpath(os.path.join(blend_file_directory,
                                                     filepath))

    return make_relative_path(filepath, start)


def strip_blender_path_prefix(path):
    is_relative = False
    BLENDER_RELATIVE_PATH_PREFIX = "//"
    prefix_length = len(BLENDER_RELATIVE_PATH_PREFIX)

    if path.startswith(BLENDER_RELATIVE_PATH_PREFIX):
        path = path[prefix_length:]
        is_relative = True

    return (is_relative, path)


def make_relative_path(filepath, start):
    try:
        relative_path = os.path.relpath(filepath, start)
        return relative_path

    except ValueError:
        raise exceptions.TextureAndBlendDiskMismatch(start, filepath)


def get_mtl_files_in_directory(directory):
    MTL_MATCH_STRING = "*.{!s}".format("mtl")

    mtl_files = []
    for file in os.listdir(directory):
        if fnmatch.fnmatch(file, MTL_MATCH_STRING):
            filepath = "{!s}/{!s}".format(directory, file)
            mtl_files.append(filepath)

    return mtl_files


def run_rc(rc_path, files_to_process, params=None):
    cbPrint(rc_path)
    process_params = [rc_path]

    if isinstance(files_to_process, list):
        process_params.extend(files_to_process)
    else:
        process_params.append(files_to_process)

    process_params.extend(params)

    cbPrint(params)
    cbPrint(files_to_process)

    try:
        run_object = subprocess.Popen(process_params)
    except:
        raise exceptions.NoRcSelectedException

    return run_object


def get_path_with_new_extension(image_path, extension):
    return "%s.%s" % (os.path.splitext(image_path)[0], extension)


# this is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
