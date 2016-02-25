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
#
#------------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     Primary python file for CryBlend add-on
#
# Author:      Angelo J. Miner,
#              Daniel White, David Marcelis, Duo Oratar, Mikołaj Milej,
#              Oscar Martin Garcia, Özkan Afacan
#
# Created:     23/02/2012
# Copyright:   (c) Angelo J. Miner 2012
# License:     GPLv2+
#------------------------------------------------------------------------------


bl_info = {
    "name": "CryEngine3 Utilities and Exporter",
    "author": "Angelo J. Miner, Duo Oratar, Mikołaj Milej, stardidi, "
              "Daniel White, Özkan Afacan, Oscar Martin Garcia",
    "blender": (2, 70, 0),
    "version": (5, 1, 0),
    "location": "CryBlend Menu",
    "description": "CryEngine3 Utilities and Exporter",
    "warning": "",
    "wiki_url": "https://github.com/travnick/CryBlend/wiki",
    "tracker_url": "https://github.com/travnick/CryBlend/issues?state=open",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

# old wiki url: http://wiki.blender.org/
# index.php/Extensions:2.5/Py/Scripts/Import-Export/CryEngine3

VERSION = '.'.join(str(n) for n in bl_info["version"])


if "bpy" in locals():
    import imp
    imp.reload(add)
    imp.reload(export)
    imp.reload(exceptions)
    imp.reload(utils)
    imp.reload(desc)
else:
    import bpy
    from io_export_cryblend import add, export, exceptions, utils, desc

from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, \
    FloatProperty, IntProperty, StringProperty, BoolVectorProperty
from bpy.types import Menu, Panel
from bpy_extras.io_utils import ExportHelper
from io_export_cryblend.configuration import Configuration
from io_export_cryblend.outpipe import cbPrint
from io_export_cryblend.desc import list
from xml.dom.minidom import Document, Element, parse, parseString
import bmesh
import bpy.ops
import bpy_extras
import configparser
import os
import os.path
import pickle
import webbrowser
import subprocess
import math


new = 2  # For help -> Open in a new tab, if possible.


#------------------------------------------------------------------------------
# Configurations:
#------------------------------------------------------------------------------

class PathSelectTemplate(ExportHelper):
    check_existing = True

    def execute(self, context):
        self.process(self.filepath)

        Configuration.save()
        return {'FINISHED'}


class FindRC(bpy.types.Operator, PathSelectTemplate):
    '''Select the Resource Compiler executable.'''

    bl_label = "Find The Resource Compiler"
    bl_idname = "file.find_rc"

    filename_ext = ".exe"

    def process(self, filepath):
        Configuration.rc_path = filepath
        cbPrint("Found RC at {!r}.".format(Configuration.rc_path), 'debug')

    def invoke(self, context, event):
        self.filepath = Configuration.rc_path

        return ExportHelper.invoke(self, context, event)


class FindRCForTextureConversion(bpy.types.Operator, PathSelectTemplate):
    '''Select if you are using RC from cryengine \
newer than 3.4.5. Provide RC path from cryengine 3.4.5 \
to be able to export your textures as dds files.'''

    bl_label = "Find the Resource Compiler for Texture Conversion"
    bl_idname = "file.find_rc_for_texture_conversion"

    filename_ext = ".exe"

    def process(self, filepath):
        Configuration.texture_rc_path = filepath
        cbPrint("Found RC at {!r}.".format(
            Configuration.texture_rc_path),
            'debug')

    def invoke(self, context, event):
        self.filepath = Configuration.texture_rc_path

        return ExportHelper.invoke(self, context, event)


class SelectTexturesDirectory(bpy.types.Operator, PathSelectTemplate):
    '''This path will be used to create relative path \
for textures in .mtl file.'''

    bl_label = "Select Textures Directory"
    bl_idname = "file.select_texture_dir"

    filename_ext = ""

    def process(self, filepath):
        Configuration.texture_dir = os.path.dirname(filepath)
        cbPrint("Textures directory: {!r}.".format(
            Configuration.texture_dir),
            'debug')

    def invoke(self, context, event):
        self.filepath = Configuration.texture_dir

        return ExportHelper.invoke(self, context, event)


class SaveCryBlendConfiguration(bpy.types.Operator):
    '''operator: Saves current CryBlend configuration.'''
    bl_label = "Save Config File"
    bl_idname = "config.save"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        Configuration.save()
        return {'FINISHED'}


#------------------------------------------------------------------------------
# Export Tools:
#------------------------------------------------------------------------------

class AddCryExportNode(bpy.types.Operator):
    '''Add selected objects to an existing or new CryExportNode'''
    bl_label = "Add Export Node"
    bl_idname = "object.add_cry_export_node"
    bl_options = {"REGISTER", "UNDO"}

    node_type = EnumProperty(
        name="Type",
        items=(
            ("cgf", "CGF",
             "Static Geometry"),
            ("cga", "CGA",
             "Animated Geometry"),
            ("chr", "CHR",
             "Character"),
            ("skin", "SKIN",
             "Skinned Render Mesh"),
            ("anm", "ANM",
             "Geometry Animation"),
            ("i_caf", "I_CAF",
             "Character Animation"),
        ),
        default="cgf",
    )
    node_name = StringProperty(name="Name")

    def execute(self, context):
        if bpy.context.selected_objects:
            scene = bpy.context.scene
            nodename = "{}.{}".format(self.node_name, self.node_type)
            group = bpy.data.groups.get(nodename)
            if group is None:
                bpy.ops.group.create(name=nodename)
            else:
                for object in bpy.context.selected_objects:
                    if object.name not in group.objects:
                        group.objects.link(object)
            message = "Adding Export Node"
        else:
            message = "No Objects Selected"

        self.report({"INFO"}, message)
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "Select one or more objects in OBJECT mode.")
            return {'FINISHED'}

        return context.window_manager.invoke_props_dialog(self)


class SelectedToCryExportNodes(bpy.types.Operator):
    '''Add selected objects to individual CryExportNodes.'''
    bl_label = "Nodes from Object Names"
    bl_idname = "object.selected_to_cry_export_nodes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected = bpy.context.selected_objects
        bpy.ops.object.select_all(action="DESELECT")
        for object_ in selected:
            object_.select = True
            if (len(object_.users_group) == 0):
                bpy.ops.group.create(name="{}.cgf".format(object_.name))
            object_.select = False

        for object_ in selected:
            object_.select = True

        message = "Adding Selected Objects to Export Nodes"
        self.report({"INFO"}, message)
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "Select one or more objects in OBJECT mode.")
            return {'FINISHED'}

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label("Confirm...")


class ApplyTransforms(bpy.types.Operator):
    '''Click to apply transforms on selected objects.'''
    bl_label = "Apply Transforms"
    bl_idname = "object.apply_transforms"

    def execute(self, context):
        selected = bpy.context.selected_objects
        if selected:
            message = "Applying object transforms."
            bpy.ops.object.transform_apply(
                location=True, rotation=True, scale=True)
        else:
            message = "No Object Selected."
        self.report({'INFO'}, message)
        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "Select one or more objects in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


#------------------------------------------------------------------------------
# CryEngine-Related Tools:
#------------------------------------------------------------------------------

class AddProxy(bpy.types.Operator):
    '''Click to add proxy to selected mesh. The proxy will always display as a box but will \
be converted to the selected shape in CryEngine.'''
    bl_label = "Add Proxy"
    bl_idname = "object.add_proxy"

    type_ = StringProperty()

    def execute(self, context):
        active = bpy.context.active_object

        if (active.type == "MESH"):
            already_exists = False
            for object_ in bpy.data.objects:
                if self.__is_proxy(object_.name):
                    already_exists = True
                    break
            if (not already_exists):
                self.__add_proxy(active)

        message = "Adding {} proxy to active object".format(getattr(self, "type_"))
        self.report({'INFO'}, message)
        return {'FINISHED'}

    def __is_proxy(self, object_name):
        return object_name.endswith("-proxy")

    def __add_proxy(self, object_):
        old_origin = object_.location.copy()
        old_cursor = bpy.context.scene.cursor_location.copy()
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.mesh.primitive_cube_add()
        bound_box = bpy.context.active_object
        bound_box.name = "{}_{}-proxy".format(object_.name,
                                              getattr(self, "type_"))
        bound_box.draw_type = "WIRE"
        bound_box.dimensions = object_.dimensions
        bound_box.location = object_.location
        bound_box.rotation_euler = object_.rotation_euler
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        for group in object_.users_group:
            bpy.ops.object.group_link(group=group.name)

        name = "{}__physProxyNoDraw".format(bound_box.name)
        proxy_material = bpy.data.materials.new(name)
        bound_box.data.materials.append(proxy_material)

        bound_box['phys_proxy'] = getattr(self, "type_")

        bpy.context.scene.cursor_location = old_origin
        bpy.ops.object.select_all(action="DESELECT")
        object_.select = True
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        object_.select = False
        bound_box.select = True
        bpy.context.scene.objects.active = bound_box
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        bpy.context.scene.cursor_location = old_cursor

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH" or context.object.mode != "OBJECT":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


