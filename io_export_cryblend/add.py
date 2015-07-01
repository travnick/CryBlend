#------------------------------------------------------------------------------
# Name:        add.py
# Purpose:     Holds functions for adding various UDP properties/helper items
#
# Author:      Angelo J. Miner
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
# from add_utils import AddObjectHelper, add_object_data


# jointed breakables
# joint
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


# wheel
def add_wheel_property(self, context):
    ob = bpy.context.active_object
    ob["wheel"] = "wheel"
    # ob["mass"] = "mass=15"
    return{'FINISHED'}


# jointed breakables
# rendermesh
def add_entity_property(self, context):
    ob = bpy.context.active_object
    ob["entity"] = "entity=1"
    return{'FINISHED'}


def add_mass_property(self, context, mass):
    ob = bpy.context.active_object
    ob["mass"] = "mass=%s" % mass
    return{'FINISHED'}


def add_density_property(self, context, density):
    ob = bpy.context.active_object
    ob["density"] = "density=%s" % density
    return{'FINISHED'}


def add_pieces_property(self, context, pieces):
    ob = bpy.context.active_object
    ob["pieces"] = "pieces=%s" % pieces
    return{'FINISHED'}


def add_no_hit_refinement_property(self, context):
    ob = bpy.context.active_object
    ob["no_hit_refinement"] = "no_hit_refinement=1"
    return{'FINISHED'}


def add_dynamic_property(self, context):
    ob = bpy.context.active_object
    ob["dynamic"] = "dynamic=1"
    return{'FINISHED'}


# joint
def add__gameplay_critical_property(self, context):
    ob = bpy.context.active_object
    ob["gameplay_critical"] = "gameplay_critical=1"
    return{'FINISHED'}


def add_player_can_break_property(self, context):
    ob = bpy.context.active_object
    ob["player_can_break"] = "player_can_break=1"
    return{'FINISHED'}


def add_bend_property(self, context, bendValue):
    ob = bpy.context.active_object
    ob["bend"] = "bend=%s" % bendValue
    return{'FINISHED'}


def add_twist_property(self, context, twistValue):
    ob = bpy.context.active_object
    ob["twist"] = "twist=%s" % twistValue
    return{'FINISHED'}


def add_pull_property(self, context, pullValue):
    ob = bpy.context.active_object
    ob["pull"] = "pull=%s" % pullValue
    return{'FINISHED'}


def add_push_property(self, context, pushValue):
    ob = bpy.context.active_object
    ob["push"] = "push=%s" % pushValue
    return{'FINISHED'}


def add_shift_property(self, context, shiftValue):
    ob = bpy.context.active_object
    ob["shift"] = "shift=%s" % shiftValue
    return{'FINISHED'}


def add_limit_constraint(self, context, limit):
    ob = bpy.context.active_object
    ob["constraint_limit"] = "constraint_limit=%s" % limit
    return{'FINISHED'}


def add_min_angle_constraint(self, context, minAngle):
    ob = bpy.context.active_object
    ob["constraint_minang"] = "constraint_minang=%s" % minAngle
    return{'FINISHED'}


def add_max_angle_constraint(self, context, maxAngle):
    ob = bpy.context.active_object
    ob["consrtaint_maxang"] = "consrtaint_maxang=%s" % maxAngle
    return{'FINISHED'}


def add_damping_constraint(self, context):
    ob = bpy.context.active_object
    ob["constraint_damping"] = "constraint_damping=1"
    return{'FINISHED'}


def add_collision_constraint(self, context):
    ob = bpy.context.active_object
    ob["constraint_collides"] = "constraint_collides=1"
    return{'FINISHED'}


# deformable
def add_deformable_property(self, context, mass, stiffness, hardness,
        max_stretch, max_impulse, skin_dist, thickness, explosion_scale, is_primitive):
        ob = bpy.context.active_object
        ob["mass"] = "mass=%s" % mass
        ob["stfns"] = "stiffness=%s" % stiffness
        ob["stfns"] = "hardness=%s" % hardness
        ob["mxstr"] = "max_stretch=%s" % max_stretch
        ob["mxstr"] = "max_impulse=%s" % max_impulse
        ob["skdist"] = "skin_dist=%s" % skin_dist
        ob["thkns"] = "thickness=%s" % thickness
        ob["thkns"] = "explosion_scale=%s" % explosion_scale
        if (is_primitive == "Yes"):
            ob["notap"] = "notaprim=0"
        else:
            ob["notap"] = "notaprim=1"
        return{'FINISHED'}


# material physics
def add_phys_material(self, context, physName):
    if not physName.startswith("__"):
        physName = "__" + physName

    me = bpy.context.active_object
    if me.active_material:
        me.active_material.name = replacePhysMaterial(me.active_material.name, physName)

    return {'FINISHED'}


def replacePhysMaterial(materialname, phys):
    if "__phys" in materialname:
        return re.sub(r"__phys.*", phys, materialname)
    else:
        return "{}{}".format(materialname, phys)


# CGF/CGA/CHR
def add_no_explosion_occlusion_property(self, context):
    ob = bpy.context.active_object
    ob["no_explosion_occlusion"] = "no_explosion_occlusion=1"
    return{'FINISHED'}


def add_rendermesh_property(self, context):
    ob = bpy.context.active_object
    ob["other_rendermesh"] = "other_rendermesh=1"
    return{'FINISHED'}


def add_colltype_player_property(self, context):
    ob = bpy.context.active_object
    ob["colltype_player"] = "colltype_player=1"
    return{'FINISHED'}


# proxies
def add_box_proxy_property(self, context):
    ob = bpy.context.active_object
    ob["box"] = "box=1"
    return{'FINISHED'}


def add_cylinder_proxy_property(self, context):
    ob = bpy.context.active_object
    ob["cylinder"] = "cylinder=1"
    return{'FINISHED'}


def add_capsule_proxy_property(self, context):
    ob = bpy.context.active_object
    ob["capsule"] = "capsule=1"
    return{'FINISHED'}


def add_sphere_proxy_property(self, context):
    ob = bpy.context.active_object
    ob["sphere"] = "sphere=1"
    return{'FINISHED'}


def add_notaprim_proxy_property(self, context):
    ob = bpy.context.active_object
    ob["notaprim"] = "notaprim=1"
    return{'FINISHED'}


# this is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
