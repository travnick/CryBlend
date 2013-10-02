# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

#------------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     primary python file for cryblend addon
#
# Author:      Angelo J. Miner
# Extended by: Duo Oratar
#
# Created:     23/02/2012
# Copyright:   (c) Angelo J. Miner 2012
# License:     GPLv2+
#------------------------------------------------------------------------------


bl_info = {
    "name": "CryEngine3 Utilities and Exporter",
    "author": "Angelo J. Miner & Duo Oratar",
    "blender": (2, 6, 8),
    "version": (4, 10, 0, 3, 'dev'),
    "location": "CryBlend Menu",
    "description": "CryEngine3 Utilities and Exporter",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/"
        "Import-Export/CryEngine3",
    "tracker_url": "https://github.com/travnick/CryBlend/issues?state=open",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

VERSION = bl_info["version"]

if "bpy" in locals():
    import imp
    imp.reload(add)
    imp.reload(export)
    imp.reload(exceptions)
else:
    import bpy
    from io_export_cryblend import add, export, exceptions

from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, \
    FloatProperty, StringProperty
from bpy_extras.io_utils import ExportHelper
from io_export_cryblend.configuration import CONFIG, save_config
from io_export_cryblend.outPipe import cbPrint
import bmesh
import bpy.ops
import bpy_extras
import configparser
import os
import os.path
import pickle
import webbrowser


# for help
new = 2  # open in a new tab, if possible


class Find_Rc(bpy.types.Operator, ExportHelper):
    bl_label = "Find the Resource compiler"
    bl_idname = "f_ind.rc"

    filename_ext = ".exe"

    def execute(self, context):
        CONFIG['RC_LOCATION'] = "%s" % self.filepath

        cbPrint("Found RC at {!r}.".format(CONFIG['RC_LOCATION']), 'debug')

        save_config()
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = ''.join([CONFIG['RC_LOCATION'], "rc.exe"])

        return ExportHelper.invoke(self, context, event)


class CryBlend_Cfg(bpy.types.Operator):
    '''operator: saves current cryblend configuration'''
    bl_idname = "save_config.file"
    bl_label = "save config file"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        save_config()
        # Report.reset()
        # Report.messages.append('SAVED %s' %CONFIG_FILEPATH)
        # Report.show()
        cbPrint('Saved %s' % CONFIG_FILEPATH)
        return {'FINISHED'}


class Open_UDP_Wp(bpy.types.Operator):
    bl_label = "Open Web Page for UDP"
    bl_idname = "open_udp.wp"

    def execute(self, context):
        url = "http://freesdk.crydev.net/display/SDKDOC3/UDP+Settings"
        webbrowser.open(url, new=new)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# class Open_Donate_Wp(bpy.types.Operator):
    # bl_label = "Open Web Page to donate to the cause"
    # bl_idname = "open_donate.wp"
    # def execute(self, context):
        # url = "https://sites.google.com/site/cryblend/"
        # webbrowser.open(url,new=new)
        # #self.report({'INFO'}, message)
        # #print(message)
        # return {'FINISHED'}


class Get_Ridof_Nasty(bpy.types.Operator):
    '''Select the object to test in object mode with nothing selected in
    it's mesh before running this.'''
    bl_label = "Find Degenerate Faces"
    bl_idname = "find_deg.faces"

    def execute(self, context):
        me = bpy.context.active_object
        vert_list = [vert for vert in me.data.vertices]
        # bpy.ops.object.mode_set(mode='EDIT')
        context.tool_settings.mesh_select_mode = (True, False, False)
        # bpy.ops.mesh.select_all(
        #    {'object':me, 'active_object':me, 'edit_object':me},
        #    action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        cbPrint("Locating degenerate faces.")
        for i in me.data.polygons:
            # print("1 face")
            if i.area == 0:
                cbPrint("Found a degenerate face.")
            for v in i.vertices:
                if i.area == 0:
                    cbPrint("Selecting face vertices.")
                    vert_list[v].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


# Duo Oratar
class Find_multiFaceLine(bpy.types.Operator):
    '''Select the object to test in object mode with nothing selected in
    it's mesh before running this.'''
    bl_label = "Find lines with 3+ faces."
    bl_idname = "find_multiface.lines"

    def execute(self, context):
        me = bpy.context.active_object
        vert_list = [vert for vert in me.data.vertices]
        # bpy.ops.object.mode_set(mode='EDIT')
        context.tool_settings.mesh_select_mode = (True, False, False)
        # bpy.ops.mesh.select_all(
        #     {'object':me, 'active_object':me, 'edit_object':me},
        #     action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        cbPrint("Locating degenerate faces.")
        for i in me.data.edges:
            counter = 0
            for polygon in me.data.polygons:
                if (i.vertices[0] in polygon.vertices
                    and i.vertices[1] in polygon.vertices):
                    counter += 1
            if counter > 2:
                cbPrint('Found a multi-face line')
                for v in i.vertices:
                    cbPrint('Selecting line vertices.')
                    vert_list[v].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


#------------------------------------------------------------------------------
# Menu Classes
# Interfaces with defs in external .py
#------------------------------------------------------------------------------
class Add_BO_Joint(bpy.types.Operator):  # , AddObjectHelper):
    bl_label = "Add Joint"
    bl_idname = "add_bo.joint"

    def execute(self, context):
        # from . import helper
        return add.add_joint(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# Add_CE_Node so short it doesn't really need to be in add
class Add_CE_Node(bpy.types.Operator):  # , AddObjectHelper):
    bl_label = "Add CryExportNode"
    bl_idname = "add_cryexport.node"
    my_string = StringProperty(name="CryExportNode name")

    def execute(self, context):
        bpy.ops.group.create(name="CryExportNode_%s" % (self.my_string))
        message = "Adding CryExportNode_'%s'" % (self.my_string)
        self.report({'INFO'}, message)
        cbPrint(message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class Add_ANIM_Node(bpy.types.Operator):  # , AddObjectHelper):
    bl_label = "Add AnimNode"
    bl_idname = "add_anim.node"
    my_string = StringProperty(name="Animation Name")
    my_floats = FloatProperty(name="Start Frame")
    my_floate = FloatProperty(name="End Frame")

    def execute(self, context):
        # bpy.ops.group.create(name="CryExportNode_%s" % (self.my_string))
        ob = bpy.context.active_object
        bpy.ops.object.add(type='EMPTY')
        anode = bpy.context.object
        anode.name = 'animnode'
        anode["animname"] = self.my_string  # "door open"
        anode["startframe"] = self.my_floats  # 1
        anode["endframe"] = self.my_floate  # 1
#      anode.select = False
#      anode.select = True
        if ob:
            ob.select = True
            bpy.context.scene.objects.active = ob

        bpy.ops.object.parent_set(type='OBJECT')
        message = "Adding AnimNode '%s'" % (self.my_string)
        self.report({'INFO'}, message)
        cbPrint(message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


# custom props
# wheels
class Add_wh_Prop(bpy.types.Operator):
    bl_label = "Add wheel Properties"
    bl_idname = "add_wh.props"

    def execute(self, context):
        return add.add_w_phl(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# wheel transform fix
class Fix_wh_trans(bpy.types.Operator):
    bl_label = "Fix wheel Transforms"
    bl_idname = "fix_wh.trans"

    def execute(self, context):
        ob = bpy.context.active_object
        ob.location.x = (ob.bound_box[0][0] + ob.bound_box[1][0])
        ob.location.x /= 2.0
        ob.location.y = (ob.bound_box[2][0] + ob.bound_box[3][0])
        ob.location.y /= 2.0
        ob.location.z = (ob.bound_box[4][0] + ob.bound_box[5][0])
        ob.location.z /= 2.0
        # return utils.fix_transforms
        return {'FINISHED'}


# jointed breakables
# rendermesh
class Add_rm_e_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_rm_e.props"

    def execute(self, context):
        return add.add_rm_e_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_rm_m_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_rm_m.props"

    def execute(self, context):
        return add.add_rm_m_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_rm_d_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_rm_d.props"

    def execute(self, context):
        return add.add_rm_d_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_rm_p_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_rm_p.props"

    def execute(self, context):
        return add.add_rm_p_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# joint
class Add_j_gpc_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_gpc.props"

    def execute(self, context):
        return add.add_j_gpc_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_pcb_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_pcb.props"

    def execute(self, context):
        return add.add_j_pcb_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_b_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_b.props"

    def execute(self, context):
        return add.add_j_b_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_t_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_t.props"

    def execute(self, context):
        return add.add_j_t_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_pull_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_pull.props"

    def execute(self, context):
        return add.add_j_pull_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_push_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_push.props"

    def execute(self, context):
        return add.add_j_push_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_shift_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_shift.props"

    def execute(self, context):
        return add.add_j_shift_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_climit_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_climit.props"

    def execute(self, context):
        return add.add_j_climit_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_cminang_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_cminang.props"

    def execute(self, context):
        return add.add_j_cminang_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_cmaxang_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_cmaxang.props"

    def execute(self, context):
        return add.add_j_cmaxang_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_cdamp_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_cdamp.props"

    def execute(self, context):
        return add.add_j_cdamp_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_j_ccol_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_j_ccol.props"

    def execute(self, context):
        return add.add_j_ccol_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# jointed breakables
class Find_Weightless(bpy.types.Operator):
    bl_label = "Find Weightless Vertices"
    bl_idname = "mesh_rep.weightless"

    def execute(self, context):
        obj = bpy.context.active_object
        if obj.type == 'MESH':
            for v in obj.data.vertices:
                v.select = True
                for g in v.groups:
                    v.select = False
                    break
        return {'FINISHED'}


class Find_Overweight(bpy.types.Operator):
    bl_label = "Find Overweight Vertices"
    bl_idname = "mesh_rep.overweight"

    def execute(self, context):
        obj = bpy.context.active_object
        if obj.type == 'MESH':
            for v in obj.data.vertices:
                v.select = False
                totalWeight = 0
                for g in v.groups:
                    totalWeight += g.weight
                if totalWeight > 1:
                    cbPrint("Vertex at " + str(v.co) + " has a weight of "
                            + str(totalWeight))
                    v.select = True
        return {'FINISHED'}


class Find_Underweight(bpy.types.Operator):
    bl_label = "Find Underweight Vertices"
    bl_idname = "mesh_rep.underweight"

    def execute(self, context):
        obj = bpy.context.active_object
        if obj.type == 'MESH':
            for v in obj.data.vertices:
                v.select = False
                totalWeight = 0
                for g in v.groups:
                    totalWeight += g.weight
                if totalWeight < 1:
                    cbPrint("Vertex at " + str(v.co) + " has a weight of "
                            + str(totalWeight))
                    v.select = True
        return {'FINISHED'}


class Remove_All_Weight(bpy.types.Operator):
        bl_label = "Remove all weight from selected vertices"
        bl_idname = "mesh_rep.removeall"

        def execute(self, context):
            obj = bpy.context.active_object
            if obj.type == 'MESH':
                verts = []
                for v in obj.data.vertices:
                    if v.select:
                        verts.append(v)
                for v in verts:
                    for g in v.groups:
                        g.weight = 0
            return {'FINISHED'}


class Remove_FakeBones(bpy.types.Operator):
        bl_label = "Remove all FakeBones"
        bl_idname = "cb.fake_bone_remove"

        def execute(self, context):
            for obj in bpy.data.objects:
                obj.select = False

            for obj in bpy.context.selectable_objects:
                isFakeBone = False
                try:
                    throwaway = obj['fakebone']
                    isFakeBone = True
                except:
                    pass
                if (obj.name == obj.parent_bone
                    and isFakeBone
                    and obj.type == 'MESH'):
                    obj.select = True
                    bpy.ops.object.delete(use_global=False)
                    # {'active_object':obj, 'object':obj},
            return {'FINISHED'}


class Find_No_UVs(bpy.types.Operator):
        bl_label = "Find all objects with no UVs"
        bl_idname = "cb.find_no_uvs"

        def execute(self, context):
            for obj in bpy.data.objects:
                obj.select = False

            for obj in bpy.context.selectable_objects:
                if obj.type == 'MESH':
                    a = False
                    # TODO: WTF?
                    for i in obj.data.uv_textures:
                        a = True
                        break
                    if not a:
                        obj.select = True
            return {'FINISHED'}


class Add_Def_Prop(bpy.types.Operator):
    bl_label = "Add DeformableMesh Properties"
    bl_idname = "add_skeleton.props"

    def execute(self, context):
        return add.add_skel_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# mat phys
class Add_M_Pd(bpy.types.Operator):
    bl_label = "Add __physDefault to Material Name"
    bl_idname = "mat_phys.def"

    def execute(self, context):
        return add.add_phys_default(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_M_PND(bpy.types.Operator):
    bl_label = "Add __physProxyNoDraw to Material Name"
    bl_idname = "mat_phys.pnd"

    def execute(self, context):
        return add.add_phys_pnd(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_M_None(bpy.types.Operator):
    bl_label = "Add __physNone to Material Name"
    bl_idname = "mat_phys.none"

    def execute(self, context):
        return add.add_phys_none(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_M_Obstr(bpy.types.Operator):
    bl_label = "Add __physObstruct to Material Name"
    bl_idname = "mat_phys.obstr"

    def execute(self, context):
        return add.add_phys_obstr(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_M_NoCol(bpy.types.Operator):
    bl_label = "Add __physNoCollide to Material Name"
    bl_idname = "mat_phys.nocol"

    def execute(self, context):
        return add.add_phys_nocol(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# CGF/CGA/CHR
class Add_neo_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_neo.props"

    def execute(self, context):
        return add.add_neo_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_orm_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_orm.props"

    def execute(self, context):
        return add.add_orm_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_colp_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_colp.props"

    def execute(self, context):
        return add.add_colp_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_b_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_b.props"

    def execute(self, context):
        return add.add_b_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_cyl_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_cyl.props"

    def execute(self, context):
        return add.add_cyl_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_caps_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_caps.props"

    def execute(self, context):
        return add.add_caps_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_sph_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_sph.props"

    def execute(self, context):
        return add.add_sph_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_nap_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_nap.props"

    def execute(self, context):
        return add.add_nap_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_nhr_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_nhr.props"

    def execute(self, context):
        return add.add_nhr_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_dyn_Prop(bpy.types.Operator):
    bl_label = "Add Entity Properties"
    bl_idname = "add_dyn.props"

    def execute(self, context):
        return add.add_dyn_p(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}

# fakebones
# todo:
# figure out how to auto parent to proper bone<<DONE!!
# WARNING!!
#this cleans out all meshes without users!!!


# verts and faces
def add_fake_bone(width, height, depth):
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    verts = [(-0.02029, -0.02029, -0.02029),
             (-0.02029, 0.02029, -0.02029),
             (0.02029, 0.02029, -0.02029),
             (0.02029, -0.02029, -0.02029),
             (-0.02029, -0.02029, 0.02029),
             (-0.02029, 0.02029, 0.02029),
             (0.02029, 0.02029, 0.02029),
             (0.02029, -0.02029, 0.02029),
             ]

    faces = [(0, 1, 2, 3),
             (4, 7, 6, 5),
             (0, 4, 5, 1),
             (1, 5, 6, 2),
             (2, 6, 7, 3),
             (4, 0, 3, 7),
            ]

    # apply size
    for i, v in enumerate(verts):
        verts[i] = v[0] * width, v[1] * depth, v[2] * height

    return verts, faces


def add_bone_geometry():
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    verts = [(-0.5, -0.5, -0.5),
             (-0.5, 0.5, -0.5),
             (0.5, 0.5, -0.5),
             (0.5, -0.5, -0.5),
             (-0.5, -0.5, 0.5),
             (-0.5, 0.5, 0.5),
             (0.5, 0.5, 0.5),
             (0.5, -0.5, 0.5),
             ]

    faces = [(0, 1, 2, 3),
             (4, 7, 6, 5),
             (0, 4, 5, 1),
             (1, 5, 6, 2),
             (2, 6, 7, 3),
             (4, 0, 3, 7),
            ]

    return verts, faces


# Duo Oratar
class RenamePhysBones(bpy.types.Operator):
    '''Renames phys bones'''
    bl_idname = "cb.phys_bones_rename"
    bl_label = "Rename Phys bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.context.scene.objects:
            if ('_Phys' == obj.name[-5:]
                and obj.type == 'ARMATURE'):
                for bone in obj.data.bones:
                    oldName = bone.name
                    bone.name = oldName + '_Phys'

        return {'FINISHED'}


class AddBoneGeometry(bpy.types.Operator):
    '''Add BoneGeometry for bones in selected armatures'''
    bl_idname = "cb.bone_geom_add"
    bl_label = "Add boneGeometry"
    bl_options = {'REGISTER', 'UNDO'}

    view_align = BoolProperty(
            name="Align to View",
            default=False,
            )
    location = FloatVectorProperty(
            name="Location",
            subtype='TRANSLATION',
            )
    rotation = FloatVectorProperty(
            name="Rotation",
            subtype='EULER',
            )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Add boneGeometry")

    def execute(self, context):
        verts_loc, faces = add_bone_geometry()

        nameList = []
        for obj in bpy.context.scene.objects:
            nameList.append(obj.name)

        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE' and obj.select:

                physBonesList = []
                if obj.name + "_Phys" in nameList:
                    for bone in bpy.data.objects[obj.name + "_Phys"].data.bones:
                        physBonesList.append(bone.name)

                for bone in obj.data.bones:
                    if ((not bone.name + "_boneGeometry" in nameList
                            and not obj.name + "_Phys" in nameList)
                        or (obj.name + "_Phys" in nameList
                            and bone.name + '_Phys' in physBonesList
                            and not bone.name + "_boneGeometry" in nameList)
                        ):
                        mesh = bpy.data.meshes.new(
                                    "{!s}_boneGeometry".format(bone.name)
                        )
                        bm = bmesh.new()

                        for v_co in verts_loc:
                            bm.verts.new(v_co)

                        for f_idx in faces:
                            bm.faces.new([bm.verts[i] for i in f_idx])

                        bm.to_mesh(mesh)
                        mesh.update()
                        bmatrix = bone.head_local
                        # loc, rotation, scale = bmatrix.decompose()
                        self.location[0] = bmatrix[0]
                        self.location[1] = bmatrix[1]
                        self.location[2] = bmatrix[2]
                        # add the mesh as an object into the scene
                        # with this utility module
                        from bpy_extras import object_utils
                        object_utils.object_data_add(
                            context, mesh, operator=self
                        )
                        bpy.ops.mesh.uv_texture_add()

        return {'FINISHED'}


class RemoveBoneGeometry(bpy.types.Operator):
    '''Remove BoneGeometry for bones in selected armatures'''
    bl_idname = "cb.bone_geom_remove"
    bl_label = "Remove boneGeometry"
    bl_options = {'REGISTER', 'UNDO'}

    view_align = BoolProperty(
            name="Align to View",
            default=False,
            )
    location = FloatVectorProperty(
            name="Location",
            subtype='TRANSLATION',
            )
    rotation = FloatVectorProperty(
            name="Rotation",
            subtype='EULER',
            )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Remove boneGeometry")

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')

        armatureList = []  # Get list of armatures requiring attention
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE' and obj.select:  # Get selected armatures
                armatureList.append(obj.name)

        nameList = []  # Get list of objects
        for obj in bpy.context.scene.objects:
            nameList.append(obj.name)
            obj.select = False

        for name in armatureList:
            obj = bpy.context.scene.objects[name]
            physBonesList = []
            # Get list of phys bones in matching phys skel
            if obj.name + "_Phys" in nameList:
                for bone in bpy.data.objects[obj.name + "_Phys"].data.bones:
                    physBonesList.append(bone.name)

            for bone in obj.data.bones:  # For each bone
                if bone.name + "_boneGeometry" in nameList:
                    bpy.data.objects[bone.name + "_boneGeometry"].select = True

            bpy.ops.object.delete()

        return {'FINISHED'}


# verts and faces
# find bone heads and add at that location
class AddFakeBone(bpy.types.Operator):
    '''Add a simple box mesh'''
    bl_idname = "cb.fake_bone_add"
    bl_label = "Add FakeBone"
    bl_options = {'REGISTER', 'UNDO'}

    width = FloatProperty(
            name="Width",
            description="Box Width",
            min=0.01, max=100.0,
            default=1.0,
            )
    height = FloatProperty(
            name="Height",
            description="Box Height",
            min=0.01, max=100.0,
            default=1.0,
            )
    depth = FloatProperty(
            name="Depth",
            description="Box Depth",
            min=0.01, max=100.0,
            default=1.0,
            )

    # generic transform props
    view_align = BoolProperty(
            name="Align to View",
            default=False,
            )
    location = FloatVectorProperty(
            name="Location",
            subtype='TRANSLATION',
            )
    rotation = FloatVectorProperty(
            name="Rotation",
            subtype='EULER',
            )

    def execute(self, context):
        verts_loc, faces = add_fake_bone(1, 1, 1,)
        for om in bpy.data.meshes:
            if om.users == 0:
                bpy.data.meshes.remove(om)

        ob = bpy.context.scene.objects
        for arm in ob:
            if arm.type == 'ARMATURE':

                for pbone in arm.pose.bones:
                    mesh = bpy.data.meshes.new("%s" % pbone.name)
                    bm = bmesh.new()

                    for v_co in verts_loc:
                        bm.verts.new(v_co)

                    for f_idx in faces:
                        bm.faces.new([bm.verts[i] for i in f_idx])

                    bm.to_mesh(mesh)
                    mesh.update()
                    bmatrix = pbone.bone.head_local
                    # loc, rotation, scale = bmatrix.decompose()
                    self.location[0] = bmatrix[0]
                    self.location[1] = bmatrix[1]
                    self.location[2] = bmatrix[2]
                    # add the mesh as an object into the scene
                    # with this utility module
                    from bpy_extras import object_utils
                    object_utils.object_data_add(context, mesh, operator=self)
                    bpy.ops.mesh.uv_texture_add()
                    for fb in ob:
                        if fb.name == pbone.name:
                            fb["fakebone"] = "fakebone"
                    bpy.context.scene.objects.active = arm
                    arm.data.bones.active = pbone.bone
                    bpy.ops.object.parent_set(type='BONE')

        return {'FINISHED'}

# fakebones
# keyframe insert for fake bones
loclist = []
rotlist = []
# scene = bpy.context.scene


def add_kfl(self, context):
    scene = bpy.context.scene
    object_ = None
    for a in bpy.context.scene.objects:
        if a.type == 'ARMATURE':
            object_ = a
    bpy.ops.screen.animation_play()

    def kfdat(frame, bonename, data):
        return frame, bonename, data

    if object_:
        for frame in range(scene.frame_end + 1):
            # frame = frame + 5
            '''do the inverse parent times current to get proper info here'''
            cbPrint("Stage 1 auto-keyframe.")
            scene.frame_set(frame)
            for bone in object_.pose.bones:
                if bone.parent:
                    if bone.parent.parent:
                        for bonep in bpy.context.scene.objects:
                            if bonep.name == bone.parent.name:
                                bonepm = bonep.matrix_local
                        for bonec in bpy.context.scene.objects:
                            if bonec.name == bone.name:
                                bonecm = bonec.matrix_local
                        animatrix = bonepm.inverted() * bonecm
                        lm, rm, sm = animatrix.decompose()
                        ltmp = kfdat(frame, bone.name, lm)
                        rtmp = kfdat(frame, bone.name, rm.to_euler())
                        loclist.append(ltmp)
                        rotlist.append(rtmp)
                    else:
                        for i in bpy.context.scene.objects:
                            if i.name == bone.name:
                                lm, rm, sm = i.matrix_local.decompose()
                                ltmp = kfdat(frame, bone.name, lm)
                                rtmp = kfdat(frame, bone.name, rm.to_euler())
                                loclist.append(ltmp)
                                rotlist.append(rtmp)
                else:
                    for i in bpy.context.scene.objects:
                        if i.name == bone.name:
                            lm, rm, sm = i.matrix_local.decompose()
                            ltmp = kfdat(frame, bone.name, lm)
                            rtmp = kfdat(frame, bone.name, rm.to_euler())
                            loclist.append(ltmp)
                            rotlist.append(rtmp)
        bpy.ops.screen.animation_play()

    # for frame in range(scene.frame_end + 1):
    #   print("stage2 auto keyframe")
        # scene.frame_set(frame)
        # for bone in object_.pose.bones:
        #   for i in bpy.context.scene.objects:
            #   if i.name == bone.name:
                #   for fr in loclist:
                    #   print(fr)
                        # if fr[0] == frame:
                        #   if fr[1] == bone.name:
                            #       print(fr[2])
                                #   i.location = fr[2]
                                    # i.keyframe_insert(data_path="location")
                    # for fr in rotlist:
                    #   print(fr)
                        # if fr[0] == frame:
                        #   if fr[1] == bone.name:
                            #       print(fr[2])
                                #   i.rotation_euler = fr[2]
                                    # i.keyframe_insert(
                                    #    data_path="rotation_euler")

    # bpy.ops.screen.animation_play()

    return {'FINISHED'}


def add_kf(self, context):
    scene = bpy.context.scene
    sfc = scene.frame_current
    object_ = None
    for a in bpy.context.scene.objects:
        if a.type == 'ARMATURE':
            object_ = a
            break

    if object_:
        for bone in object_.pose.bones:
            i = bpy.context.scene.objects.get(bone.name)
            if i is not None:
                # TODO: merge those two for loops
                for fr in loclist:
                    if fr[0] == sfc:
                        if fr[1] == bone.name:
                            cbPrint(fr[2])
                            i.location = fr[2]
                            i.keyframe_insert(data_path="location")
                for fr in rotlist:
                    cbPrint(fr)
                    if fr[0] == sfc:
                        if fr[1] == bone.name:
                            cbPrint(fr[2])
                            i.rotation_euler = fr[2]
                            i.keyframe_insert(data_path="rotation_euler")
    return {'FINISHED'}


# fakebone keyframe
class Make_key_framelist(bpy.types.Operator):
    bl_label = "Make Fakebone Keyframes list"
    bl_idname = "make_fb.kfml"

    def execute(self, context):
        return add_kfl(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class Add_fkey_frame(bpy.types.Operator):
    bl_label = "Add Fakebone Keyframe"
    bl_idname = "add_fb.kfm"

    def execute(self, context):
        return add_kf(self, context)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# exporter
# systemconsole
# class Toggle_sys_con(bpy.types.Operator):
    # bl_label = "Toggle System Console"
    # bl_idname = "tog_sys.con"
    # def execute(self, context):
        # return bpy.ops.wm.console_toggle()
        # self.report({'INFO'}, message)
        # cbPrint(message)
        # return {'FINISHED'}


class Export(bpy.types.Operator, ExportHelper):
    bl_label = "Export To Game"
    bl_idname = "export_to.game"
    filename_ext = ".dae"
    filter_glob = StringProperty(default="*.dae", options={'HIDDEN'})

    export_type = EnumProperty(
            name="File Type:",
            description="Select a file type to export.",
            items=(
                ("CGF", "CGF",
                 "Static geometry"),
                ("CHR & CAF", "CHR",
                 "Flexible animated geometry, i.e. characters."),
                ("CGA & ANM", "CGA",
                 "Hard body animated geometry.")
            ),
            default="CGF",
    )
    merge_anm = BoolProperty(
            name="Merge anim",
            description="For Animated Models--merge animations into 1",
            default=False,
            )
    donot_merge = BoolProperty(
            name="Do Not Merge Nodes",
            description="Generally a Good Idea",
            default=True,
            )
    avg_pface = BoolProperty(
            name="Average Planar Face normals",
            description="Help align face normals that have normals"
                        + "that are within 1 degree",
            default=False,
            )
    run_rc = BoolProperty(
            name="Run Resource Compiler",
            description="Generally a Good Idea",
            default=True,
            )
    do_materials = BoolProperty(
            name="Run RC and Do Materials",
            description="Generally a Good Idea",
            default=False,
            )
    convert_source_image_to_dds = BoolProperty(
            name="Convert images to DDS",
            description="Converts source textures to DDSs"
                        + " while exporting materials",
            default=False,
            )
    save_tiff_during_conversion = BoolProperty(
            name="Save tiff during conversion",
            description="Saves tiff images that are generated"
                        + "during conversion to DDS",
            default=False,
            )
    refresh_rc = BoolProperty(
            name="Refresh RC output",
            description="Generally a Good Idea",
            default=True,
            )
    include_ik = BoolProperty(
            name="Include IK in Character",
            description="Adds IK from your skeleton to the phys skeleton"
                        + "upon export.",
            default=False,
            )
    make_layer = BoolProperty(
            name="Make .lyr file",
            description="Makes a .lyr to reassemble your scene"
                        + "in the CryEngine 3",
            default=False,
            )

    class Config:
        def __init__(self, config):
            attributes = (
                'filepath',
                'export_type',
                'merge_anm',
                'donot_merge',
                'avg_pface',
                'run_rc',
                'do_materials',
                'convert_source_image_to_dds',
                'save_tiff_during_conversion',
                'refresh_rc',
                'include_ik',
                'make_layer'
            )

            for attribute in attributes:
                setattr(self, attribute, getattr(config, attribute))

    def execute(self, context):
        exe = CONFIG['RC_LOCATION']
        cbPrint(CONFIG['RC_LOCATION'])
        try:
            config = Export.Config(config=self)
            export.save(config, context, exe)
            self.filepath = '//'

        except exceptions.CryBlendException as exception:
            cbPrint(exception.what(), 'error')
            bpy.ops.error.message('INVOKE_DEFAULT', message=exception.what())

        return {'FINISHED'}


class ErrorHandler(bpy.types.Operator):
    WIDTH = 400
    HEIGHT = 200
    bl_idname = "error.message"
    bl_label = "Error:"

    message = bpy.props.StringProperty()

    def execute(self, context):
        self.report({'ERROR'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, self.WIDTH, self.HEIGHT)

    def draw(self, context):
        self.layout.label(self.bl_label, icon='ERROR')
        self.layout.split()
        multiline_label(self.layout, self.message)
        self.layout.split()
        self.layout.split(0.2)


def multiline_label(layout, text):
    for line in text.splitlines():
        row = layout.split()
        row.label(line)


############################### MENU   ################################
class Mesh_Repair_Tools(bpy.types.Menu):
    bl_idname = "mesh_rep_tools"
    bl_label = "Weight Paint Repair"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text="Mesh Repair Tools")
        layout.separator()
        layout.operator("mesh_rep.underweight", icon='MESH_CUBE')
        layout.operator("mesh_rep.overweight", icon='MESH_CUBE')
        layout.operator("mesh_rep.weightless", icon='MESH_CUBE')
        layout.operator("mesh_rep.removeall", icon='MESH_CUBE')


class Mat_phys_add(bpy.types.Menu):
    bl_idname = "Mat_ph_add"
    bl_label = "Add Material Physics"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text="Add Material Physics")
        layout.separator()
        layout.operator("mat_phys.def", icon='PHYSICS')
        layout.operator("mat_phys.pnd", icon='PHYSICS')
        layout.operator("mat_phys.none", icon='PHYSICS')
        layout.operator("mat_phys.obstr", icon='PHYSICS')
        layout.operator("mat_phys.nocol", icon='PHYSICS')


class J_Props_Add(bpy.types.Menu):
    bl_idname = "j_props.add"
    bl_label = "Add JOINTED (pre-broken) BREAKABLES Properties"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text="Rendermesh:")
        layout.operator("add_rm_e.props", icon='SCRIPT', text="entity")
        layout.operator("add_rm_m.props", icon='SCRIPT', text="mass=value")
        layout.operator("add_rm_d.props", icon='SCRIPT', text="density=value")
        layout.operator("add_rm_p.props", icon='SCRIPT', text="pieces=value")
        layout.separator()
        layout.label(text="Joint Node:")
        layout.operator("add_j_gpc.props", icon='SCRIPT',
                        text="gameplay_critical")
        layout.operator("add_j_pcb.props", icon='SCRIPT',
                        text="player_can_break")
        layout.operator("add_j_b.props", icon='SCRIPT', text="bend")
        layout.operator("add_j_t.props", icon='SCRIPT', text="twist")
        layout.operator("add_j_pull.props", icon='SCRIPT', text="pull")
        layout.operator("add_j_push.props", icon='SCRIPT', text="push")
        layout.operator("add_j_shift.props", icon='SCRIPT', text="shift")
        layout.operator("add_j_climit.props", icon='SCRIPT',
                        text="constraint_limit")
        layout.operator("add_j_cminang.props", icon='SCRIPT',
                        text="constraint_minang")
        layout.operator("add_j_cmaxang.props", icon='SCRIPT',
                        text="consrtaint_maxang")
        layout.operator("add_j_cdamp.props", icon='SCRIPT',
                        text="constraint_damping")
        layout.operator("add_j_ccol.props", icon='SCRIPT',
                        text="constraint_collides")


# cgf/cga/chr
class CFAR_Props_Add(bpy.types.Menu):
    bl_idname = "cfar_props.add"
    bl_label = "Add CGF/CGA/CHR Properties"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text="Phys Proxy:")
        layout.operator("add_neo.props", icon='SCRIPT',
                        text="no_explosion_occlusion")
        layout.operator("add_orm.props", icon='SCRIPT',
                        text="other_rendermesh")
        layout.operator("add_colp.props", icon='SCRIPT',
                        text="colltype_player")
        layout.operator("add_b.props", icon='SCRIPT', text="box")
        layout.operator("add_cyl.props", icon='SCRIPT', text="cylinder")
        layout.operator("add_caps.props", icon='SCRIPT', text="capsule")
        layout.operator("add_sph.props", icon='SCRIPT', text="sphere")
        layout.operator("add_nap.props", icon='SCRIPT', text="notaprim")
        layout.separator()
        layout.label(text="Rendermesh:")
        layout.operator("add_nhr.props", icon='SCRIPT',
                        text="no_hit_refinement")
        layout.operator("add_dyn.props", icon='SCRIPT', text="dynamic")


class Cust_props_add(bpy.types.Menu):
    bl_idname = "Cust_props.add"
    bl_label = "Add Custom Properties"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text="Add Custom Properties")
        layout.separator()
        layout.operator("open_udp.wp", icon='HELP')
        layout.separator()
        layout.label(text="CGF/CGA/CHR:")
        layout.menu("cfar_props.add", icon='SCRIPT')
        # layout.operator("add_entity.props", icon='SCRIPT')
        layout.separator()
        layout.label(text="JOINTED (pre-broken) BREAKABLES:")
        layout.menu("j_props.add", icon='SCRIPT')
        layout.separator()
        layout.label(text="DEFORMABLES:")
        layout.operator("add_skeleton.props", icon='SCRIPT',
                    text="Add Properties to your deformable mesh skeleton.")
        layout.separator()
        layout.label(text="Vehicles:")
        layout.operator("add_wh.props", icon='SCRIPT',
                        text="Add Properties to your Vehicle Wheels.")


class CustomMenu(bpy.types.Menu):
    # bl_space_type = 'INFO'#testing
    bl_label = "CryBlend Menu"
    bl_idname = "OBJECT_MT_custom_menu"

    def draw(self, context):
        userpref = context.user_preferences
        paths = userpref.filepaths
        layout = self.layout
        # version number
        layout.label(text='v' + '.'.join(str(n) for n in VERSION))
        # layout.operator("open_donate.wp", icon='FORCE_DRAG')
        layout.operator("add_cryexport.node", icon='VIEW3D_VEC')
        layout.operator("add_bo.joint", icon='META_CUBE')
        layout.separator()
        layout.operator("add_anim.node", icon='POSE_HLT')
        layout.separator()
        layout.operator("cb.fake_bone_add", icon='BONE_DATA')
        layout.operator("cb.fake_bone_remove", icon='BONE_DATA')
        layout.separator()
        layout.operator("cb.bone_geom_add", icon="PHYSICS")
        layout.operator("cb.bone_geom_remove", icon="PHYSICS")
        layout.operator("cb.phys_bones_rename", icon="PHYSICS")
        layout.separator()
        layout.operator("make_fb.kfml", icon='KEY_HLT')
        layout.operator("add_fb.kfm", icon='KEY_HLT')
        layout.separator()
        # layout.operator_context = 'EXEC_AREA'
        # layout.label(text="Add Material Physics", icon="PHYSICS")
        layout.menu("Mat_ph_add", icon='PHYSICS')
        layout.separator()
        layout.menu("mesh_rep_tools", icon="MESH_CUBE")
        layout.separator()
        layout.operator("cb.find_no_uvs", icon="UV_FACESEL")
        layout.separator()
        # layout.label(text="Add Custom Properties", icon="SCRIPT")
        layout.menu("Cust_props.add", icon='SCRIPT')
        layout.separator()
        layout.operator("find_deg.faces", icon='ZOOM_ALL')
        layout.operator("find_multiface.lines", icon='ZOOM_ALL')
        layout.separator()
        # layout.operator("fix_wh.trans", icon='ZOOM_ALL')
        layout.separator()
        layout.operator("f_ind.rc", icon='SCRIPTWIN')
        layout.separator()
        layout.separator()
        # layout.label(text="Export to CryEngine", icon='GAME')
        layout.operator("export_to.game", icon='GAME')
        layout.separator()
        # layout.operator("tog_sys.con", icon="CONSOLE")
        # layout.label(text="rc.exe:")
        # layout.prop(paths, "r_c", text="")
        # layout.operator("f_ind.rc", icon='GAME')
        # layout.operator("save_config.file", icon='GAME')
        # use an operator enum property to populate a submenu
        # layout.operator_menu_enum("object.select_by_type",
        #                           property="type",
        #                           text="Select All by Type...",
        #                           )save_config.file


def draw_item(self, context):
    layout = self.layout
    layout.menu(CustomMenu.bl_idname)


def get_classes_to_register():
    classes = (
        CustomMenu,
        Add_CE_Node,
        Add_BO_Joint,
        Export,
        Cust_props_add,

        Add_Def_Prop,
        Mat_phys_add,

        Mesh_Repair_Tools,
        Find_Weightless,
        Find_Overweight,
        Find_Underweight,
        Remove_All_Weight,

        Remove_FakeBones,
        Find_No_UVs,
        Add_M_Pd,
        Add_M_PND,
        Add_M_None,
        Add_M_Obstr,
        Add_M_NoCol,

        J_Props_Add,

        Add_rm_e_Prop,
        Add_rm_m_Prop,
        Add_rm_d_Prop,
        Add_rm_p_Prop,

        Add_j_gpc_Prop,
        Add_j_pcb_Prop,
        Add_j_b_Prop,
        Add_j_t_Prop,
        Add_j_pull_Prop,
        Add_j_push_Prop,
        Add_j_shift_Prop,
        Add_j_climit_Prop,
        Add_j_cminang_Prop,
        Add_j_cmaxang_Prop,
        Add_j_cdamp_Prop,
        Add_j_ccol_Prop,

        Add_neo_Prop,
        Add_orm_Prop,
        Add_colp_Prop,
        Add_b_Prop,
        Add_cyl_Prop,
        Add_caps_Prop,
        Add_sph_Prop,
        Add_nap_Prop,
        Add_nhr_Prop,
        Add_dyn_Prop,

        CFAR_Props_Add,

        Open_UDP_Wp,
        Add_wh_Prop,
        Get_Ridof_Nasty,

        Find_multiFaceLine,
        CryBlend_Cfg,
        Find_Rc,

        Fix_wh_trans,
        Add_ANIM_Node,
        Make_key_framelist,
        Add_fkey_frame,
        AddFakeBone,

        RenamePhysBones,
        AddBoneGeometry,
        ErrorHandler,
        RemoveBoneGeometry,
    )

    return classes


def register():
    for classToRegister in get_classes_to_register():
        bpy.utils.register_class(classToRegister)

    # lets add ourselves to the main headerAdd_rm_e_Prop
    bpy.types.INFO_HT_header.append(draw_item)


def unregister():
    # you guys already know this but for my reference,
    # unregister your classes or when you do new scene
    # your script wont import other modules properly.
    for classToRegister in get_classes_to_register():
        bpy.utils.unregister_class(classToRegister)

    bpy.types.INFO_HT_header.remove(draw_item)


if __name__ == "__main__":
    register()

    # The menu can also be called from scripts
    bpy.ops.wm.call_menu(name=CustomMenu.bl_idname)