class AddBreakableJoint(bpy.types.Operator):
    '''Click to add a pre-broken breakable joint to current selection.'''
    bl_label = "Add Joint"
    bl_idname = "object.add_joint"

    def execute(self, context):
        return add.add_joint(self, context)
        
    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH" or context.object.mode != "OBJECT":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


class AddBranch(bpy.types.Operator):
    '''Click to add a branch at active vertex or first vertex in a set of vertices.'''
    bl_label = "Add Branch"
    bl_idname = "mesh.add_branch"

    def execute(self, context):
        active_object = bpy.context.scene.objects.active
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_vert_coordinates = get_vertex_data()
        if (selected_vert_coordinates):
            selected_vert = selected_vert_coordinates[0]
            bpy.ops.object.add(
                type='EMPTY',
                view_align=False,
                enter_editmode=False,
                location=(
                    selected_vert[0],
                    selected_vert[1],
                    selected_vert[2]))
            empty_object = bpy.context.active_object
            empty_object.name = name_branch(True)
            bpy.context.scene.objects.active = active_object
            bpy.ops.object.mode_set(mode='EDIT')

            message = "Adding Branch"
            self.report({'INFO'}, message)
            cbPrint(message)

        return {'FINISHED'}

    def invoke(self, context, event):
        if (context.object is None or context.object.type != "MESH" or
                context.object.mode != "EDIT" or not get_vertex_data()):
            self.report({'ERROR'}, "Select a vertex in EDIT mode.")
            return {'FINISHED'}

        return self.execute(context)


class AddBranchJoint(bpy.types.Operator):
    '''Click to add a branch joint at selected vertex or first vertex in a set of vertices.'''
    bl_label = "Add Branch Joint"
    bl_idname = "mesh.add_branch_joint"

    def execute(self, context):
        active_object = bpy.context.scene.objects.active
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_vert_coordinates = get_vertex_data()
        if (selected_vert_coordinates):
            selected_vert = selected_vert_coordinates[0]
            bpy.ops.object.add(
                type='EMPTY',
                view_align=False,
                enter_editmode=False,
                location=(
                    selected_vert[0],
                    selected_vert[1],
                    selected_vert[2]))
            empty_object = bpy.context.active_object
            empty_object.name = name_branch(False)
            bpy.context.scene.objects.active = active_object
            bpy.ops.object.mode_set(mode='EDIT')

            message = "Adding Branch Joint"
            self.report({'INFO'}, message)
            cbPrint(message)

        return {'FINISHED'}

    def invoke(self, context, event):
        if (context.object is None or context.object.type != "MESH" or
                context.object.mode != "EDIT" or not get_vertex_data()):
            self.report({'ERROR'}, "Select a vertex in EDIT mode.")
            return {'FINISHED'}

        return self.execute(context)


def get_vertex_data():
    old_mode = bpy.context.scene.objects.active.mode
    bpy.ops.object.mode_set(mode="OBJECT")
    selected_vert_coordinates = [
        i.co for i in bpy.context.active_object.data.vertices if i.select]
    bpy.ops.object.mode_set(mode=old_mode)

    return selected_vert_coordinates


def name_branch(is_new_branch):
    highest_branch_number = 0
    highest_joint_number = 0
    for object in bpy.context.scene.objects:
        if ((object.type == 'EMPTY') and ("branch" in object.name)):
            branch_components = object.name.split("_")
            if(branch_components):
                branch_name = branch_components[0]
                branch_number = int(branch_name[6:])
                joint_number = int(branch_components[1])
                if (branch_number > highest_branch_number):
                    highest_branch_number = branch_number
                    if (joint_number > highest_joint_number):
                        highest_joint_number = joint_number
    if (highest_branch_number != 0):
        if (is_new_branch):
            return "branch{}_1".format(highest_branch_number + 1)
        else:
            return "branch{}_{}".format(
                    highest_branch_number, highest_joint_number + 1)
    else:
        return "branch1_1"

def get_materials_per_group(group):
    materials = []
    for _objtmp in bpy.data.groups[group].objects:
        for material in _objtmp.data.materials:
            if material is not None:
                if material.name not in materials:
                    materials.append(material.name)
    return materials

class AddMaterial(bpy.types.Operator):
    '''Add material to node'''
    bl_label = "Add Material to Node"
    bl_idname = "object.add_cry_material"
    bl_options = {"REGISTER", "UNDO"}

    material_name = StringProperty(name="Material")

    physics_type = EnumProperty(
        name="Physics",
        items=(
            ("physDefault", "Default", list['physDefault']),
            ("physProxyNoDraw", "Proxy", list['physProxyNoDraw']),
            ("physNoCollide", "Collide", list['physNoCollide']),
            ("physObstruct", "Obstruct", list['physObstruct']),
            ("physNone", "None", list['physNone']),
        ),
        default="physDefault",
    )

    def execute(self, context):
        if bpy.context.selected_objects:
            materials = {}
            for _object in bpy.context.selected_objects:
                if (len(_object.users_group) > 0):
                    # get cryexport group
                    node_name = _object.users_group[0].name
                    # get material for this group
                    if node_name not in materials:
                        index = len(get_materials_per_group(node_name)) + 1
                        #generate new material
                        material = bpy.data.materials.new(
                            "{}__{}__{}__{}".format(
                            node_name.split(".")[0],
                            index, self.material_name, self.physics_type
                            )
                        )
                        materials[node_name] = material
                    _object.data.materials.append(material)
                else:
                    # ignoring object without group
                    cbPrint("Object " + _object.name +
                            " not assigned to any group")
            message = "Assigned material"
        else:
            message = "No Objects Selected"

        self.report({"INFO"}, message)
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "Select one or more objects in OBJECT mode.")
            return {'FINISHED'}

        return context.window_manager.invoke_props_dialog(self)

#------------------------------------------------------------------------------
# (UDP) Inverse Kinematics:
#------------------------------------------------------------------------------

