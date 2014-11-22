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
# Purpose:     Primary python file for CryBlend add-on
#
# Author:      Angelo J. Miner
# Extended by: Duo Oratar, Mikołaj Milej, stardidi, Daniel White
#
# Created:     23/02/2012
# Copyright:   (c) Angelo J. Miner 2012
# License:     GPLv2+
#------------------------------------------------------------------------------


bl_info = {
    "name": "CryEngine3 Utilities and Exporter",
    "author": "Angelo J. Miner, Duo Oratar, Mikołaj Milej, stardidi, Daniel White",
    "blender": (2, 70, 0),
    "version": (4, 13, 0),
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
else:
    import bpy
    from io_export_cryblend import add, export, exceptions, utils

from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, \
    FloatProperty, IntProperty, StringProperty
from bpy.types import Menu, Panel
from bpy_extras.io_utils import ExportHelper
from io_export_cryblend.configuration import Configuration
from io_export_cryblend.outPipe import cbPrint
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


# for help
new = 2  # open in a new tab, if possible


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
        Configuration.rc_path = "%s" % filepath
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
        Configuration.rc_for_texture_conversion_path = "%s" % filepath
        cbPrint("Found RC at {!r}.".format(
                        Configuration.rc_for_texture_conversion_path),
                'debug')

    def invoke(self, context, event):
        self.filepath = Configuration.rc_for_texture_conversion_path

        return ExportHelper.invoke(self, context, event)


class SelectTexturesDirectory(bpy.types.Operator, PathSelectTemplate):
    '''This path will be used to create relative path \
for textures in .mtl file.'''

    bl_label = "Select Textures Directory"
    bl_idname = "file.select_textures_directory"

    filename_ext = ""

    def process(self, filepath):
        Configuration.textures_directory = "%s" % os.path.dirname(filepath)
        cbPrint("Textures directory: {!r}.".format(
                                            Configuration.textures_directory),
                'debug')

    def invoke(self, context, event):
        self.filepath = Configuration.textures_directory

        return ExportHelper.invoke(self, context, event)


class MenuTemplate():
    class Operator:
        def __init__(self, name="", icon=''):
            self.name = name
            self.icon = icon

    operators = None
    label = None

    def draw(self, context):
        col = self.col

        if self.label:
            col.label(text=self.label)
            col.separator()

        for operator in self.operators:
            col.operator(operator.name, icon=operator.icon)


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


class AddCryExportNode(bpy.types.Operator):
    '''Add selected objects to an existing or new CryExportNode'''
    bl_label = "Add selection to a single CryExportNode"
    bl_idname = "object.add_cry_export_node"
    bl_options = {"REGISTER", "UNDO"}
    nodeNameUserInput = StringProperty(name="CryExportNode name")

    def execute(self, context):
        # Add to existing ExportNode.
        for group in bpy.data.groups:
            if utils.isExportNode(group.name):
                if group.name.endswith(self.nodeNameUserInput):
                    selected = bpy.context.selected_objects
                    for object in selected:
                        if not object.name in group.objects:
                            group.objects.link(object)
                            message = "Added {} to {}".format(object.name, group.name)
                            self.report({'INFO'}, message)
                            cbPrint(message)
                    return {'FINISHED'}

        # Create new ExportNode.
        bpy.ops.group.create(name="CryExportNode_{}".format(self.nodeNameUserInput))
        message = "Created CryExportNode_{}".format(self.nodeNameUserInput)
        self.report({'INFO'}, message)
        cbPrint(message)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddProxy(bpy.types.Operator):
    '''Click to add proxy to selected mesh. The proxy will always display as a box but will \
be converted to the selected shape in CryEngine.'''
    bl_label = "Add Proxy"
    bl_idname = "object.add_proxy"
    type = StringProperty()

    def execute(self, context):
        active = bpy.context.active_object

        if (active.type == "MESH"):
            already_exists = False
            for object_ in bpy.data.objects:
                if (object_.name == "{0}_{1}-proxy".format(active.name, getattr(self, "type")) or
                        object_.name.endswith("-proxy")):
                    already_exists = True
                    break
            if (not already_exists):
                self.add_proxy(active, type)

        message = "Adding %s proxy to active object" % getattr(self, "type")
        self.report({'INFO'}, message)
        return {'FINISHED'}


    def add_proxy(self, object_, type):
        old_origin = object_.location.copy()
        old_cursor = bpy.context.scene.cursor_location.copy()
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.mesh.primitive_cube_add()
        bound_box = bpy.context.active_object
        bound_box.name = "{0}_{1}-proxy".format(object_.name, getattr(self, "type"))
        bound_box.draw_type = "WIRE"
        bound_box.dimensions = object_.dimensions
        bound_box.location = object_.location
        bound_box.rotation_euler = object_.rotation_euler

        for group in object_.users_group:
            bpy.ops.object.group_link(group=group.name)

        proxy_material = bpy.data.materials.new("{0}_{1}-proxy__physProxyNone".format(object_.name, getattr(self, "type")))
        bound_box.data.materials.append(proxy_material)

        if (getattr(self, "type") == "box"):
            bpy.ops.object.add_box_proxy_property()
        elif (getattr(self, "type") == "capsule"):
            bpy.ops.object.add_capsule_proxy_property()
        elif (getattr(self, "type") == "cylinder"):
            bpy.ops.object.add_cylinder_proxy_property()
        else: # sphere proxy
            bpy.ops.object.add_sphere_proxy_property()

        bpy.context.scene.cursor_location = old_origin
        bpy.ops.object.select_all(action="DESELECT")
        object_.select = True
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        object_.select = False
        bound_box.select = True
        bpy.context.scene.objects.active = bound_box
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        bpy.context.scene.cursor_location = old_cursor


class SelectedToCryExportNodes(bpy.types.Operator):
    '''Add selected objects to individual CryExportNodes.'''
    bl_label = "Add selection to individual CryExportNodes"
    bl_idname = "object.selected_to_cry_export_nodes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected = bpy.context.selected_objects
        bpy.ops.object.select_all(action="DESELECT")
        for object_ in selected:
            object_.select = True
            if (len(object_.users_group) == 0):
                bpy.ops.group.create(name="CryExportNode_%s" % (object_.name))
            object_.select = False

        message = "Adding Selected to CryExportNodes"
        self.report({"INFO"}, message)
        return {"FINISHED"}


class SetMaterialNames(bpy.types.Operator):
    '''Materials will be named after the first CryExportNode the Object is in.'''
    """Set Material Names by heeding the RC naming scheme:
        - CryExportNode group name
        - Strict number sequence beginning with 1 for each CryExportNode (max 999)
        - Physics
    """
    bl_label = "Update material names in CryExportNodes"
    bl_idname = "material.set_material_names"
    physUserInput = StringProperty(name="Physics", default = "physDefault")

    def execute(self, context):
        # Revert all materials to fetch also those that are no longer in a group
        # and store their possible physics properties in a dictionary.
        physicsProperties = getMaterialPhysics()
        removeCryBlendProperties()

        # Create a dictionary with all CryExportNodes to store the current number
        # of materials in it.
        materialCounter = getMaterialCounter()

        for group in bpy.data.groups:
            if utils.isExportNode(group.name):
                for object in group.objects:
                    for slot in object.material_slots:

                        # Skip materials that have been renamed already.
                        if not utils.isCryBlendMaterial(slot.material.name):
                            materialCounter[group.name] += 1
                            materialOldName = slot.material.name

                            # Load stored Physics if available for that material.
                            if physicsProperties.get(slot.material.name):
                                physics = physicsProperties[slot.material.name]
                            else:
                                physics = self.physUserInput

                            # Rename.
                            slot.material.name = "{}__{:03d}__{}__{}".format(
                                    group.name.replace("CryExportNode_", ""),
                                    materialCounter[group.name],
                                    utils.replaceInvalidRCCharacters(materialOldName),
                                    physics)
                            message = "Renamed {} to {}".format(
                                    materialOldName,
                                    slot.material.name)
                            self.report({'INFO'}, message)
                            cbPrint(message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class RemoveCryBlendProperties(bpy.types.Operator):
    '''Removes all CryBlend properties from material names. This includes \
physics, so they get lost.'''
    bl_label = "Remove CryBlend properties from material names"
    bl_idname = "material.remove_cry_blend_properties"

    def execute(self, context):
        removeCryBlendProperties()
        message = "Removed CryBlend properties from material names"
        self.report({'INFO'}, message)
        cbPrint(message)
        return {'FINISHED'}


def getMaterialCounter():
    """Returns a dictionary with all CryExportNodes."""
    materialCounter = {}
    for group in bpy.data.groups:
        if utils.isExportNode(group.name):
            materialCounter[group.name] = 0
    return materialCounter


def removeCryBlendProperties():
    """Removes CryBlend properties from all material names."""
    for material in bpy.data.materials:
        properties = utils.extractCryBlendProperties(material.name)
        if properties:
            material.name = properties["Name"]


def getMaterialPhysics():
    """Returns a dictionary with the physics of all material names."""
    physicsProperties = {}
    for material in bpy.data.materials:
        properties = utils.extractCryBlendProperties(material.name)
        if properties:
            physicsProperties[properties["Name"]] = properties["Physics"]
    return physicsProperties


class AddAnimNode(bpy.types.Operator):
    '''Click to add an AnimNode to selection or, with nothing selected, \
add an AnimNode to the scene.'''
    bl_label = "Add AnimNode"
    bl_idname = "object.add_anim_node"
    animNameUserInput = StringProperty(name="Animation Name")
    start_frame = FloatProperty(name="Start Frame")
    end_frame = FloatProperty(name="End Frame")

    def execute(self, context):
        object_ = bpy.context.active_object

        # 'add' selects added object
        bpy.ops.object.add(type='EMPTY')
        empty_object = bpy.context.active_object
        empty_object.name = 'animnode'
        empty_object["animname"] = self.animNameUserInput
        empty_object["startframe"] = self.start_frame
        empty_object["endframe"] = self.end_frame

        if object_:
            object_.select = True
            bpy.context.scene.objects.active = object_

        bpy.ops.object.parent_set(type='OBJECT')
        message = "Adding AnimNode '%s'" % (self.animNameUserInput)
        self.report({'INFO'}, message)
        cbPrint(message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddBreakableJoint(bpy.types.Operator):
    '''Click to add a pre-broken breakable joint to current selection.'''
    bl_label = "Add Joint"
    bl_idname = "object.add_joint"

    def execute(self, context):
        return add.add_joint(self, context)


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
            bpy.ops.object.add(type='EMPTY', view_align=False, enter_editmode=False, location=(selected_vert[0], selected_vert[1], selected_vert[2]))
            empty_object = bpy.context.active_object
            empty_object.name = name_branch(True)
            bpy.context.scene.objects.active = active_object
            bpy.ops.object.mode_set(mode='EDIT')

            message = "Adding Branch"
            self.report({'INFO'}, message)
            cbPrint(message)
        return {'FINISHED'}


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
            bpy.ops.object.add(type='EMPTY', view_align=False, enter_editmode=False, location=(selected_vert[0], selected_vert[1], selected_vert[2]))
            empty_object = bpy.context.active_object
            empty_object.name = name_branch(False)
            bpy.context.scene.objects.active = active_object
            bpy.ops.object.mode_set(mode='EDIT')

            message = "Adding Branch Joint"
            self.report({'INFO'}, message)
            cbPrint(message)
        return {'FINISHED'}


def get_vertex_data():
    selected_vert_coordinates = [i.co for i in bpy.context.active_object.data.vertices if i.select] 
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
            return ("branch%s_1" % (highest_branch_number + 1))
        else:
            return ("branch%s_%s" % (highest_branch_number, highest_joint_number + 1))
    else:
        return "branch1_1"


class OpenCryDevWebpage(bpy.types.Operator):
    '''A link to the CryDev forums.'''
    bl_label = "Visit CryDev Forums"
    bl_idname = "file.open_crydev_webpage"

    def execute(self, context):
        url = "http://www.crydev.net/viewtopic.php?f=315&t=103136"
        webbrowser.open(url, new=new)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class OpenGitHubWebpage(bpy.types.Operator):
    '''A link to the CryBlend Tutorial Wiki'''
    bl_label = "Visit CryBlend Tutorial Wiki"
    bl_idname = "file.open_github_webpage"

    def execute(self, context):
        url = "https://github.com/travnick/CryBlend/wiki/users-area"
        webbrowser.open(url, new=new)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


class OpenCryEngineDocsWebpage(bpy.types.Operator):
    '''A link to the CryEngine Docs Page.'''
    bl_label = "Visit CryEngine Docs Page"
    bl_idname = "file.open_cryengine_docs_webpage"

    def execute(self, context):
        url = "http://docs.cryengine.com/display/SDKDOC1/Home"
        webbrowser.open(url, new=new)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


#------------------------------------------------------------------------------
# CryEngine User
# Defined Properties:
#------------------------------------------------------------------------------


class OpenUDPWebpage(bpy.types.Operator):
    '''A link to UDP.'''
    bl_label = "Open Web Page for UDP"
    bl_idname = "file.open_udp_webpage"

    def execute(self, context):
        url = "http://freesdk.crydev.net/display/SDKDOC3/UDP+Settings"
        webbrowser.open(url, new=new)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# Rendermesh:
class AddMassProperty(bpy.types.Operator):
    '''Click to add a mass value.'''
    bl_label = "Mass"
    bl_idname = "object.add_mass_property"
    mass = FloatProperty(name="Mass")

    def execute(self, context):
        message = "Adding Mass of %s" % (self.mass)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_mass_property(self, context, self.mass)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddDensityProperty(bpy.types.Operator):
    '''Click to add a density value.'''
    bl_label = "Density"
    bl_idname = "object.add_density_property"
    density = FloatProperty(name="Density")

    def execute(self, context):
        message = "Adding Density of %s" % (self.density)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_density_property(self, context, self.density)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddPiecesProperty(bpy.types.Operator):
    '''Click to add a pieces value.'''
    bl_label = "Pieces"
    bl_idname = "object.add_pieces_property"
    pieces = FloatProperty(name="Pieces")

    def execute(self, context):
        message = "Adding %s Pieces" % (self.pieces)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_pieces_property(self, context, self.pieces)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddEntityProperty(bpy.types.Operator):
    '''Click to add an entity property.'''
    bl_label = "Entity"
    bl_idname = "object.add_entity_property"

    def execute(self, context):
        message = "Adding Entity Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_entity_property(self, context)


class AddDynamicProperty(bpy.types.Operator):
    '''Click to add a dynamic property.'''
    bl_label = "Dynamic"
    bl_idname = "object.add_dynamic_property"

    def execute(self, context):
        message = "Adding Dynamic Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_dynamic_property(self, context)


class AddNoHitRefinementProperty(bpy.types.Operator):
    '''Click to add a no hit refinement property.'''
    bl_label = "No Hit Refinement"
    bl_idname = "object.add_no_hit_refinement_property"

    def execute(self, context):
        message = "Adding No Hit Refinement Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_no_hit_refinement_property(self, context)


# Phys Proxy:
class AddBoxProxyProperty(bpy.types.Operator):
    '''Click to add a box proxy.'''
    bl_label = "Box"
    bl_idname = "object.add_box_proxy_property"

    def execute(self, context):
        message = "Adding Box Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_box_proxy_property(self, context)


class AddCylinderProxyProperty(bpy.types.Operator):
    '''Click to add a cylinder proxy.'''
    bl_label = "Cylinder"
    bl_idname = "object.add_cylinder_proxy_property"

    def execute(self, context):
        message = "Adding Cylinder Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_cylinder_proxy_property(self, context)


class AddCapsuleProxyProperty(bpy.types.Operator):
    '''Click to add a capsule proxy.'''
    bl_label = "Capsule"
    bl_idname = "object.add_capsule_proxy_property"

    def execute(self, context):
        message = "Adding Capsule Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_capsule_proxy_property(self, context)


class AddSphereProxyProperty(bpy.types.Operator):
    '''Click to add a sphere proxy.'''
    bl_label = "Sphere"
    bl_idname = "object.add_sphere_proxy_property"

    def execute(self, context):
        message = "Adding Sphere Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_sphere_proxy_property(self, context)


class AddNotaprimProxyProperty(bpy.types.Operator):
    '''Click to add a 'not a primitive' proxy property.'''
    bl_label = "Not a Primitive"
    bl_idname = "object.add_notaprim_proxy_property"

    def execute(self, context):
        message = "Adding 'Not a Primitive' Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_notaprim_proxy_property(self, context)


class AddNoExplosionOcclusionProperty(bpy.types.Operator):
    '''Click to add a no explosion occlusion property.'''
    bl_label = "No Explosion Occlusion"
    bl_idname = "object.add_no_explosion_occlusion_property"

    def execute(self, context):
        message = "Adding No Explosion Occlusion Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_no_explosion_occlusion_property(self, context)


class AddOtherRendermeshProperty(bpy.types.Operator):
    '''Click to add an other rendermesh property.'''
    bl_label = "Other Rendermesh"
    bl_idname = "object.add_other_rendermesh_property"

    def execute(self, context):
        message = "Adding Other Rendermesh Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_other_rendermesh_property(self, context)


class AddColltypePlayerProperty(bpy.types.Operator):
    '''Click to add a colltype player property.'''
    bl_label = "Colltype Player"
    bl_idname = "object.add_colltype_player_property"

    def execute(self, context):
        message = "Adding Colltype Player Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_colltype_player_property(self, context)


# Joint Node:
class AddBendProperty(bpy.types.Operator):
    '''Click to add a bend property.'''
    bl_label = "Bend"
    bl_idname = "object.add_bend_property"
    bendValue = FloatProperty(name="Bend Value")

    def execute(self, context):
        message = "Adding Bend Value of %s" % (self.bendValue)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_bend_property(self, context, self.bendValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddTwistProperty(bpy.types.Operator):
    '''Click to add a twist property.'''
    bl_label = "Twist"
    bl_idname = "object.add_twist_property"
    twistValue = FloatProperty(name="Twist Value")

    def execute(self, context):
        message = "Adding Twist Value of %s" % (self.twistValue)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_twist_property(self, context, self.twistValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddPullProperty(bpy.types.Operator):
    '''Click to add a pull property.'''
    bl_label = "Pull"
    bl_idname = "object.add_pull_property"
    pullValue = FloatProperty(name="Pull Value")

    def execute(self, context):
        message = "Adding Pull Value of %s" % (self.pullValue)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_pull_property(self, context, self.pullValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddPushProperty(bpy.types.Operator):
    '''Click to add a push property.'''
    bl_label = "Push"
    bl_idname = "object.add_push_property"
    pushValue = FloatProperty(name="Push Value")

    def execute(self, context):
        message = "Adding Push Value of %s" % (self.pushValue)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_push_property(self, context, self.pushValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddShiftProperty(bpy.types.Operator):
    '''Click to add a shift property.'''
    bl_label = "Shift"
    bl_idname = "object.add_shift_property"
    shiftValue = FloatProperty(name="Shift Value")

    def execute(self, context):
        message = "Adding Shift Value of %s" % (self.shiftValue)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_shift_property(self, context, self.shiftValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddGameplayCriticalProperty(bpy.types.Operator):
    '''Click to add a critical property.'''
    bl_label = "Gameplay Critical"
    bl_idname = "object.add_gameplay_critical_property"

    def execute(self, context):
        message = "Adding Gameplay Critical Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_gameplay_critical_property(self, context)


class AddPlayerCanBreakProperty(bpy.types.Operator):
    '''Click to add a breakable property.'''
    bl_label = "Player Can Break"
    bl_idname = "object.add_player_can_break_property"

    def execute(self, context):
        message = "Adding Player Can Break Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_player_can_break_property(self, context)


# Constraints:
class AddLimitConstraint(bpy.types.Operator):
    '''Click to add a limit constraint.'''
    bl_label = "Limit"
    bl_idname = "object.add_limit_constraint"
    limit = FloatProperty(name="Limit")

    def execute(self, context):
        message = "Adding Limit of %s" % (self.limit)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_limit_constraint(self, context, self.limit)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddMinAngleConstraint(bpy.types.Operator):
    '''Click to add a min angle constraint.'''
    bl_label = "Min Angle"
    bl_idname = "object.add_min_angle_constraint"
    minAngle = FloatProperty(name="Min Angle")

    def execute(self, context):
        message = "Adding Min Angle of %s" % (self.minAngle)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_min_angle_constraint(self, context, self.minAngle)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class AddMaxAngleConstraint(bpy.types.Operator):
    '''Click to add a max angle constraint.'''
    bl_label = "Max Angle"
    bl_idname = "object.add_max_angle_constraint"
    maxAngle = FloatProperty(name="Max Angle")

    def execute(self, context):
        message = "Adding Max Angle of %s" % (self.maxAngle)
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_max_angle_constraint(self, context, self.maxAngle)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddDampingConstraint(bpy.types.Operator):
    '''Click to add a damping constraint.'''
    bl_label = "Damping"
    bl_idname = "object.add_damping_constraint"

    def execute(self, context):
        message = "Adding Damping Constraint"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_damping_constraint(self, context)


class AddCollisionConstraint(bpy.types.Operator):
    '''Click to add a collision constraint.'''
    bl_label = "Collision"
    bl_idname = "object.add_collision_constraint"

    def execute(self, context):
        message = "Adding Collision Constraint"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_collision_constraint(self, context)


# Deformables:
class AddDeformableProperties(bpy.types.Operator):
    '''Click to add a deformable mesh property.'''
    bl_label = "Deformable"
    bl_idname = "object.add_deformable_properties"
    mass = FloatProperty(name="Mass")
    stiffness = FloatProperty(name="Stiffness")
    hardness = FloatProperty(name="Hardness")
    max_stretch = FloatProperty(name="Max Stretch")
    max_impulse = FloatProperty(name="Max Impulse")
    skin_dist = FloatProperty(name="Skin Distance")
    thickness = FloatProperty(name="Thickness")
    explosion_scale = FloatProperty(name="Explosion Scale")
    is_primitive = EnumProperty(
        name="Primitive?",
        description="",
        items=(
            ("Yes", "Yes", "Is a primitive"),
            ("No", "No", "Not a primitive"),
        ),
        default="No",
    )

    def execute(self, context):
        message = "Adding Deformable Properties"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_deformable_properties(self, context, self.mass, self.stiffness, self.hardness,
        self.max_stretch, self.max_impulse, self.skin_dist, self.thickness, self.explosion_scale, self.is_primitive)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


# Vehicles:
class AddWheelProperty(bpy.types.Operator):
    '''Click to add a wheels property.'''
    bl_label = "Add Wheel Properties"
    bl_idname = "object.add_wheel_property"

    def execute(self, context):
        message = "Adding Wheel Properties"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_wheel_property(self, context)


class FixWheelTransforms(bpy.types.Operator):
    bl_label = "Fix Wheel Transforms"
    bl_idname = "object.fix_wheel_transforms"

    def execute(self, context):
        ob = bpy.context.active_object
        ob.location.x = (ob.bound_box[0][0] + ob.bound_box[1][0]) / 2.0
        ob.location.y = (ob.bound_box[2][0] + ob.bound_box[3][0]) / 2.0
        ob.location.z = (ob.bound_box[4][0] + ob.bound_box[5][0]) / 2.0

        return {'FINISHED'}


# Material Physics:
class AddMaterialPhysDefault(bpy.types.Operator):
    '''__physDefault will be added to the material name.'''
    bl_label = "__physDefault"
    bl_idname = "material.add_phys_default"

    def execute(self, context):
        message = "Adding __physDefault"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_default(self, context)


class AddMaterialPhysProxyNoDraw(bpy.types.Operator):
    '''__physProxyNoDraw will be added to the material name.'''
    bl_label = "Add __physProxyNoDraw to Material Name"
    bl_idname = "material.add_phys_proxy_no_draw"

    def execute(self, context):
        message = "Adding __physProxyNoDraw"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_proxy_no_draw(self, context)


class AddMaterialPhysNone(bpy.types.Operator):
    '''__physNone will be added to the material name.'''
    bl_label = "__physNone"
    bl_idname = "material.add_phys_none"

    def execute(self, context):
        message = "Adding __physNone"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_none(self, context)


class AddMaterialPhysObstruct(bpy.types.Operator):
    '''__physObstruct will be added to the material name.'''
    bl_label = "__physObstruct"
    bl_idname = "material.add_phys_obstruct"

    def execute(self, context):
        return add.add_phys_obstruct(self, context)


class AddMaterialPhysNoCollide(bpy.types.Operator):
    '''__physNoCollide will be added to the material name.'''
    bl_label = "__physNoCollide"
    bl_idname = "material.add_phys_no_collide"

    def execute(self, context):
        message = "Adding __physNoCollide"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_no_collide(self, context)


#------------------------------------------------------------------------------
# Mesh and Weight
# Repair Tools:
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
        bpy.ops.mesh.select_all(action = 'DESELECT')

        ''' Vertices data should be actually manipulated in Object mode
            to be displayed in Edit mode correctly.'''
        bpy.ops.object.mode_set(mode='OBJECT')
        me = bpy.context.active_object

        vert_list = [vert for vert in me.data.vertices]
        context.tool_settings.mesh_select_mode = (True, False, False)
        cbPrint("Locating degenerate faces.")
        degenerate_count = 0



        for poly in me.data.polygons:
            if poly.area < self.area_epsilon:
                cbPrint("Found a degenerate face.")
                degenerate_count += 1

                for v in poly.vertices:
                    cbPrint("Selecting face vertices.")
                    vert_list[v].select = True

        if degenerate_count > 0:
            bpy.ops.object.mode_set(mode='EDIT')
            self.report({'WARNING'},
                        "Found %i degenerate faces" % degenerate_count)
        else:
            self.report({'INFO'}, "No degenerate faces found")
            # Restore the original mode
            bpy.ops.object.mode_set(mode=saved_mode)

        return {'FINISHED'}


# Duo Oratar
class FindMultifaceLines(bpy.types.Operator):
    '''Select the object to test in object mode with nothing selected in \
it's mesh before running this.'''
    bl_label = "Find Lines with 3+ Faces."
    bl_idname = "mesh.find_multiface_lines"

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


class FindWeightless(bpy.types.Operator):
    '''Select the object in object mode with nothing in its mesh selected \
before running this'''
    bl_label = "Find Weightless Vertices"
    bl_idname = "mesh.find_weightless"

    # Minimum net weight to be considered non-weightless
    weight_epsilon = 0.0001

    # Weightless: a vertex not belonging to any groups or with a net weight of 0
    def execute(self, context):
        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        if obj.type == "MESH":
            for v in obj.data.vertices:
                if (not v.groups):
                    v.select = True
                else:
                    weight = 0
                    for g in v.groups:
                        weight += g.weight
                    if (weight < self.weight_epsilon):
                        v.select = True
        obj.data.update()
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


class RemoveAllWeight(bpy.types.Operator):
        '''Select vertices from which to remove weight in edit mode.'''
        bl_label = "Remove All Weight from Selected Vertices"
        bl_idname = "mesh.remove_weight"

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


class FindNoUVs(bpy.types.Operator):
        '''Use this with no objects selected in object mode
to find all items without UVs.'''
        bl_label = "Find All Objects with No UV's"
        bl_idname = "scene.find_no_uvs"

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


class AddUVTexture(bpy.types.Operator):
        '''Add UVs to all meshes without UVs.'''
        bl_label = "Add UV's to Objects"
        bl_idname = "mesh.add_uv_texture"

        def execute(self, context):
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    uv = False
                    for i in obj.data.uv_textures:
                        uv = True
                        break
                    if not uv:
                        bpy.context.scene.objects.active = obj
                        bpy.ops.mesh.uv_texture_add()
                        message = "Added UV map to {}".format(obj.name)
                        self.report({'INFO'}, message)
                        cbPrint(message)
            return {'FINISHED'}


#------------------------------------------------------------------------------
# Regarding Fakebones
# And BoneGeometry:
#------------------------------------------------------------------------------


# verts and faces
# find bone heads and add at that location
class AddFakeBone(bpy.types.Operator):
    '''Add helpers to track bone transforms.'''
    bl_label = "Add FakeBone"
    bl_idname = "armature.add_fake_bone"
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

        scene_objects = bpy.context.scene.objects
        for arm in scene_objects:
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
                    for fb in scene_objects:
                        if fb.name == pbone.name:
                            fb["fakebone"] = "fakebone"
                    bpy.context.scene.objects.active = arm
                    arm.data.bones.active = pbone.bone
                    bpy.ops.object.parent_set(type='BONE')

        return {'FINISHED'}


def add_fake_bone(width, height, depth):
    """
    This function takes inputs and returns vertex and face arrays.
    No actual mesh data creation is done here.
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


class RemoveFakeBones(bpy.types.Operator):
        '''Select to remove all fakebones from the scene.'''
        bl_label = "Remove All FakeBones"
        bl_idname = "scene.remove_fake_bones"
        bl_options = {'REGISTER', 'UNDO'}

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


class KeyframeFakebones(bpy.types.Operator):
    '''Adds a key frame list for the fakebones.'''
    bl_label = "Make Fakebone Keyframes List"
    bl_idname = "armature.keyframe_fakebones"

    def execute(self, context):
        return keyframe_fakebones()


def keyframe_fakebones():
    scene = bpy.context.scene
    location_list = []
    rotation_list = []
    keyframe_list = []
    armature = None
    for object_ in scene.objects:
        if (object_.type == "ARMATURE"):
            armature = object_

    if (armature is None):
        return {"FINISHED"}

    # Stage 1: Find unique keyframes
    animation_data = armature.animation_data
    if (animation_data is None):
        return {"FINISHED"}
    action = animation_data.action
    for fcurve in action.fcurves:
        for keyframe in fcurve.keyframe_points:
            keyframe_entry = int(keyframe.co.x)
            if (keyframe_entry not in keyframe_list):
                keyframe_list.append(keyframe_entry)

    # Stage 2: Calculate fakebone transformation data
    for frame in keyframe_list:
        scene.frame_set(frame)
        for bone in armature.pose.bones:
            fakebone = scene.objects.get(bone.name)
            if (fakebone is None):
                return {"FINISHED"}
            bonecm = fakebone.matrix_local
            if (bone.parent and bone.parent.parent):
                bonepm = scene.objects.get(bone.parent.name).matrix_local
                # Relative to parent = inverse parent bone matrix * bone matrix
                animatrix = bonepm.inverted() * bonecm
            else:
                # Root bone or bones connected directly to root
                animatrix = bonecm
            lm, rm, sm = animatrix.decompose()
            location_list.append(lm)
            rotation_list.append(rm.to_euler())

    # Stage 3: Keyframe fakebones
    i = 0
    for frame in keyframe_list:
        scene.frame_set(frame)
        for bone in armature.pose.bones:
            fakebone = scene.objects.get(bone.name)
            fakebone.location = location_list[i]
            fakebone.rotation_euler = rotation_list[i]
            fakebone.keyframe_insert(data_path="location")
            fakebone.keyframe_insert(data_path="rotation_euler")
            i += 1
            
    scene.frame_set(scene.frame_start)

    return {'FINISHED'}


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

    def draw(self, context):
        col = self.col
        col.label(text="Add boneGeometry")

    def execute(self, context):
        verts_loc, faces = add_bone_geometry()

        nameList = []
        for obj in bpy.context.scene.objects:
            nameList.append(obj.name)

        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE' and obj.select:

                physBonesList = []
                if "%s_Phys" % obj.name in nameList:
                    for bone in bpy.data.objects["%s_Phys" % obj.name].data.bones:
                        physBonesList.append(bone.name)

                for bone in obj.data.bones:
                    if ((not "%s_boneGeometry" % bone.name in nameList
                            and not "%s_Phys" % obj.name in nameList)
                        or ("%s_Phys" % obj.name in nameList
                            and "%s_Phys" % bone.name in physBonesList
                            and not "%s_boneGeometry" % bone.name in nameList)
                        ):
                        mesh = bpy.data.meshes.new(
                                    "%s_boneGeometry" % bone.name
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
    '''Remove BoneGeometry for bones in selected armatures'''
    bl_label = "Remove BoneGeometry"
    bl_idname = "armature.remove_bone_geometry"
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
        col = self.col
        col.label(text="Remove boneGeometry")

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
            if "%s_Phys" % obj.name in nameList:
                for bone in bpy.data.objects["%s_Phys" % obj.name].data.bones:
                    physBonesList.append(bone.name)

            for bone in obj.data.bones:  # For each bone
                if "%s_boneGeometry" % bone.name in nameList:
                    bpy.data.objects["%s_boneGeometry" % bone.name].select = True

            bpy.ops.object.delete()

        return {'FINISHED'}


# Duo Oratar
class RenamePhysBones(bpy.types.Operator):
    '''Renames bones with _Phys extension.'''
    bl_label = "Rename Phys Bones"
    bl_idname = "armature.rename_phys_bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.context.scene.objects:
            if ('_Phys' == obj.name[-5:]
                and obj.type == 'ARMATURE'):
                for bone in obj.data.bones:
                    bone.name = "%s_Phys" % bone.name

        return {'FINISHED'}


class Export(bpy.types.Operator, ExportHelper):
    '''Select to export to game.'''
    bl_label = "Export to Game"
    bl_idname = "scene.export_to_game"
    filename_ext = ".dae"
    filter_glob = StringProperty(default="*.dae", options={'HIDDEN'})

    export_type = EnumProperty(
            name="File Type",
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
            name="Merge Animations",
            description="For animated models - merge animations into 1.",
            default=False,
            )
    donot_merge = BoolProperty(
            name="Do Not Merge Nodes",
            description="Generally a good idea.",
            default=True,
            )
    avg_pface = BoolProperty(
            name="Average Planar Face Normals",
            description="Help align face normals that have normals that are within 1 degree.",
            default=False,
            )
    run_rc = BoolProperty(
            name="Run RC",
            description="Generally a good idea.",
            default=True,
            )
    do_materials = BoolProperty(
            name="Run RC and Do Materials",
            description="Generally a good idea.",
            default=False,
            )
    convert_source_image_to_dds = BoolProperty(
            name="Convert Textures to DDS",
            description="Converts source textures to DDS while exporting materials.",
            default=False,
            )
    save_tiff_during_conversion = BoolProperty(
            name="Save TIFF During Conversion",
            description="Saves TIFF images that are generated during conversion to DDS.",
            default=False,
            )
    refresh_rc = BoolProperty(
            name="Refresh RC Output",
            description="Generally a good idea.",
            default=True,
            )
    include_ik = BoolProperty(
            name="Include IK in Character",
            description="Adds IK from your skeleton to the phys skeleton upon export.",
            default=False,
            )
    correct_weight = BoolProperty(
            name="Correct Weights",
            description="For use with .chr files.",
            default=False,
            )
    make_layer = BoolProperty(
            name="Make .lyr File",
            description="Makes a .lyr to reassemble your scene in the CryEngine 3.",
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
                'correct_weight',
                'make_layer'
            )

            for attribute in attributes:
                setattr(self, attribute, getattr(config, attribute))

            setattr(self, 'cryblend_version', VERSION)
            setattr(self, 'rc_path', Configuration.rc_path)
            setattr(self, 'rc_for_textures_conversion_path',
                    Configuration.rc_for_texture_conversion_path)
            setattr(self, 'textures_dir', Configuration.textures_directory)

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
            bpy.ops.screen.display_error('INVOKE_DEFAULT', message=exception.what())

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        box = col.box()
        box.label("General")
        box.prop(self, "export_type")
        box.prop(self, "donot_merge")
        box.prop(self, "avg_pface")

        box = col.box()
        box.prop(self, "run_rc")
        box.prop(self, "refresh_rc")

        box = col.box()
        box.label("Image and Material")
        box.prop(self, "do_materials")
        box.prop(self, "convert_source_image_to_dds")
        box.prop(self, "save_tiff_during_conversion")

        box = col.box()
        box.label("Animation")
        box.prop(self, "merge_anm")
        box.prop(self, "include_ik")

        box = col.box()
        box.label("Weight Correction")
        box.prop(self, "correct_weight")

        box = col.box()
        box.label("CryEngine Editor")
        box.prop(self, "make_layer")

        box = col.box()
        box.label("Developer Tools")
        box.prop(self, "run_in_profiler")


class ErrorHandler(bpy.types.Operator):
    bl_label = "Error:"
    bl_idname = "screen.display_error"

    WIDTH = 400
    HEIGHT = 200

    message = bpy.props.StringProperty()

    def execute(self, context):
        self.report({'ERROR'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, self.WIDTH, self.HEIGHT)

    def draw(self, context):
        self.col.label(self.bl_label, icon='ERROR')
        self.col.split()
        multiline_label(self.col, self.message)
        self.col.split()
        self.col.split(0.2)


def multiline_label(col, text):
    for line in text.splitlines():
        row = col.split()
        row.label(line)


#------------------------------------------------------------------------------
# Scripting
# Module:
#------------------------------------------------------------------------------


class SelectScriptEditor(bpy.types.Operator, PathSelectTemplate):
    '''Select a text editor of your choice to open scripts (i.e., notepad++.exe)'''

    bl_label = "Select Script/Text Editor"
    bl_idname = "file.select_script_editor"

    filename_ext = ".exe"
    filter_glob = StringProperty(default="*.exe", options={'HIDDEN'})

    def process(self, filepath):
        Configuration.script_editor = filepath

    def invoke(self, context, event):
        self.filepath = Configuration.script_editor

        return ExportHelper.invoke(self, context, event)


class GenerateScript(bpy.types.Operator, PathSelectTemplate):
    bl_label = "Generate Script"
    bl_idname = "wm.generate_script"

    filename_ext = ""
    filter_glob = StringProperty(options={'HIDDEN'})

    type = StringProperty(options={'HIDDEN'})
    entries = IntProperty(name="Entries", min=1, default=1)

    def process(self, filepath):
        if (getattr(self, "type") == "CHRPARAMS"):
            self.generate_chrparams(filepath, self.entries)
        elif (getattr(self, "type") == "CDF"):
            self.generate_cdf(filepath, self.entries)
        elif (getattr(self, "type") == "ENT"):
            self.generate_ent(filepath)
        elif (getattr(self, "type") == "LUA"):
            self.generate_lua(filepath)

    def invoke(self, context, event):
        if (getattr(self, "type") == "CHRPARAMS"):
            self.filename_ext = ".chrparams"
            self.filter_glob = "*.chrparams"
        elif (getattr(self, "type") == "CDF"):
            self.filename_ext = ".cdf"
            self.filter_glob = "*.cdf"
        elif (getattr(self, "type") == "ENT"):
            self.filename_ext = ".ent"
            self.filter_glob = "*.ent"
        elif (getattr(self, "type") == "LUA"):
            self.filename_ext = ".lua"
            self.filter_glob = "*.lua"
        return ExportHelper.invoke(self, context, event)

    def draw(self, context):
        layout = self.layout
        if (getattr(self, "type") == "CHRPARAMS" or
                getattr(self, "type") == "CDF"):
            layout.prop(self, "entries")

    def generate_chrparams(self, filepath, entries):
        contents = """<Params>\
<AnimationList>\
</AnimationList>\
</Params>"""
        script = parseString(contents)

        animation_list = script.getElementsByTagName("AnimationList")[0]
        animation = parseString("""<Animation name="???" path="???.caf"/>""").getElementsByTagName("Animation")[0]
        for index in range(0, entries):
            animation_list.appendChild(animation.cloneNode(deep=False))
        contents = script.toprettyxml(indent="\t")

        self.generate_file(filepath, contents)

    def generate_cdf(self, filepath, entries):
        contents = """<CharacterDefinition>\
<Model File="???.chr" Material="???"/>\
<AttachmentList>\
</AttachmentList>\
<ShapeDeformation COL0="0" COL1="0" COL2="0" COL3="0" COL4="0" COL5="0" COL6="0" COL7="0"/>\
</CharacterDefinition>"""

        script = parseString(contents)

        attachment_list = script.getElementsByTagName("AttachmentList")[0]
        attachment = parseString("""<Attachment AName="???" Type="CA_SKIN" Rotation="1,0,0,0" Position="0,0,0" \
                                    BoneName="" Binding="???.chr" Flags="0"/>""").getElementsByTagName("Attachment")[0]
        for index in range(0, entries):
            attachment_list.appendChild(attachment.cloneNode(deep=False))
        contents = script.toprettyxml(indent="\t")

        self.generate_file(filepath, contents)

    def generate_ent(self, filepath):
        contents = """<?xml version="1.0" ?>
<Entity
\tName="???"
\tScript="Scripts/Entities/???.lua"
/>
"""

        self.generate_file(filepath, contents)

    def generate_lua(self, filepath):
        contents = ""

        self.generate_file(filepath, contents)

    def generate_file(self, filepath, contents):
        file = open(filepath, "w")
        file.write(contents)
        file.close()

        message="Please select a text editor .exe such as Notepad or Notepad++.\n\
This will be used as the default program for opening scripts."
        if (len(Configuration.script_editor) == 0):
            try:
                os.startfile(filepath)
            except:
                bpy.ops.screen.display_error('INVOKE_DEFAULT', message=message)
        else:
            try:
                process = subprocess.Popen([Configuration.script_editor, filepath])
            except:
                bpy.ops.screen.display_error('INVOKE_DEFAULT', message=message)


#------------------------------------------------------------------------------
# CryBlend
# Interface:
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

 
class CryBlendPanel(PropPanel, Panel): 
    bl_label = "CryBlend" 

    def draw(self, context): 
        layout = self.layout 

        col = layout.column(align=True) 
        col.label(text="Configuration Paths", icon="SCRIPT") 
        col.separator() 
        row = col.row(align=True) 
        row.operator("file.find_rc", text="Find RC") 
        row.operator("file.find_rc_for_texture_conversion", text="Find Texture RC") 
        row = col.row(align=True) 
        row.operator("file.select_textures_directory", text="Select Textures Folder") 
        col.separator() 
        col.operator("scene.export_to_game", icon="GAME") 


class AddPhysicsProxyMenu(bpy.types.Menu):
    bl_label = "Add Physics Proxy"
    bl_idname = "menu.add_physics_proxy"

    def draw(self, context):
        layout = self.layout

        add_box_proxy = layout.operator("object.add_proxy", text="Box", icon="META_CUBE")
        add_box_proxy.type = "box"
        add_capsule_proxy = layout.operator("object.add_proxy", text="Capsule", icon="META_ELLIPSOID")
        add_capsule_proxy.type = "capsule"
        add_cylinder_proxy = layout.operator("object.add_proxy", text="Cylinder", icon="META_CAPSULE")
        add_cylinder_proxy.type = "cylinder"
        add_sphere_proxy = layout.operator("object.add_proxy", text="Sphere", icon="META_BALL")
        add_sphere_proxy.type = "sphere"


class MeshRepairToolsMenu(bpy.types.Menu):
    bl_label = "Weight Paint Repair"
    bl_idname = "menu.weight_paint_repair"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Configuration Paths", icon="SCRIPT")
        col.separator()
        row = col.row(align=True)
        row.operator("file.find_rc", text="Find RC")
        row.operator("file.find_rc_for_texture_conversion", text="Find Texture RC")
        row = col.row(align=True)
        row.operator("file.select_textures_directory", text="Select Textures Folder")
        col.separator()
        col.operator("scene.export_to_game", icon="GAME")


class ExportUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Export Utilities"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label("Nodes:", icon="GROUP")
        col.separator()
        col.operator("object.add_cry_export_node", text="Add ExportNode")
        col.operator("object.selected_to_cry_export_nodes", text="ExportNodes from Objects")
        col.separator()

        col.label("Animation:", icon="POSE_HLT")
        col.separator()
        col.operator("object.add_anim_node")


class CryUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Cry Utilities"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label("Materials:", icon="MATERIAL")
        col.separator()
        col.operator("material.set_material_names", text="Update Material Names")
        col.operator("material.remove_cry_blend_properties", text="Remove Material Properties")
        col.separator()

        col.label("Add Physics Proxy", icon="ROTATE")
        col.separator()
        row = col.row(align=True)
        add_box_proxy = row.operator("object.add_proxy", text="Box")
        add_box_proxy.type = "box"
        add_capsule_proxy = row.operator("object.add_proxy", text="Capsule")
        add_capsule_proxy.type = "capsule"

        row = col.row(align=True)
        add_cylinder_proxy = row.operator("object.add_proxy", text="Cylinder")
        add_cylinder_proxy.type = "cylinder"
        add_sphere_proxy = row.operator("object.add_proxy", text="Sphere")
        add_sphere_proxy.type = "sphere"
        col.separator()

        col.label("Breakables:", icon="PARTICLES")
        col.separator()
        col.operator("object.add_joint")
        col.separator()

        col.label("Touch-Bending:", icon="MOD_SIMPLEDEFORM")
        col.separator()
        col.operator("mesh.add_branch")
        col.operator("mesh.add_branch_joint")


class BonePhysicsPanel(View3DPanel, Panel):
    bl_label = "Bone Physics"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="Physics", icon="PHYSICS")
        col.separator()
        col.operator("armature.add_bone_geometry")
        col.operator("armature.remove_bone_geometry")
        col.operator("armature.rename_phys_bones")


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
        layout.menu("menu.add_property")


class HelpPanel(View3DPanel, Panel):
    bl_label = "Help"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="Resources", icon='QUESTION')
        col.separator()
        col.operator("file.open_crydev_webpage", text = "CryDev Forums")
        col.operator("file.open_github_webpage", text = "CryBlend Wiki")
        col.operator("file.open_cryengine_docs_webpage", text = "CryEngine Docs")


class CryBlendMainMenu(bpy.types.Menu):
    bl_label = 'CryBlend'
    bl_idname = 'view3d.cryblend_main_menu'

    def draw(self, context):
        layout = self.layout

        # version number
        layout.label(text='v%s' % VERSION)
        # layout.operator("open_donate.wp", icon='FORCE_DRAG')
        layout.operator("object.add_cry_export_node", text="Add ExportNode", icon='GROUP')
        layout.operator("object.selected_to_cry_export_nodes", text="ExportNodes from Objects")
        layout.separator()

        layout.operator("object.add_anim_node", icon='POSE_HLT')
        layout.separator()

        layout.operator("material.set_material_names", text="Update Material Names", icon="MATERIAL")
        layout.operator("material.remove_cry_blend_properties", text="Remove Material Properties")
        layout.separator()

        layout.menu("menu.add_physics_proxy", icon="ROTATE")
        layout.separator()
        layout.menu(BonePhysicsMenu.bl_idname, icon='BONE_DATA')
        layout.separator()
        layout.menu(BreakablesMenu.bl_idname, icon='PARTICLES')
        layout.separator()
        layout.menu(TouchBendingMenu.bl_idname, icon='OUTLINER_OB_EMPTY')
        layout.separator()
        layout.menu(MeshUtilitiesMenu.bl_idname, icon='MESH_CUBE')
        layout.separator()
        layout.menu(CustomPropertiesMenu.bl_idname, icon='SCRIPT')
        layout.separator()
        layout.menu(GenerateScriptMenu.bl_idname, icon='TEXT')
        layout.separator()
        layout.menu(HelpMenu.bl_idname, icon='QUESTION')


class BonePhysicsMenu(bpy.types.Menu):
    bl_label = "Bone Physics"
    bl_idname = "view3d.bone_utilities"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Physics")
        layout.operator("armature.add_bone_geometry", icon="PHYSICS")
        layout.operator("armature.remove_bone_geometry", icon="PHYSICS")
        layout.operator("armature.rename_phys_bones", icon="PHYSICS")


class BreakablesMenu(bpy.types.Menu):
    bl_label = "Breakables"
    bl_idname = "view3d.breakables"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Add")
        layout.operator("object.add_joint", icon="PROP_ON")


class TouchBendingMenu(bpy.types.Menu):
    bl_label = "Touch Bending"
    bl_idname = "view3d.touch_bending"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Nodes")
        layout.operator("mesh.add_branch", icon='MOD_SIMPLEDEFORM')
        layout.operator("mesh.add_branch_joint", icon='EMPTY_DATA')


class MeshUtilitiesMenu(bpy.types.Menu):
    bl_label = "Mesh Utilities"
    bl_idname = "view3d.mesh_utilities"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Weight Repair")
        layout.operator("mesh.find_weightless", text="Find Weightless", icon="WPAINT_HLT")
        layout.operator("mesh.remove_weight", text="Remove Weight", icon="WPAINT_HLT")
        layout.separator()

        layout.label(text="Mesh Repair")
        layout.operator("object.find_degenerate_faces", text="Find Degenerate", icon='ZOOM_ALL')
        layout.operator("mesh.find_multiface_lines", text="Find Multi-face", icon='ZOOM_ALL')
        layout.separator()

        layout.label(text="UV Repair")
        layout.operator("scene.find_no_uvs", text="Find All Objects with No UV's", icon="UV_FACESEL")
        layout.operator("mesh.add_uv_texture", text="Add UV's to Objects", icon="UV_FACESEL")


class CustomPropertiesMenu(bpy.types.Menu):
    bl_label = "Add Property"
    bl_idname = "menu.add_property"

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        sub = row.column()
        sub.label("Rendermesh")
        sub.operator("object.add_mass_property", text="Mass", icon="FORCE_LENNARDJONES")
        sub.operator("object.add_density_property", text="Density", icon="BBOX")
        sub.operator("object.add_pieces_property", text="Pieces", icon="STICKY_UVS_DISABLE")
        sub.label(" ")
        sub.label(" ")
        sub.separator()
        sub.operator("object.add_entity_property", text="Entity", icon="FILE_TICK")
        sub.operator("object.add_dynamic_property", text="Dynamic", icon="FILE_TICK")
        sub.operator("object.add_no_hit_refinement_property", text="No Hit Refinement", icon="FILE_TICK")

        sub = row.column()
        sub.label("Physics Proxy")
        sub.operator("object.add_box_proxy_property", text="Box", icon="META_CUBE")
        sub.operator("object.add_cylinder_proxy_property", text="Cylinder", icon="META_CAPSULE")
        sub.operator("object.add_capsule_proxy_property", text="Capsule", icon="META_ELLIPSOID")
        sub.operator("object.add_sphere_proxy_property", text="Sphere", icon="META_BALL")
        sub.operator("object.add_notaprim_proxy_property", text="Not a Primitive", icon="X")
        sub.separator()
        sub.operator("object.add_no_explosion_occlusion_property", text="No Explosion Occlusion", icon="FILE_TICK")
        sub.operator("object.add_other_rendermesh_property", text="Other Rendermesh", icon="FILE_TICK")
        sub.operator("object.add_colltype_player_property", text="Colltype Player", icon="FILE_TICK")

        sub = row.column()
        sub.label("Joint Node")
        sub.operator("object.add_bend_property", text="Bend", icon="LINCURVE")
        sub.operator("object.add_twist_property", text="Twist", icon="MOD_SCREW")
        sub.operator("object.add_pull_property", text="Pull", icon="FULLSCREEN_ENTER")
        sub.operator("object.add_push_property", text="Push", icon="FULLSCREEN_EXIT")
        sub.operator("object.add_shift_property", text="Shift", icon="NEXT_KEYFRAME")
        sub.separator()
        sub.operator("object.add_gameplay_critical_property", text="Gameplay Critical", icon="FILE_TICK")
        sub.operator("object.add_player_can_break_property", text="Player Can Break", icon="FILE_TICK")

        sub = row.column()
        sub.label("Constraints")
        sub.operator("object.add_limit_constraint", text="Limit", icon="CONSTRAINT")
        sub.operator("object.add_min_angle_constraint", text="Min Angle", icon="ZOOMIN")
        sub.operator("object.add_max_angle_constraint", text="Max Angle", icon="ZOOMOUT")
        sub.label(" ")
        sub.label(" ")
        sub.separator()
        sub.operator("object.add_damping_constraint", text="Damping", icon="FILE_TICK")
        sub.operator("object.add_collision_constraint", text="Collision", icon="FILE_TICK")

        sub = row.column()
        sub.label("Other")
        sub.operator("object.add_deformable_properties", text="Deformable", icon="MOD_SIMPLEDEFORM")
        sub.operator("object.add_wheel_property", text="Wheel", icon="ROTATECOLLECTION")
        sub.label(" ")
        sub.label(" ")
        sub.label(" ")
        sub.separator()


class GenerateScriptMenu(bpy.types.Menu):
    bl_label = "Generate Script"
    bl_idname = "menu.generate_script"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Generate")
        layout.separator()
        chrparams_generator = layout.operator("wm.generate_script", text="CHRPARAMS", icon="SPACE2")
        chrparams_generator.type = "CHRPARAMS"
        cdf_generator = layout.operator("wm.generate_script", text="CDF", icon="SPACE2")
        cdf_generator.type = "CDF"
        ent_generator = layout.operator("wm.generate_script", text="ENT", icon="SPACE2")
        ent_generator.type = "ENT"
        lua_generator = layout.operator("wm.generate_script", text="LUA", icon="SPACE2")
        lua_generator.type = "LUA"
        layout.separator()
        layout.operator("file.select_script_editor", icon="TEXT")


class HelpMenu(bpy.types.Menu):
    bl_label = "Help"
    bl_idname = "view3d.help"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Resources")
        layout.operator("file.open_crydev_webpage", text = "CryDev Forums", icon='SPACE2')
        layout.operator("file.open_github_webpage", text = "CryBlend Wiki", icon='SPACE2')
        layout.operator("file.open_cryengine_docs_webpage", text = "CryEngine Docs", icon='SPACE2')


class AddMaterialPhysicsMenu(bpy.types.Menu):
    bl_label = "Add Material Physics"
    bl_idname = "menu.add_material_physics"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Add Material Physics")
        layout.separator()
        layout.operator("material.add_phys_default", text="__physDefault", icon='PHYSICS')
        layout.operator("material.add_phys_proxy_no_draw", text="__physProxyNoDraw", icon='PHYSICS')
        layout.operator("material.add_phys_none", text="__physNone", icon='PHYSICS')
        layout.operator("material.add_phys_obstruct", text="__physObstruct", icon='PHYSICS')
        layout.operator("material.add_phys_no_collide", text="__physNoCollide", icon='PHYSICS')


def get_classes_to_register():
    classes = (
        FindRC,
        FindRCForTextureConversion,
        SelectTexturesDirectory,
        SaveCryBlendConfiguration,

        AddCryExportNode,
        SelectedToCryExportNodes,
        SetMaterialNames,
        RemoveCryBlendProperties,
        AddAnimNode,
        AddProxy,
        AddBreakableJoint,
        AddBranch,
        AddBranchJoint,
        OpenCryDevWebpage,
        OpenGitHubWebpage,
        OpenCryEngineDocsWebpage,

        OpenUDPWebpage,
        AddMassProperty,
        AddDensityProperty,
        AddPiecesProperty,
        AddEntityProperty,
        AddNoHitRefinementProperty,
        AddDynamicProperty,

        AddBoxProxyProperty,
        AddCylinderProxyProperty,
        AddCapsuleProxyProperty,
        AddSphereProxyProperty,
        AddNotaprimProxyProperty,
        AddNoExplosionOcclusionProperty,
        AddOtherRendermeshProperty,
        AddColltypePlayerProperty,

        AddBendProperty,
        AddTwistProperty,
        AddPullProperty,
        AddPushProperty,
        AddShiftProperty,
        AddGameplayCriticalProperty,
        AddPlayerCanBreakProperty,

        AddLimitConstraint,
        AddMinAngleConstraint,
        AddMaxAngleConstraint,
        AddDampingConstraint,
        AddCollisionConstraint,

        AddDeformableProperties,
        AddWheelProperty,
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

        AddFakeBone,
        RemoveFakeBones,
        KeyframeFakebones,
        RenamePhysBones,
        AddBoneGeometry,
        RemoveBoneGeometry,

        Export,
        ErrorHandler,

        CryBlendPanel,

        ExportUtilitiesPanel,
        CryUtilitiesPanel,
        BonePhysicsPanel,
        MeshUtilitiesPanel,
        CustomPropertiesPanel,
        HelpPanel,

        CryBlendMainMenu,
        AddPhysicsProxyMenu,
        BonePhysicsMenu,
        BreakablesMenu,
        TouchBendingMenu,
        MeshUtilitiesMenu,
        CustomPropertiesMenu,
        GenerateScriptMenu,
        HelpMenu,

        AddMaterialPhysicsMenu,

        SelectScriptEditor,
        GenerateScript,
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
        kmi = km.keymap_items.new('wm.call_menu', 'Q', 'PRESS', ctrl = False, shift = True)
        kmi.properties.name = "view3d.cryblend_main_menu"

    bpy.types.INFO_HT_header.append(draw_item)
    bpy.types.MATERIAL_MT_specials.append(physics_menu)


def unregister():
    # you guys already know this but for my reference,
    # unregister your classes or when you do new scene
    # your script wont import other modules properly.
    for classToRegister in get_classes_to_register():
        bpy.utils.unregister_class(classToRegister)
        wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['3D View']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "view3d.cryblend_main_menu":
                    km.keymap_items.remove(kmi)
                    break

    bpy.types.INFO_HT_header.remove(draw_item)
    bpy.types.MATERIAL_MT_specials.remove(physics_menu)


if __name__ == "__main__":
    register()

    # The menu can also be called from scripts
    bpy.ops.wm.call_menu(name=ExportUtilitiesPanel.bl_idname)
