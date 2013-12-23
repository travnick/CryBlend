#------------------------------------------------------------------------------
# Name:        add.py
# Purpose:     this holds the add whatever _joint , exportnode....
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
# from add_utils import AddObjectHelper, add_object_data


# animnode for animation name and frame range slection
def add_animnode(self, context):
    bpy.ops.object.add(type='EMPTY')
    anode = bpy.context.active_object
    anode.name = 'animnode'
    anode["animname"] = "door open"
    anode["startframe"] = 1
    anode["endframe"] = 1


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


def add_j_gpc_p(self, context):
    ob = bpy.context.active_object
    ob["gameplay_critical"] = "gameplay_critical=1"
    return{'FINISHED'}


def add_j_pcb_p(self, context):
    ob = bpy.context.active_object
    ob["player_can_break"] = "player_can_break"
    return{'FINISHED'}


def add_j_b_p(self, context):
    ob = bpy.context.active_object
    ob["bend"] = "bend=value"
    return{'FINISHED'}


def add_j_t_p(self, context):
    ob = bpy.context.active_object
    ob["twist"] = "twist=value"
    return{'FINISHED'}


def add_j_pull_p(self, context):
    ob = bpy.context.active_object
    ob["pull"] = "pull=value"
    return{'FINISHED'}


def add_j_push_p(self, context):
    ob = bpy.context.active_object
    ob["push"] = "push=value"
    return{'FINISHED'}


def add_j_shift_p(self, context):
    ob = bpy.context.active_object
    ob["shift"] = "shift=value"
    return{'FINISHED'}


def add_j_climit_p(self, context):
    ob = bpy.context.active_object
    ob["constraint_limit"] = "constraint_limit=value"
    return{'FINISHED'}


def add_j_cminang_p(self, context):
    ob = bpy.context.active_object
    ob["constraint_minang"] = "constraint_minang=value"
    return{'FINISHED'}


def add_j_cmaxang_p(self, context):
    ob = bpy.context.active_object
    ob["consrtaint_maxang"] = "consrtaint_maxang=value"
    return{'FINISHED'}


def add_j_cdamp_p(self, context):
    ob = bpy.context.active_object
    ob["constraint_damping"] = "constraint_damping=value"
    return{'FINISHED'}


def add_j_ccol_p(self, context):
    ob = bpy.context.active_object
    ob["constraint_collides"] = "constraint_collides=value"
    return{'FINISHED'}


# rendermesh
def add_rm_e_p(self, context):
    ob = bpy.context.active_object
    ob["entity"] = "entity=1"
    return{'FINISHED'}


def add_rm_m_p(self, context):
    ob = bpy.context.active_object
    ob["mass"] = "mass=15"
    return{'FINISHED'}


def add_rm_d_p(self, context):
    ob = bpy.context.active_object
    ob["density"] = "density=15"
    return{'FINISHED'}


def add_rm_p_p(self, context):
    ob = bpy.context.active_object
    ob["pieces"] = "pieces=EG:_piece01,_piece02.."
    return{'FINISHED'}


# might remove
def add_ent_p(self, context):
    ob = bpy.context.active_object
    ob["entity"] = "entity=1"
    ob["mass"] = "mass=15"
    return{'FINISHED'}


# end jointed breakables
# wheel
def add_w_phl(self, context):
    ob = bpy.context.active_object
    ob["wheel"] = "wheel"
    # ob["mass"] = "mass=15"
    return{'FINISHED'}


# deformable mesh skeleton props
def add_skel_p(self, context):
        ob = bpy.context.active_object
        ob["stfns"] = "stiffness=10"
        ob["stfns"] = "hardness=10"
        ob["mxstr"] = "max_stretch=0.01"
        ob["mxstr"] = "max_impulse=10"
        ob["skdist"] = "skin_dist=0.4"
        ob["thkns"] = "thickness=0.01"
        ob["notap"] = "notaprim=1"
        ob["thkns"] = "explosion_scale=0.01"
        ob["mass"] = "mass=0.05"  # might move
        return{'FINISHED'}


# CGF/CGA/CHR props
# phys proxy
def add_neo_p(self, context):
    ob = bpy.context.active_object
    ob["no_explosion_occlusion"] = "no_explosion_occlusion=1"
    return{'FINISHED'}


def add_orm_p(self, context):
    ob = bpy.context.active_object
    ob["other_rendermesh"] = "other_rendermesh=1"
    return{'FINISHED'}


def add_colp_p(self, context):
    ob = bpy.context.active_object
    ob["colltype_player"] = "colltype_player=1"
    return{'FINISHED'}


def add_b_p(self, context):
    ob = bpy.context.active_object
    ob["box"] = "box=1"
    return{'FINISHED'}


def add_cyl_p(self, context):
    ob = bpy.context.active_object
    ob["cylinder"] = "cylinder=1"
    return{'FINISHED'}


def add_caps_p(self, context):
    ob = bpy.context.active_object
    ob["capsule"] = "capsule=1"
    return{'FINISHED'}


def add_sph_p(self, context):
    ob = bpy.context.active_object
    ob["sphere"] = "sphere=1"
    return{'FINISHED'}


def add_nap_p(self, context):
    ob = bpy.context.active_object
    ob["notaprim"] = "notaprim=1"
    return{'FINISHED'}


# rendermesh
def add_nhr_p(self, context):
    ob = bpy.context.active_object
    ob["no_hit_refinement"] = "no_hit_refinement=1"
    return{'FINISHED'}


def add_dyn_p(self, context):
    ob = bpy.context.active_object
    ob["dynamic"] = "dynamic=1"
    return{'FINISHED'}
# end CGF/CGA/CHR props


# material props
def add_phys_default(self, context):
    me = bpy.context.active_object
    if me.active_material:
        me.active_material.name += "__physDefault"
    return{'FINISHED'}


def add_phys_none(self, context):
    me = bpy.context.active_object
    if me.active_material:
        me.active_material.name += "__physNone"
    return{'FINISHED'}


def add_phys_pnd(self, context):
    me = bpy.context.active_object
    if me.active_material:
        me.active_material.name += "__physProxyNoDraw"
    return{'FINISHED'}


def add_phys_obstr(self, context):
    me = bpy.context.active_object
    if me.active_material:
        me.active_material.name += "__physObstruct"
    return{'FINISHED'}


def add_phys_nocol(self, context):
    me = bpy.context.active_object
    if me.active_material:
        me.active_material.name += "__physNoCollide"
    return{'FINISHED'}

# this is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