class EditInverseKinematics(bpy.types.Operator):
    '''Edit inverse kinematics properties for selected bone.'''
    bl_label = "Edit Inverse Kinematics of Selected Bone"
    bl_idname = "object.edit_inverse_kinematics"

    info = "Force this bone proxy to be a {} primitive in the engine."

    proxy_type = EnumProperty(
        name="Physic Proxy",
        items=(
            ("box", "Box", info.format('Box')),
            ("cylinder", "Cylinder", info.format('Cylinder')),
            ("capsule", "Capsule", info.format('Capsule')),
            ("sphere", "Sphere", info.format('Sphere'))
        ),
        default="capsule")

    is_rotation_lock = BoolVectorProperty(
        name="Rotation Lock  [X, Y, Z]:",
        description="Bone Rotation Lock X, Y, Z")

    rotation_min = bpy.props.IntVectorProperty(
        name="Rot Limit Min:", description="Bone Rotation Minimum Limit X, Y, Z", default=(
            -180, -180, -180), min=-180, max=0)
    rotation_max = bpy.props.IntVectorProperty(
        name="Rot Limit Max:",
        description="Bone Rotation Maximum Limit X, Y, Z",
        default=(
            180,
            180,
            180),
        min=0,
        max=180)

    bone_spring = FloatVectorProperty(
        name="Spring  [X, Y, Z]:",
        description=desc.list['spring'],
        default=(
            0.0,
            0.0,
            0.0),
        min=0.0,
        max=1.0)

    bone_spring_tension = FloatVectorProperty(
        name="Spring Tension  [X, Y, Z]:",
        description=desc.list['spring'],
        default=(
            1.0,
            1.0,
            1.0),
        min=-3.14159,
        max=3.14159)

    bone_damping = FloatVectorProperty(
        name="Damping  [X, Y, Z]:",
        description=desc.list['damping'],
        default=(
            1.0,
            1.0,
            1.0),
        min=0.0,
        max=1.0)

    bone = None

    def __init__(self):
        armature = bpy.context.scene.objects.active
        if armature is None or armature.type != "ARMATURE":
            return None

        for temp_bone in armature.pose.bones:
            if temp_bone.bone.select:
                self.bone = temp_bone
                break

        if self.bone is None:
            return None

        try:
            self.proxy_type = self.bone['phys_proxy']
        except:
            pass

        self.is_rotation_lock[0] = self.bone.lock_ik_x
        self.is_rotation_lock[1] = self.bone.lock_ik_y
        self.is_rotation_lock[2] = self.bone.lock_ik_z

        self.rotation_min[0] = math.degrees(self.bone.ik_min_x)
        self.rotation_min[1] = math.degrees(self.bone.ik_min_y)
        self.rotation_min[2] = math.degrees(self.bone.ik_min_z)

        self.rotation_max[0] = math.degrees(self.bone.ik_max_x)
        self.rotation_max[1] = math.degrees(self.bone.ik_max_y)
        self.rotation_max[2] = math.degrees(self.bone.ik_max_z)

        try:
            self.bone_spring = self.bone['Spring']
            self.bone_spring_tension = self.bone['Spring Tension']
            self.bone_damping = self.bone['Damping']
        except:
            pass

        return None

    def execute(self, context):
        if self.bone is None:
            cbPrint("Please select a bone in pose mode!")
            return {'FINISHED'}

        self.bone['phys_proxy'] = self.proxy_type

        self.bone.lock_ik_x = self.is_rotation_lock[0]
        self.bone.lock_ik_y = self.is_rotation_lock[1]
        self.bone.lock_ik_z = self.is_rotation_lock[2]

        self.bone.ik_min_x = math.radians(self.rotation_min[0])
        self.bone.ik_min_y = math.radians(self.rotation_min[1])
        self.bone.ik_min_z = math.radians(self.rotation_min[2])

        self.bone.ik_max_x = math.radians(self.rotation_max[0])
        self.bone.ik_max_y = math.radians(self.rotation_max[1])
        self.bone.ik_max_z = math.radians(self.rotation_max[2])

        self.bone['Spring'] = self.bone_spring
        self.bone['Spring Tension'] = self.bone_spring_tension
        self.bone['Damping'] = self.bone_damping

        return {'FINISHED'}

    def invoke(self, context, event):
        if (context.object is None or context.object.type != "ARMATURE" or
                context.object.mode != "POSE" or self.bone is None):
            self.report({'ERROR'}, "Select a bone in POSE mode.")
            return {'FINISHED'}

        return context.window_manager.invoke_props_dialog(self)


#------------------------------------------------------------------------------
# (UDP) Physics Proxy:
#------------------------------------------------------------------------------

class EditPhysicProxy(bpy.types.Operator):
    '''Edit Physic Proxy Properties for selected object.'''
    bl_label = "Edit physic proxy properties of active object."
    bl_idname = "object.edit_physics_proxy"

    ''' "phys_proxy", "colltype_player", "no_explosion_occlusion", "wheel" '''

    is_proxy = BoolProperty(
        name="Use Physic Proxy",
        description="If you want to use physic proxy properties. Please enable this.")

    info = "Force this proxy to be a {} primitive in the engine."

    proxy_type = EnumProperty(
        name="Physic Proxy",
        items=(
            ("box", "Box", info.format('Box')),
            ("cylinder", "Cylinder", info.format('Cylinder')),
            ("capsule", "Capsule", info.format('Capsule')),
            ("sphere", "Sphere", info.format('Sphere')),
            ("notaprim", "Not a primitive", desc.list['notaprim'])
        ),
        default="box")

    no_exp_occlusion = BoolProperty(name="No Explosion Occlusion",
                                    description=desc.list['no_exp_occlusion'])
    colltype_player = BoolProperty(name="Colltype Player",
                                   description=desc.list['colltpye_player'])
    wheel = BoolProperty(name="Wheel", description="Wheel for vehicles.")

    object_ = None

    def __init__(self):
        self.object_ = bpy.context.scene.objects.active

        if self.object_ is None:
            return None

        self.proxy_type, self.is_proxy = add.get_udp(
            self.object_, "phys_proxy", self.proxy_type, self.is_proxy)
        self.no_exp_occlusion = add.get_udp(
            self.object_,
            "no_explosion_occlusion",
            self.no_exp_occlusion)
        self.colltype_player = add.get_udp(
            self.object_, "colltype_player", self.colltype_player)
        self.wheel = add.get_udp(self.object_, "wheel", self.wheel)

        return None

    def execute(self, context):
        if self.object_ is None:
            cbPrint("Please select a object.")
            return {'FINISHED'}

        add.edit_udp(
            self.object_,
            "phys_proxy",
            self.proxy_type,
            self.is_proxy)
        add.edit_udp(
            self.object_,
            "no_explosion_occlusion",
            "no_explosion_occlusion",
            self.no_exp_occlusion)
        add.edit_udp(
            self.object_,
            "colltype_player",
            "colltype_player",
            self.colltype_player)
        add.edit_udp(self.object_, "wheel", "wheel", self.wheel)

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return context.window_manager.invoke_props_dialog(self)


#------------------------------------------------------------------------------
# (UDP) Render Mesh:
#------------------------------------------------------------------------------

class EditRenderMesh(bpy.types.Operator):
    '''Edit Render Mesh Properties for selected object.'''
    bl_label = "Edit render mesh properties of active object."
    bl_idname = "object.edit_render_mesh"

    ''' "entity", "mass", "density", "pieces", "dynamic", "no_hit_refinement" '''

    is_entity = BoolProperty(name="Entity", description=desc.list['is_entity'])

    info = "If you want to use {} property. Please enable this."

    is_mass = BoolProperty(name="Use Mass", description=info.format('mass'))
    mass = FloatProperty(name="Mass", description=desc.list['mass'])

    is_density = BoolProperty(
        name="Use Density",
        description=info.format('density'))
    density = FloatProperty(name="Density", description=desc.list['density'])

    is_pieces = BoolProperty(
        name="Use Pieces",
        description=info.format('pieces'))
    pieces = FloatProperty(name="Pieces", description=desc.list['pieces'])

    is_dynamic = BoolProperty(
        name="Dynamic",
        description=desc.list['is_dynamic'])

    no_hit_refinement = BoolProperty(
        name="No Hit Refinement",
        description=desc.list['no_hit_refinement'])

    other_rendermesh = BoolProperty(name="Other Rendermesh",
                                    description=desc.list['other_rendermesh'])

    object_ = None

    def __init__(self):
        self.object_ = bpy.context.scene.objects.active

        if self.object_ is None:
            return None

        self.mass, self.is_mass = add.get_udp(self.object_,
                                              "mass", self.mass, self.is_mass)
        self.density, self.is_density = add.get_udp(
            self.object_, "density", self.density, self.is_density)
        self.pieces, self.is_pieces = add.get_udp(
            self.object_, "pieces", self.pieces, self.is_pieces)
        self.no_hit_refinement = add.get_udp(
            self.object_, "no_hit_refinement", self.no_hit_refinement)
        self.other_rendermesh = add.get_udp(
            self.object_, "other_rendermesh", self.other_rendermesh)

        self.is_entity = add.get_udp(self.object_, "entity", self.is_entity)
        self.is_dynamic = add.get_udp(self.object_, "dynamic", self.is_dynamic)

        return None

    def execute(self, context):
        if self.object_ is None:
            cbPrint("Please select a object.")
            return {'FINISHED'}

        add.edit_udp(self.object_, "entity", "entity", self.is_entity)
        add.edit_udp(self.object_, "mass", self.mass, self.is_mass)
        add.edit_udp(self.object_, "density", self.density, self.is_density)
        add.edit_udp(self.object_, "pieces", self.pieces, self.is_pieces)
        add.edit_udp(self.object_, "dynamic", "dynamic", self.is_dynamic)
        add.edit_udp(
            self.object_,
            "no_hit_refinement",
            "no_hit_refinement",
            self.no_hit_refinement)
        add.edit_udp(
            self.object_,
            "other_rendermesh",
            "other_rendermesh",
            self.other_rendermesh)

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return context.window_manager.invoke_props_dialog(self)


