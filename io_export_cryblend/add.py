#------------------------------------------------------------------------------
# Name:        add.py
# Purpose:     Holds functions for adding various UDP properties/helper items
#
# Author:      Angelo J. Miner,
#              Daniel White, David Marcelis, Duo Oratar, Mikołaj Milej,
#              Oscar Martin Garcia, Özkan Afacan
#
# Created:     23/02/2012
# Copyright:   (c) Angelo J. Miner 2012
# License:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>


from bpy.props import *
from bpy_extras.io_utils import ExportHelper
import bpy
import bpy.ops
import bpy_extras
import re
import math


#------------------------------------------------------------------------------
# User Defined Properties:
#------------------------------------------------------------------------------

def get_udp(object_, udp_name, udp_value, is_checked=None):
    '''Get User Defined Property -- Overloaded function that have two variation'''

    if is_checked is None:
        try:
            temp_value = object_[udp_name]
            udp_value = True
        except:
            udp_value = False

        return udp_value

    else:
        try:
            udp_value = object_[udp_name]
            is_checked = True
        except:
            is_checked = False

        return udp_value, is_checked


def edit_udp(object_, udp_name, udp_value, is_checked=True):
    '''Edit User Defined Property'''

    if is_checked:
        object_[udp_name] = udp_value
    else:
        try:
            del object_[udp_name]
        except:
            pass


def is_user_defined_property(property_name):
    prop_list = [
        "phys_proxy",
        "colltype_player",
        "no_explosion_occlusion",
        "entity",
        "mass",
        "density",
        "pieces",
        "dynamic",
        "no_hit_refinement",
        "limit",
        "bend",
        "twist",
        "pull",
        "push",
        "shift",
        "player_can_break",
        "gameplay_critical",
        "constraint_limit",
        "constraint_minang",
        "consrtaint_maxang",
        "constraint_damping",
        "constraint_collides",
        "stiffness",
        "hardness",
        "max_stretch",
        "max_impulse",
        "skin_dist",
        "thickness",
        "explosion_scale",
        "notaprim",
        "wheel"]

    return property_name in prop_list


#------------------------------------------------------------------------------
# Bone Inverse Kinematics:
#------------------------------------------------------------------------------

def get_bone_ik_max_min(pose_bone):
    xIK = yIK = zIK = ""

    if pose_bone.lock_ik_x:
        xIK = '_xmax={!s}'.format(0.0) + '_xmin={!s}'.format(0.0)
    else:
        xIK = '_xmax={!s}'.format(math.degrees(pose_bone.ik_max_x)) \
            + '_xmin={!s}'.format(math.degrees(pose_bone.ik_min_x))

    if pose_bone.lock_ik_y:
        yIK = '_ymax={!s}'.format(0.0) + '_ymin={!s}'.format(0.0)
    else:
        yIK = '_ymax={!s}'.format(math.degrees(pose_bone.ik_max_y)) \
            + '_ymin={!s}'.format(math.degrees(pose_bone.ik_min_y))

    if pose_bone.lock_ik_z:
        zIK = '_zmax={!s}'.format(0.0) + '_zmin={!s}'.format(0.0)
    else:
        zIK = '_zmax={!s}'.format(math.degrees(pose_bone.ik_max_z)) \
            + '_zmin={!s}'.format(math.degrees(pose_bone.ik_min_z))

    return xIK, yIK, zIK


def get_bone_ik_properties(pose_bone):
    damping = [1.0, 1.0, 1.0]
    spring = [0.0, 0.0, 0.0]
    spring_tension = [1.0, 1.0, 1.0]

    try:
        damping = pose_bone['Damping']
    except:
        pass

    try:
        spring = pose_bone['Spring']
    except:
        pass

    try:
        spring_tension = pose_bone['Spring Tension']
    except:
        pass

    return damping, spring, spring_tension


#------------------------------------------------------------------------------
# Jointed Breakable:
#------------------------------------------------------------------------------

def add_joint(self, context):
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    ob.draw_type = "BOUNDS"
    ob.show_x_ray = True
    ob.name = '_jointNUM'
    ob.show_name = True
    ob["rotLimitMin"] = "rotLimitMin=0"
    ob["rotLimitMinX"] = "rotLimitMinX=0"
    ob["rotLimitMinY"] = "rotLimitMinY=0"
    ob["rotLimitMinZ"] = "rotLimitMinZ=0"
    ob["rotLimitMax"] = "rotLimitMax=0"
    ob["rotLimitMaxX"] = "rotLimitMaxX=0"
    ob["rotLimitMaxY"] = "rotLimitMaxY=0"
    ob["rotLimitMaxZ"] = "rotLimitMaxZ=0"
    ob["spring"] = "spring=0"
    ob["springX"] = "springX=0"
    ob["springY"] = "springY=0"
    ob["springZ"] = "springZ=0"
    ob["springTension"] = "springTension=0"
    ob["springTensionX"] = "springTensionX=1"
    ob["springTensionY"] = "springTensionY=1"
    ob["springTensionZ"] = "springTensionZ=1"
    ob["damping"] = "damping=0"
    ob["dampingX"] = "dampingX=1"
    ob["dampingY"] = "dampingY=1"
    ob["dampingZ"] = "dampingZ=1"
    ob["limit"] = "limit=100"

    return {'FINISHED'}


#------------------------------------------------------------------------------
# Material Physics:
#------------------------------------------------------------------------------

def add_phys_material(self, context, physName):
    if not physName.startswith("__"):
        physName = "__" + physName

    me = bpy.context.active_object
    if me.active_material:
        me.active_material.name = replacePhysMaterial(
            me.active_material.name, physName)

    return {'FINISHED'}


def replacePhysMaterial(materialname, phys):
    if "__phys" in materialname:
        return re.sub(r"__phys.*", phys, materialname)
    else:
        return "{}{}".format(materialname, phys)


# This is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
