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

import bpy
import math
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
    s = ((bpy.context.scene.render.fps_base * frx)
         / bpy.context.scene.render.fps)
    return s


def fix_transforms():
    ob = bpy.context.selected_objects
    ob.location.x = (ob.bound_box[0][0] + ob.bound_box[1][0])
    ob.location.x /= 2.0
    ob.location.y = (ob.bound_box[2][0] + ob.bound_box[3][0])
    ob.location.y /= 2.0
    ob.location.z = (ob.bound_box[4][0] + ob.bound_box[5][0])
    ob.location.z /= 2.0


# this is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