#------------------------------------------------------------------------------
# (UDP) Joint Node:
#------------------------------------------------------------------------------

class EditJointNode(bpy.types.Operator):
    '''Edit Joint Node Properties for selected joint.'''
    bl_label = "Edit joint node properties of active object."
    bl_idname = "object.edit_joint_node"

    ''' "limit", "bend", "twist", "pull", "push",
        "shift", "player_can_break", "gameplay_critical" '''

    info = "If you want to use {} joint property. Please enable this."

    is_limit = BoolProperty(name="Use Limit Property",
                            description=info.format('limit'))
    limit = FloatProperty(name="Limit", description=desc.list['limit'])

    is_bend = BoolProperty(name="Use Bend Property",
                           description=info.format('bend'))
    bend = FloatProperty(name="Bend", description=desc.list['bend'])

    is_twist = BoolProperty(name="Use Twist Property",
                            description=info.format('twist'))
    twist = FloatProperty(name="Twist", description=desc.list['twist'])

    is_pull = BoolProperty(name="Use Pull Property",
                           description=info.format('pull'))
    pull = FloatProperty(name="Pull", description=desc.list['pull'])

    is_push = BoolProperty(name="Use Psuh Property",
                           description=info.format('push'))
    push = FloatProperty(name="Push", description=desc.list['push'])

    is_shift = BoolProperty(name="Use Shift Property",
                            description=info.format('shift'))
    shift = FloatProperty(name="Shift", description=desc.list['shift'])

    player_can_break = BoolProperty(name="Player can break",
                                    description=desc.list['player_can_break'])

    gameplay_critical = BoolProperty(
        name="Gameplay critical",
        description=desc.list['gameplay_critical'])

    object_ = None

    def __init__(self):
        self.object_ = bpy.context.scene.objects.active

        if self.object_ is None:
            return None

        self.limit, self.is_limit = add.get_udp(
            self.object_, "limit", self.limit, self.is_limit)
        self.bend, self.is_bend = add.get_udp(
            self.object_, "bend", self.bend, self.is_bend)
        self.twist, self.is_twist = add.get_udp(
            self.object_, "twist", self.twist, self.is_twist)
        self.pull, self.is_pull = add.get_udp(
            self.object_, "pull", self.pull, self.is_pull)
        self.push, self.is_push = add.get_udp(
            self.object_, "push", self.push, self.is_push)
        self.shift, self.is_shift = add.get_udp(
            self.object_, "shift", self.shift, self.is_shift)
        self.player_can_break = add.get_udp(
            self.object_, "player_can_break", self.player_can_break)
        self.gameplay_critical = add.get_udp(
            self.object_, "gameplay_critical", self.gameplay_critical)

        return None

    def execute(self, context):
        if self.object_ is None:
            cbPrint("Please select a object.")
            return {'FINISHED'}

        add.edit_udp(self.object_, "limit", self.limit, self.is_limit)
        add.edit_udp(self.object_, "bend", self.bend, self.is_bend)
        add.edit_udp(self.object_, "twist", self.twist, self.is_twist)
        add.edit_udp(self.object_, "pull", self.pull, self.is_pull)
        add.edit_udp(self.object_, "push", self.push, self.is_push)
        add.edit_udp(self.object_, "shift", self.shift, self.is_shift)
        add.edit_udp(
            self.object_,
            "player_can_break",
            "player_can_break",
            self.player_can_break)
        add.edit_udp(
            self.object_,
            "gameplay_critical",
            "gameplay_critical",
            self.gameplay_critical)

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return context.window_manager.invoke_props_dialog(self)


#------------------------------------------------------------------------------
# (UDP) Deformable:
#------------------------------------------------------------------------------

class EditDeformable(bpy.types.Operator):
    '''Edit Deformable Properties for selected skeleton mesh.'''
    bl_label = "Edit deformable properties of active skeleton mesh."
    bl_idname = "object.edit_deformable"

    ''' "stiffness", "hardness", "max_stretch", "max_impulse",
        "skin_dist", "thickness", "explosion_scale", "notaprim" '''

    info = "If you want to use {} deform property. Please enable this."

    is_stiffness = BoolProperty(name="Use Stiffness",
                                description=info.format('stiffness'))
    stiffness = FloatProperty(name="Stiffness",
                              description=desc.list['stiffness'], default=10.0)

    is_hardness = BoolProperty(name="Use Hardness",
                               description=info.format('hardness'))
    hardness = FloatProperty(name="Hardness",
                             description=desc.list['hardness'], default=10.0)

    is_max_stretch = BoolProperty(name="Use Max Stretch",
                                  description=info.format('max stretch'))
    max_stretch = FloatProperty(
        name="Max Stretch",
        description=desc.list['max_stretch'],
        default=0.01)

    is_max_impulse = BoolProperty(name="Use Max Impulse",
                                  description=info.format('max impulse'))
    max_impulse = FloatProperty(name="Max Impulse",
                                description=desc.list['max_impulse'])

    is_skin_dist = BoolProperty(name="Use Skin Dist",
                                description=info.format('skin dist'))
    skin_dist = FloatProperty(name="Skin Dist",
                              description=desc.list['skin_dist'])

    is_thickness = BoolProperty(name="Use Thickness",
                                description=info.format('thickness'))
    thickness = FloatProperty(name="Thickness",
                              description=desc.list['thickness'])

    is_explosion_scale = BoolProperty(
        name="Use Explosion Scale",
        description=info.format('explosion scale'))
    explosion_scale = FloatProperty(name="Explosion Scale",
                                    description=desc.list['explosion_scale'])

    notaprim = BoolProperty(name="Is not a primitive",
                            description=desc.list['notaprim'])

    object_ = None

    def __init__(self):
        self.object_ = bpy.context.scene.objects.active

        if self.object_ is None:
            return None

        self.stiffness, self.is_stiffness = add.get_udp(
            self.object_, "stiffness", self.stiffness, self.is_stiffness)
        self.hardness, self.is_hardness = add.get_udp(
            self.object_, "hardness", self.hardness, self.is_hardness)
        self.max_stretch, self.is_max_stretch = add.get_udp(
            self.object_, "max_stretch", self.max_stretch, self.is_max_stretch)
        self.max_impulse, self.is_max_impulse = add.get_udp(
            self.object_, "max_impulse", self.max_impulse, self.is_max_impulse)
        self.skin_dist, self.is_skin_dist = add.get_udp(
            self.object_, "skin_dist", self.skin_dist, self.is_skin_dist)
        self.thickness, self.is_thickness = add.get_udp(
            self.object_, "thickness", self.thickness, self.is_thickness)
        self.explosion_scale, self.is_explosion_scale = add.get_udp(
            self.object_, "explosion_scale", self.explosion_scale, self.is_explosion_scale)

        self.notaprim = add.get_udp(self.object_, "notaprim", self.notaprim)

        return None

    def execute(self, context):
        if self.object_ is None:
            cbPrint("Please select a object.")
            return {'FINISHED'}

        add.edit_udp(
            self.object_,
            "stiffness",
            self.stiffness,
            self.is_stiffness)
        add.edit_udp(self.object_, "hardness", self.hardness, self.is_hardness)
        add.edit_udp(
            self.object_,
            "max_stretch",
            self.max_stretch,
            self.is_max_stretch)
        add.edit_udp(
            self.object_,
            "max_impulse",
            self.max_impulse,
            self.is_max_impulse)
        add.edit_udp(
            self.object_,
            "skin_dist",
            self.skin_dist,
            self.is_skin_dist)
        add.edit_udp(
            self.object_,
            "thickness",
            self.thickness,
            self.is_thickness)
        add.edit_udp(
            self.object_,
            "explosion_scale",
            self.explosion_scale,
            self.is_explosion_scale)
        add.edit_udp(self.object_, "notaprim", "notaprim", self.notaprim)

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return context.window_manager.invoke_props_dialog(self)


#------------------------------------------------------------------------------
# (UDP) Vehicle:
#------------------------------------------------------------------------------

class FixWheelTransforms(bpy.types.Operator):
    bl_label = "Fix Wheel Transforms"
    bl_idname = "object.fix_wheel_transforms"

    def execute(self, context):
        ob = bpy.context.active_object
        ob.location.x = (ob.bound_box[0][0] + ob.bound_box[1][0]) / 2.0
        ob.location.y = (ob.bound_box[2][0] + ob.bound_box[3][0]) / 2.0
        ob.location.z = (ob.bound_box[4][0] + ob.bound_box[5][0]) / 2.0

        return {'FINISHED'}


#------------------------------------------------------------------------------
# Material Physics:
#------------------------------------------------------------------------------

class AddMaterialPhysDefault(bpy.types.Operator):
    '''__physDefault will be added to the material name.'''
    bl_label = "__physDefault"
    bl_idname = "material.add_phys_default"

    def execute(self, context):
        message = "Adding __physDefault"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_material(self, context, self.bl_label)


class AddMaterialPhysProxyNoDraw(bpy.types.Operator):
    '''__physProxyNoDraw will be added to the material name.'''
    bl_label = "__physProxyNoDraw"
    bl_idname = "material.add_phys_proxy_no_draw"

    def execute(self, context):
        message = "Adding __physProxyNoDraw"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_material(self, context, self.bl_label)


class AddMaterialPhysNone(bpy.types.Operator):
    '''__physNone will be added to the material name.'''
    bl_label = "__physNone"
    bl_idname = "material.add_phys_none"

    def execute(self, context):
        message = "Adding __physNone"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_material(self, context, self.bl_label)


class AddMaterialPhysObstruct(bpy.types.Operator):
    '''__physObstruct will be added to the material name.'''
    bl_label = "__physObstruct"
    bl_idname = "material.add_phys_obstruct"

    def execute(self, context):
        return add.add_phys_material(self, context, self.bl_label)


class AddMaterialPhysNoCollide(bpy.types.Operator):
    '''__physNoCollide will be added to the material name.'''
    bl_label = "__physNoCollide"
    bl_idname = "material.add_phys_no_collide"

    def execute(self, context):
        message = "Adding __physNoCollide"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_material(self, context, self.bl_label)


#------------------------------------------------------------------------------
# Mesh Repair Tools:
#------------------------------------------------------------------------------

class FindDegenerateFaces(bpy.types.Operator):
    '''Select the object to test in object mode with nothing selected in \
it's mesh before running this.'''
    bl_label = "Find Degenerate Faces"
    bl_idname = "object.find_degenerate_faces"

    # Minimum face area to be considered non-degenerate
    area_epsilon = 0.000001

    def execute(self, context):
        # Deselect any vertices prevously selected in Edit mode
        saved_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        # Vertices data should be actually manipulated in Object mode
        # to be displayed in Edit mode correctly.
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = bpy.context.active_object.data

        vert_list = [vert for vert in mesh.vertices]
        context.tool_settings.mesh_select_mode = (True, False, False)
        cbPrint("Locating degenerate faces.")
        degenerate_count = 0

        for poly in mesh.polygons:
            if poly.area < self.area_epsilon:
                cbPrint("Found a degenerate face.")
                degenerate_count += 1

                for v in poly.vertices:
                    cbPrint("Selecting face vertices.")
                    vert_list[v].select = True

        if degenerate_count > 0:
            bpy.ops.object.mode_set(mode='EDIT')
            self.report({'WARNING'},
                        "Found {} degenerate faces".format(degenerate_count))
        else:
            self.report({'INFO'}, "No degenerate faces found")
            # Restore the original mode
            bpy.ops.object.mode_set(mode=saved_mode)

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


class FindMultifaceLines(bpy.types.Operator):
    '''Select the object to test in object mode with nothing selected in \
it's mesh before running this.'''
    bl_label = "Find Lines with 3+ Faces."
    bl_idname = "mesh.find_multiface_lines"

    def execute(self, context):
        mesh = bpy.context.active_object.data
        vert_list = [vert for vert in mesh.vertices]
        context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.object.mode_set(mode='OBJECT')
        cbPrint("Locating degenerate faces.")
        for i in mesh.edges:
            counter = 0
            for polygon in mesh.polygons:
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

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


class FindWeightless(bpy.types.Operator):
    '''Select the object in object mode with nothing in its mesh selected \
before running this'''
    bl_label = "Find Weightless Vertices"
    bl_idname = "mesh.find_weightless"

    # Minimum net weight to be considered non-weightless
    weight_epsilon = 0.0001

    # Weightless: a vertex not belonging to any groups or with a net weight of
    # 0
    def execute(self, context):
        object_ = bpy.context.active_object
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        if object_.type == "MESH":
            for v in object_.data.vertices:
                if (not v.groups):
                    v.select = True
                else:
                    weight = 0
                    for g in v.groups:
                        weight += g.weight
                    if (weight < self.weight_epsilon):
                        v.select = True
        object_.data.update()
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH":
            self.report({'ERROR'}, "Select a mesh in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


class RemoveAllWeight(bpy.types.Operator):
    '''Select vertices from which to remove weight in edit mode.'''
    bl_label = "Remove All Weight from Selected Vertices"
    bl_idname = "mesh.remove_weight"

    def execute(self, context):
        object_ = bpy.context.active_object
        if object_.type == 'MESH':
            verts = []
            for v in object_.data.vertices:
                if v.select:
                    verts.append(v)
            for v in verts:
                for g in v.groups:
                    g.weight = 0
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object is None or context.object.type != "MESH" or context.object.mode != "EDIT":
            self.report({'ERROR'}, "Select one or more vertices in EDIT mode.")
            return {'FINISHED'}

        return self.execute(context)


class FindNoUVs(bpy.types.Operator):
    '''Use this with no objects selected in object mode \
to find all items without UVs.'''
    bl_label = "Find All Objects with No UV's"
    bl_idname = "scene.find_no_uvs"

    def execute(self, context):
        for object_ in bpy.data.objects:
            object_.select = False

        for object_ in bpy.context.selectable_objects:
            if object_.type == 'MESH' and not object_.data.uv_textures:
                object_.select = True

        return {'FINISHED'}


class AddUVTexture(bpy.types.Operator):
    '''Add UVs to all meshes without UVs.'''
    bl_label = "Add UV's to Objects"
    bl_idname = "mesh.add_uv_texture"

    def execute(self, context):
        for object_ in bpy.data.objects:
            if object_.type == 'MESH':
                uv = False
                for i in object_.data.uv_textures:
                    uv = True
                    break
                if not uv:
                    bpy.context.scene.objects.active = object_
                    bpy.ops.mesh.uv_texture_add()
                    message = "Added UV map to {}".format(object_.name)
                    self.report({'INFO'}, message)
                    cbPrint(message)

        return {'FINISHED'}


#------------------------------------------------------------------------------
# Bone Utilities:
#------------------------------------------------------------------------------

class AddRootBone(bpy.types.Operator):
    '''Click to add a root bone to the active armature.'''
    bl_label = "Add Root Bone"
    bl_idname = "armature.add_root_bone"

    def execute(self, context):
        cbPrint("TEST")
        active = bpy.context.active_object
        if active is not None:
            if active.type == "ARMATURE":
                if utils.count_root_bones(active) == 1:
                    root_bone = utils.get_root_bone(active)
                    loc = root_bone.head
                    if loc.x == 0 and loc.y == 0 and loc.z == 0:
                        message = "Root bone already exists."
                        self.report({'INFO'}, message)
                        return {'FINISHED'}
                message = "Adding root bone to armature."
                old_mode = bpy.context.object.mode
                bpy.ops.object.mode_set(mode="EDIT")
                edit_bones = active.data.edit_bones
                bpy.ops.armature.bone_primitive_add(name="root")
                root_bone = edit_bones["root"]
                bpy.ops.armature.select_all(action="DESELECT")
                for edit_bone in edit_bones:
                    if edit_bone.parent is None:
                        edit_bone.parent = root_bone
                bpy.ops.object.mode_set(mode="OBJECT")
            else:
                message = "Object is not an armature."
        else:
            message = "No Object Selected."
        self.report({'INFO'}, message)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        if context.object is None or context.object.type != "ARMATURE":
            self.report({'ERROR'}, "Select one or more vertices in EDIT mode.")
            return {'FINISHED'}
            
        return self.execute(context)


class AddBoneGeometry(bpy.types.Operator):
    '''Add BoneGeometry for bones in selected armatures.'''
    bl_label = "Add BoneGeometry"
    bl_idname = "armature.add_bone_geometry"
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

    def execute(self, context):
        verts_loc, faces = add_bone_geometry()

        for object_ in bpy.context.selected_objects:
            if (object_.type == 'ARMATURE' and not object_.name.endswith("_Phys")):
                for bone in object_.data.bones:
                    mesh = bpy.data.meshes.new(
                        "{}_boneGeometry".format(bone.name)
                    )
                    bm = bmesh.new()

                    for v_co in verts_loc:
                        bm.verts.new(v_co)

                    if hasattr(bm.verts, "ensure_lookup_table"):
                        bm.verts.ensure_lookup_table()

                    for f_idx in faces:
                        bm.faces.new([bm.verts[i] for i in f_idx])

                    bm.to_mesh(mesh)
                    mesh.update()

                    bmatrix = bone.head_local
                    self.location[0] = bmatrix[0]
                    self.location[1] = bmatrix[1]
                    self.location[2] = bmatrix[2]

                    # Add the mesh as an object into the scene
                    # with this utility module
                    from bpy_extras import object_utils
                    object_utils.object_data_add(
                        context, mesh, operator=self
                    )
                    bpy.ops.mesh.uv_texture_add()

        return {'FINISHED'}

    def invoke(self, context, event):
        has_armature = False
        for object_ in context.selected_objects:
            if object_.type == "ARMATURE":
                has_armature = True
                break

        if not has_armature:
            self.report({'ERROR'}, "Select one or more armatures in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


def add_bone_geometry():
    """
    This function takes inputs and returns vertex and face arrays.
    No actual mesh data creation is done here.
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


class RemoveBoneGeometry(bpy.types.Operator):
    '''Remove all bone geometry from the scene.'''
    bl_label = "Remove BoneGeometry"
    bl_idname = "armature.remove_bone_geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        utils.deselect_all()

        for object_ in bpy.context.scene.objects:
            if (object_.type == "MESH" and
                    object_.name.endswith("_boneGeometry")):
                object_.select = True

        bpy.ops.object.delete()

        return {'FINISHED'}


class RenamePhysBones(bpy.types.Operator):
    '''Renames bones with _Phys extension.'''
    bl_label = "Rename Phys Bones"
    bl_idname = "armature.rename_phys_bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for object_ in bpy.context.selected_objects:
            if (object_.type == 'ARMATURE'):
                object_.name = "{}_Phys".format(object_.name)
                for bone in object_.data.bones:
                    if not bone.name.endswith("_Phys"):
                        bone.name = "{}_Phys".format(bone.name)

        return {'FINISHED'}
        
    def invoke(self, context, event):
        has_armature = False
        for object_ in context.selected_objects:
            if object_.type == "ARMATURE":
                has_armature = True
                break

        if not has_armature:
            self.report({'ERROR'}, "Select one or more armatures in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


class ApplyAnimationScale(bpy.types.Operator):
    '''Select to apply animation skeleton scaling and rotation'''
    bl_label = "Apply Animation Scaling"
    bl_idname = "ops.apply_animation_scaling"

    def execute(self, context):
        utils.apply_animation_scale(bpy.context.scene.objects.active)
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object is None or context.object.type != "ARMATURE" or context.object.mode != "OBJECT":
            self.report({'ERROR'}, "Select an armature in OBJECT mode.")
            return {'FINISHED'}

        return self.execute(context)


class RemoveFakebones(bpy.types.Operator):
    '''(Deprecated) Remove all fakebones for backward compatibility'''
    bl_label = "Remove All FakeBones"
    bl_idname = "scene.remove_fake_bones"

    def execute(self, context):
        utils.remove_fakebones()
        return {'FINISHED'}


#------------------------------------------------------------------------------
# Export Handler:
#------------------------------------------------------------------------------

class Export(bpy.types.Operator, ExportHelper):
    '''Select to export to game.'''
    bl_label = "Export to Game"
    bl_idname = "scene.export_to_game"
    filename_ext = ".dae"
    filter_glob = StringProperty(default="*.dae", options={'HIDDEN'})

    apply_modifiers = BoolProperty(
        name="Apply Modifiers",
        description="Apply all modifiers before exporting.",
        default=True,
    )
    do_not_merge = BoolProperty(
        name="Do Not Merge Nodes",
        description="Generally a good idea.",
        default=True,
    )
    do_materials = BoolProperty(
        name="Do Materials",
        description="Create MTL files for materials.",
        default=False,
    )
    do_textures = BoolProperty(
        name="Do Textures",
        description="Converts source textures to DDS while exporting materials.",
        default=False,
    )
    make_chrparams = BoolProperty(
        name="Make CHRPARAMS File",
        description="Create a base CHRPARAMS file for character animations.",
        default=False,
    )
    make_cdf = BoolProperty(
        name="Make CDF File",
        description="Create a base CDF file for character attachments.",
        default=False,
    )
    include_ik = BoolProperty(
        name="Include IK in Character",
        description="Add IK to the physics skeleton upon export.",
        default=False,
    )
    convert_space = BoolProperty(
        name="Convert to Whitespaces",
        description="Convert double underscores to whitespaces in skeleton.",
        default=False,
    )
    fix_weights = BoolProperty(
        name="Fix Weights",
        description="For use with .chr files. Generally a good idea.",
        default=False,
    )
    average_planar = BoolProperty(
        name="Average Planar Face Normals",
        description="Align face normals within 1 degree of each other.",
        default=False,
    )
    make_layer = BoolProperty(
        name="Make LYR File",
        description="Makes a LYR to reassemble your scene in CryEngine.",
        default=False,
    )
    disable_rc = BoolProperty(
        name="Disable RC",
        description="Do not run the resource compiler.",
        default=False,
    )
    save_dae = BoolProperty(
        name="Save DAE File",
        description="Save the DAE file for developing purposes.",
        default=False,
    )
    save_tiffs = BoolProperty(
        name="Save TIFFs",
        description="Saves TIFF images that are generated during conversion to DDS.",
        default=False,
    )
    run_in_profiler = BoolProperty(
        name="Profile CryBlend",
        description="Select only if you want to profile CryBlend.",
        default=False,
    )

    class Config:

        def __init__(self, config):
            attributes = (
                'filepath',
                'apply_modifiers',
                'do_not_merge',
                'do_materials',
                'do_textures',
                'make_chrparams',
                'make_cdf',
                'include_ik',
                'convert_space',
                'fix_weights',
                'average_planar',
                'make_layer',
                'disable_rc',
                'save_dae',
                'save_tiffs',
                'run_in_profiler'
            )

            for attribute in attributes:
                setattr(self, attribute, getattr(config, attribute))

            setattr(self, 'cryblend_version', VERSION)
            setattr(self, 'rc_path', Configuration.rc_path)
            setattr(self, 'texture_rc_path', Configuration.texture_rc_path)
            setattr(self, 'texture_dir', Configuration.texture_dir)

    def execute(self, context):
        cbPrint(Configuration.rc_path, 'debug')
        try:
            config = Export.Config(config=self)

            if self.run_in_profiler:
                import cProfile
                cProfile.runctx('export.save(config)', {},
                                {'export': export, 'config': config})
            else:
                export.save(config)

            self.filepath = '//'

        except exceptions.CryBlendException as exception:
            cbPrint(exception.what(), 'error')
            bpy.ops.screen.display_error(
                'INVOKE_DEFAULT', message=exception.what())

        return {'FINISHED'}

    def invoke(self, context, event):
        if not Configuration.configured():
            self.report({'ERROR'}, "No RC found.")
            return {'FINISHED'}

        if not utils.get_export_nodes():
            self.report({'ERROR'}, "No export nodes found.")
            return {'FINISHED'}

        return ExportHelper.invoke(self, context, event)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        box = col.box()
        box.label("General", icon="WORLD")
        box.prop(self, "apply_modifiers")
        box.prop(self, "do_not_merge")

        box = col.box()
        box.label("Material & Texture", icon="TEXTURE")
        box.prop(self, "do_materials")
        box.prop(self, "do_textures")

        box = col.box()
        box.label("Character", icon="ARMATURE_DATA")
        box.prop(self, "make_chrparams")
        box.prop(self, "make_cdf")
        box.prop(self, "include_ik")
        box.prop(self, "convert_space")

        box = col.box()
        box.label("Corrective", icon="BRUSH_DATA")
        box.prop(self, "fix_weights")
        box.prop(self, "average_planar")

        box = col.box()
        box.label("CryEngine Editor", icon="OOPS")
        box.prop(self, "make_layer")

        box = col.box()
        box.label("Developer Tools", icon="MODIFIER")
        box.prop(self, "disable_rc")
        box.prop(self, "save_dae")
        box.prop(self, "save_tiffs")
        box.prop(self, "run_in_profiler")


class ErrorHandler(bpy.types.Operator):
    bl_label = "Error:"
    bl_idname = "screen.display_error"

    message = bpy.props.StringProperty()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(self.bl_label, icon='ERROR')
        col.split()
        multiline_label(col, self.message)
        col.split()
        col.split(0.2)


def multiline_label(col, text):
    for line in text.splitlines():
        row = col.split()
        row.label(line)


#------------------------------------------------------------------------------
# CryBlend Tab:
#------------------------------------------------------------------------------

class PropPanel():
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render_layer"
    COMPAT_ENGINES = {"BLENDER_RENDER"}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene and (scene.render.engine in cls.COMPAT_ENGINES)


class View3DPanel():
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "CryBlend"


class ExportUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Export Utilities"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label("Export Nodes", icon="GROUP")
        col.separator()
        row = col.row(align=True)
        row.operator("object.add_cry_export_node", text="Add Export Node")
        col.operator(
            "object.selected_to_cry_export_nodes",
            text="Export Nodes from Objects")
        col.separator()
        col.operator("object.apply_transforms", text="Apply All Transforms")


class CryUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Cry Utilities"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label("Material:", icon="MATERIAL_DATA")
        col.separator()
        col.operator("object.add_cry_material", text="Add Material")
        col.separator()

        col.label("Add Physics Proxy", icon="ROTATE")
        col.separator()
        row = col.row(align=True)
        add_box_proxy = row.operator("object.add_proxy", text="Box")
        add_box_proxy.type_ = "box"
        add_capsule_proxy = row.operator("object.add_proxy", text="Capsule")
        add_capsule_proxy.type_ = "capsule"

        row = col.row(align=True)
        add_cylinder_proxy = row.operator("object.add_proxy", text="Cylinder")
        add_cylinder_proxy.type_ = "cylinder"
        add_sphere_proxy = row.operator("object.add_proxy", text="Sphere")
        add_sphere_proxy.type_ = "sphere"
        col.separator()

        col.label("Breakables:", icon="PARTICLES")
        col.separator()
        col.operator("object.add_joint", text="Add Joint")
        col.separator()

        col.label("Touch Bending:", icon="MOD_SIMPLEDEFORM")
        col.separator()
        col.operator("mesh.add_branch", text="Add Branch")
        col.operator("mesh.add_branch_joint", text="Add Branch Joint")


class BoneUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Bone Utilities"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label("Skeleton", icon="ARMATURE_DATA")
        col.separator()
        col.operator("armature.add_root_bone", text="Add Root Bone")
        col.operator(
            "ops.apply_animation_scaling",
            text="Apply Animation Scaling")
        col.separator()

        col.label(text="Bone", icon="BONE_DATA")
        col.separator()
        col.operator(
            "object.edit_inverse_kinematics",
            text="Edit Inverse Kinematics")
        col.operator("scene.remove_fake_bones", text="Remove Old Fakebones")
        col.separator()

        col.label("Physics", icon="PHYSICS")
        col.separator()
        col.operator("armature.add_bone_geometry", text="Add Bone Geometry")
        col.operator(
            "armature.remove_bone_geometry",
            text="Remove Bone Geometry")
        col.operator("armature.rename_phys_bones", text="Rename Phys Bones")


class MeshUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Mesh Utilities"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="Weight Repair", icon="WPAINT_HLT")
        col.separator()
        col.operator("mesh.find_weightless", text="Find Weightless")
        col.operator("mesh.remove_weight", text="Remove Weight")
        col.separator()

        col.label(text="Mesh Repair", icon='ZOOM_ALL')
        col.separator()
        col.operator("object.find_degenerate_faces", text="Find Degenerate")
        col.operator("mesh.find_multiface_lines", text="Find Multi-face")
        col.separator()

        col.label(text="UV Repair", icon="UV_FACESEL")
        col.separator()
        col.operator("scene.find_no_uvs", text="Find All Objects with No UV's")
        col.operator("mesh.add_uv_texture", text="Add UV's to Objects")


class CustomPropertiesPanel(View3DPanel, Panel):
    bl_label = "Custom Properties"

    def draw(self, context):
        layout = self.layout

        layout.label("Properties:", icon="SCRIPT")
        layout.menu("menu.UDP", text="User Defined Properties")


class ConfigurationsPanel(View3DPanel, Panel):
    bl_label = "Configurations"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label("Configure", icon="NEWFOLDER")
        col.separator()
        col.operator("file.find_rc", text="Find RC")
        col.operator(
            "file.find_rc_for_texture_conversion",
            text="Find Texture RC")
        col.separator()
        col.operator("file.select_texture_dir", text="Select Textures Folder")


#------------------------------------------------------------------------------
# CryBlend Menu:
#------------------------------------------------------------------------------

class CryBlendMainMenu(bpy.types.Menu):
    bl_label = 'CryBlend'
    bl_idname = 'view3d.cryblend_main_menu'

    def draw(self, context):
        layout = self.layout

        # version number
        layout.label(text='v{}'.format(VERSION))
        if not Configuration.configured():
            layout.label(text="No RC found.", icon='ERROR')
        layout.separator()

        # layout.operator("open_donate.wp", icon='FORCE_DRAG')
        layout.operator(
            "object.add_cry_export_node",
            text="Add Export Node",
            icon="GROUP")
        layout.operator(
            "object.selected_to_cry_export_nodes",
            text="Export Nodes from Objects")
        layout.separator()
        layout.operator(
            "object.apply_transforms",
            text="Apply All Transforms",
            icon="MESH_DATA")
        layout.separator()
        layout.operator(
            "object.add_cry_material",
            text="Add Material",
            icon="MATERIAL_DATA")
        layout.separator()

        layout.menu("menu.add_physics_proxy", icon="ROTATE")
        layout.separator()
        layout.menu(CryUtilitiesMenu.bl_idname, icon='OUTLINER_OB_EMPTY')
        layout.separator()
        layout.menu(BoneUtilitiesMenu.bl_idname, icon='BONE_DATA')
        layout.separator()
        layout.menu(MeshUtilitiesMenu.bl_idname, icon='MESH_CUBE')
        layout.separator()
        layout.menu(CustomPropertiesMenu.bl_idname, icon='SCRIPT')
        layout.separator()
        layout.menu(ConfigurationsMenu.bl_idname, icon='NEWFOLDER')

        layout.separator()
        layout.separator()
        layout.operator("scene.export_to_game", icon="GAME")


class AddPhysicsProxyMenu(bpy.types.Menu):
    bl_label = "Add Physics Proxy"
    bl_idname = "menu.add_physics_proxy"

    def draw(self, context):
        layout = self.layout

        layout.label("Proxies")
        add_box_proxy = layout.operator(
            "object.add_proxy", text="Box", icon="META_CUBE")
        add_box_proxy.type_ = "box"
        add_capsule_proxy = layout.operator(
            "object.add_proxy", text="Capsule", icon="META_ELLIPSOID")
        add_capsule_proxy.type_ = "capsule"
        add_cylinder_proxy = layout.operator(
            "object.add_proxy", text="Cylinder", icon="META_CAPSULE")
        add_cylinder_proxy.type_ = "cylinder"
        add_sphere_proxy = layout.operator(
            "object.add_proxy", text="Sphere", icon="META_BALL")
        add_sphere_proxy.type_ = "sphere"


class CryUtilitiesMenu(bpy.types.Menu):
    bl_label = "Cry Utilities"
    bl_idname = "view3d.cry_utilities"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Breakables")
        layout.operator("object.add_joint", text="Add Joint", icon="PARTICLES")
        layout.separator()

        layout.label(text="Touch Bending")
        layout.operator(
            "mesh.add_branch",
            text="Add Branch",
            icon='MOD_SIMPLEDEFORM')
        layout.operator(
            "mesh.add_branch_joint",
            text="Add Branch Joint",
            icon='MOD_SIMPLEDEFORM')

 
class BoneUtilitiesMenu(bpy.types.Menu):
    bl_label = "Bone Utilities"
    bl_idname = "view3d.bone_utilities"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Skeleton")
        layout.operator(
            "armature.add_root_bone",
            text="Add Root Bone",
            icon="BONE_DATA")
        layout.operator(
            "ops.apply_animation_scaling",
            text="Apply Animation Scaling",
            icon='BONE_DATA')
        layout.separator()

        layout.label(text="Bone")
        layout.operator(
            "object.edit_inverse_kinematics",
            text="Edit Inverse Kinematics",
            icon="CONSTRAINT")
        layout.operator(
            "scene.remove_fake_bones",
            text="Remove Old Fakebones",
            icon='CONSTRAINT')
        layout.separator()

        layout.label(text="Physics")
        layout.operator(
            "armature.add_bone_geometry",
            text="Add Bone Geometry",
            icon="PHYSICS")
        layout.operator(
            "armature.remove_bone_geometry",
            text="Remove Bone Geometry",
            icon="PHYSICS")
        layout.operator(
            "armature.rename_phys_bones",
            text="Rename Phys Bones",
            icon="PHYSICS")


class MeshUtilitiesMenu(bpy.types.Menu):
    bl_label = "Mesh Utilities"
    bl_idname = "view3d.mesh_utilities"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Weight Repair")
        layout.operator(
            "mesh.find_weightless",
            text="Find Weightless",
            icon="WPAINT_HLT")
        layout.operator(
            "mesh.remove_weight",
            text="Remove Weight",
            icon="WPAINT_HLT")
        layout.separator()

        layout.label(text="Mesh Repair")
        layout.operator(
            "object.find_degenerate_faces",
            text="Find Degenerate",
            icon='ZOOM_ALL')
        layout.operator(
            "mesh.find_multiface_lines",
            text="Find Multi-face",
            icon='ZOOM_ALL')
        layout.separator()

        layout.label(text="UV Repair")
        layout.operator(
            "scene.find_no_uvs",
            text="Find All Objects with No UV's",
            icon="UV_FACESEL")
        layout.operator(
            "mesh.add_uv_texture",
            text="Add UV's to Objects",
            icon="UV_FACESEL")


class CustomPropertiesMenu(bpy.types.Menu):
    bl_label = "User Defined Properties"
    bl_idname = "menu.UDP"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "object.edit_render_mesh",
            text="Edit Render Mesh",
            icon="FORCE_LENNARDJONES")
        layout.separator()
        layout.operator(
            "object.edit_physics_proxy",
            text="Edit Physics Proxy",
            icon="META_CUBE")
        layout.separator()
        layout.operator(
            "object.edit_joint_node",
            text="Edit Joint Node",
            icon="MOD_SCREW")
        layout.separator()
        layout.operator(
            "object.edit_deformable",
            text="Edit Deformable",
            icon="MOD_SIMPLEDEFORM")


class ConfigurationsMenu(bpy.types.Menu):
    bl_label = "Configurations"
    bl_idname = "view3d.configurations"

    def draw(self, context):
        layout = self.layout

        layout.label("Configure")
        layout.operator("file.find_rc", text="Find RC", icon="SPACE2")
        layout.operator(
            "file.find_rc_for_texture_conversion",
            text="Find Texture RC",
            icon="SPACE2")
        layout.separator()
        layout.operator(
            "file.select_texture_dir",
            text="Select Textures Folder",
            icon="FILE_FOLDER")


class AddMaterialPhysicsMenu(bpy.types.Menu):
    bl_label = "Add Material Physics"
    bl_idname = "menu.add_material_physics"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Add Material Physics")
        layout.separator()
        layout.operator(
            "material.add_phys_default",
            text="__physDefault",
            icon='PHYSICS')
        layout.operator(
            "material.add_phys_proxy_no_draw",
            text="__physProxyNoDraw",
            icon='PHYSICS')
        layout.operator(
            "material.add_phys_none",
            text="__physNone",
            icon='PHYSICS')
        layout.operator(
            "material.add_phys_obstruct",
            text="__physObstruct",
            icon='PHYSICS')
        layout.operator(
            "material.add_phys_no_collide",
            text="__physNoCollide",
            icon='PHYSICS')


class CryBlendReducedMenu(bpy.types.Menu):
    bl_label = 'CryBlend'
    bl_idname = 'view3d.cryblend_reduced_menu'

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "object.apply_transforms",
            text="Apply All Transforms",
            icon="MESH_DATA")
        layout.separator()
        layout.menu("menu.add_physics_proxy", icon="ROTATE")
        layout.separator()
        layout.menu(CryUtilitiesMenu.bl_idname, icon='OUTLINER_OB_EMPTY')
        layout.separator()
        layout.menu(BoneUtilitiesMenu.bl_idname, icon='BONE_DATA')
        layout.separator()
        layout.menu(MeshUtilitiesMenu.bl_idname, icon='MESH_CUBE')
        layout.separator()
        layout.menu(CustomPropertiesMenu.bl_idname, icon='SCRIPT')
        layout.separator()


#------------------------------------------------------------------------------
# Registration:
#------------------------------------------------------------------------------

def get_classes_to_register():
    classes = (
        FindRC,
        FindRCForTextureConversion,
        SelectTexturesDirectory,
        SaveCryBlendConfiguration,

        AddCryExportNode,
        SelectedToCryExportNodes,
        AddMaterial,
        AddRootBone,
        ApplyTransforms,
        AddProxy,
        AddBreakableJoint,
        AddBranch,
        AddBranchJoint,

        EditInverseKinematics,
        EditRenderMesh,
        EditPhysicProxy,
        EditJointNode,
        EditDeformable,

        FixWheelTransforms,

        AddMaterialPhysDefault,
        AddMaterialPhysProxyNoDraw,
        AddMaterialPhysNone,
        AddMaterialPhysObstruct,
        AddMaterialPhysNoCollide,

        FindDegenerateFaces,
        FindMultifaceLines,
        FindWeightless,
        RemoveAllWeight,
        FindNoUVs,
        AddUVTexture,

        RenamePhysBones,
        AddBoneGeometry,
        RemoveBoneGeometry,
        RemoveFakebones,

        ApplyAnimationScale,

        Export,
        ErrorHandler,

        ExportUtilitiesPanel,
        CryUtilitiesPanel,
        BoneUtilitiesPanel,
        MeshUtilitiesPanel,
        CustomPropertiesPanel,
        ConfigurationsPanel,

        CryBlendMainMenu,
        AddPhysicsProxyMenu,
        BoneUtilitiesMenu,
        CryUtilitiesMenu,
        MeshUtilitiesMenu,
        CustomPropertiesMenu,
        ConfigurationsMenu,

        AddMaterialPhysicsMenu,
        CryBlendReducedMenu,
    )

    return classes


def draw_item(self, context):
    layout = self.layout
    layout.menu(CryBlendMainMenu.bl_idname)


def physics_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.label("CryBlend")
    layout.menu("menu.add_material_physics", icon="PHYSICS")
    layout.separator()


def register():
    for classToRegister in get_classes_to_register():
        bpy.utils.register_class(classToRegister)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            'wm.call_menu',
            'Q',
            'PRESS',
            ctrl=False,
            shift=True)
        kmi.properties.name = "view3d.cryblend_reduced_menu"

    bpy.types.INFO_HT_header.append(draw_item)
    bpy.types.MATERIAL_MT_specials.append(physics_menu)


def unregister():
    # Be sure to unregister operators.
    for classToRegister in get_classes_to_register():
        bpy.utils.unregister_class(classToRegister)
        wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['3D View']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "view3d.cryblend_reduced_menu":
                    km.keymap_items.remove(kmi)
                    break

    bpy.types.INFO_HT_header.remove(draw_item)
    bpy.types.MATERIAL_MT_specials.remove(physics_menu)


if __name__ == "__main__":
    register()

    # The menu can also be called from scripts
    bpy.ops.wm.call_menu(name=ExportUtilitiesPanel.bl_idname)
