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
    "blender": (2, 60, 0),
    "version": (4, 12, 2, 4, "dev"),
    "location": "CryBlend Menu",
    "description": "CryEngine3 Utilities and Exporter",
    "warning": "",
    "wiki_url": "https://github.com/travnick/CryBlend/wiki",
    "tracker_url": "https://github.com/travnick/CryBlend/issues?state=open",
    "support": "OFFICIAL",
    "category": "Import-Export"}

# old wiki url: http://wiki.blender.org/
# index.php/Extensions:2.5/Py/Scripts/Import-Export/CryEngine3

VERSION = ".".join(str(n) for n in bl_info["version"])


if "bpy" in locals():
    import imp
    imp.reload(add)
    imp.reload(export)
    imp.reload(exceptions)
else:
    import bpy
    from io_export_cryblend import add, export, exceptions, utils

from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, \
    FloatProperty, StringProperty, IntProperty
from bpy.types import Menu, Panel
from bpy_extras.io_utils import ExportHelper
from io_export_cryblend.configuration import Configuration
from io_export_cryblend.outPipe import cbPrint
from xml.dom.minidom import Document, Element, parse
from bpy.app.handlers import persistent
import bmesh
import bpy.ops
import bpy_extras
import configparser
import os
import os.path
import pickle
import webbrowser
import re
import sys


# for help
new = 2  # open in a new tab, if possible

class PathSelectTemplate(ExportHelper):
    check_existing = True

    def execute(self, context):
        self.process(self.filepath)

        Configuration.save()
        return {"FINISHED"}


class FindRc(bpy.types.Operator, PathSelectTemplate):
    """Select the Resource Compiler executable"""

    bl_label = "Select RC"
    bl_idname = "file.find_rc"

    filename_ext = ".exe"

    def process(self, filepath):
        Configuration.rc_path = "%s" % filepath
        cbPrint("Found RC at {!r}.".format(Configuration.rc_path), "debug")

    def invoke(self, context, event):
        self.filepath = Configuration.rc_path

        return ExportHelper.invoke(self, context, event)


class FindRcForTextureConversion(bpy.types.Operator, PathSelectTemplate):
    """Select if you are using RC from cryengine \
newer than 3.4.5. Provide RC path from cryengine 3.4.5 \
to be able to export your textures as dds files"""

    bl_label = "Select Texture RC"
    bl_idname = "file.find_rc_for_texture_conversion"

    filename_ext = ".exe"

    def process(self, filepath):
        Configuration.rc_for_texture_conversion_path = "%s" % filepath
        cbPrint("Found RC at {!r}.".format(Configuration.rc_for_texture_conversion_path), "debug")

    def invoke(self, context, event):
        self.filepath = Configuration.rc_for_texture_conversion_path

        return ExportHelper.invoke(self, context, event)


class MenuTemplate():
    class Operator:
        def __init__(self, name="", icon=""):
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
    """Saves current CryBlend configuration"""
    bl_label = "Save Config File"
    bl_idname = "config.save"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        Configuration.save()
        return {"FINISHED"}


class AddBreakableJoint(bpy.types.Operator):
    """Click to add a pre-broken breakable joint to current selection"""
    bl_label = "Add Joint"
    bl_idname = "object.add_joint"

    def execute(self, context):
        return add.add_joint(self, context)


class AddCryExportNode(bpy.types.Operator):
    """Click to add selection to a CryExportNode"""
    bl_label = "Add CryExportNode"
    bl_idname = "object.add_cry_export_node"
    my_string = StringProperty(name="CryExportNode name")

    def execute(self, context):
        bpy.ops.group.create(name="CryExportNode_%s" % (self.my_string))
        message = "Adding CryExportNode_'%s'" % (self.my_string)
        self.report({"INFO"}, message)
        cbPrint(message)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def get_vertex_data():
    selected_vert_coordinates = [i.co for i in bpy.context.active_object.data.vertices if i.select] 
    return selected_vert_coordinates


def name_branch(is_new_branch):
    highest_branch_number = 0
    highest_joint_number = 0
    for object_ in bpy.context.scene.objects:
        if ((object_.type == "EMPTY") and ("branch" in object_.name)):
            branch_components = object_.name.split("_")
            if (branch_components):
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
                        


class AddBranch(bpy.types.Operator):
    """Click to add a branch at active vertex or first vertex in a set of vertices"""
    bl_label = "Add Branch"
    bl_idname = "mesh.add_branch"

    def execute(self, context):
        active_object = bpy.context.scene.objects.active
        bpy.ops.object.mode_set(mode="OBJECT")
        selected_vert_coordinates = get_vertex_data()
        if (selected_vert_coordinates):
            selected_vert = selected_vert_coordinates[0]
            bpy.ops.object.add(type="EMPTY", view_align=False, enter_editmode=False, location=(selected_vert[0], selected_vert[1], selected_vert[2]))
            empty_object = bpy.context.active_object
            empty_object.name = name_branch(is_new_branch=True)
            bpy.context.scene.objects.active = active_object
            bpy.ops.object.mode_set(mode="EDIT")
            message = "Adding Branch"
            self.report({"INFO"}, message)
            cbPrint(message)
        return {"FINISHED"}


class AddBranchJoint(bpy.types.Operator):
    """Click to add a branch joint at selected vertex or first vertex in a set of vertices"""
    bl_label = "Add Branch Joint"
    bl_idname = "mesh.add_branch_joint"

    def execute(self, context):
        active_object = bpy.context.scene.objects.active
        bpy.ops.object.mode_set(mode="OBJECT")
        selected_vert_coordinates = get_vertex_data()
        if (selected_vert_coordinates):
            selected_vert = selected_vert_coordinates[0]
            bpy.ops.object.add(type="EMPTY", view_align=False, enter_editmode=False, location=(selected_vert[0], selected_vert[1], selected_vert[2]))
            empty_object = bpy.context.active_object
            empty_object.name = name_branch(is_new_branch=False)
            bpy.context.scene.objects.active = active_object
            bpy.ops.object.mode_set(mode="EDIT")

            message = "Adding Branch Joint"
            self.report({"INFO"}, message)
            cbPrint(message)
        return {"FINISHED"}


class AddAnimNode(bpy.types.Operator):
    """Click to add an AnimNode to selection or with nothing selected
add an AnimNode to the scene"""
    bl_label = "Add AnimNode"
    bl_idname = "object.add_anim_node"
    my_string = StringProperty(name="Animation Name")
    start_frame = FloatProperty(name="Start Frame")
    end_frame = FloatProperty(name="End Frame")

    def execute(self, context):
        object_ = bpy.context.active_object

        # "add" selects added object
        bpy.ops.object.add(type="EMPTY")
        empty_object = bpy.context.active_object
        empty_object.name = "animnode"
        empty_object["animname"] = self.my_string
        empty_object["startframe"] = self.start_frame
        empty_object["endframe"] = self.end_frame

        if object_:
            object_.select = True
            bpy.context.scene.objects.active = object_

        bpy.ops.object.parent_set(type="OBJECT")
        message = "Adding AnimNode '%s'" % (self.my_string)
        self.report({"INFO"}, message)
        cbPrint(message)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddCharacterAnimation(bpy.types.Operator):
    """Click to add a new animation to character"""
    bl_label = "Add Character Animation"
    bl_idname = "file.add_character_animation"
    animation_name = StringProperty(name="Animation Name")

    def execute(self, context):
        chrparams_path = bpy.path.ensure_ext("%s/%s/%s/%s" % (utils.get_cry_root_path(), "Objects", utils.get_project_path(), utils.get_project_name()), ".chrparams")
        if (not os.path.exists(chrparams_path)):
            chrparams_contents = "<Params><AnimationList></AnimationList></Params>"
            chrparams_file = open(chrparams_path, "w")
            chrparams_file.write(chrparams_contents)
            chrparams_file.close()

        chrparams_file = parse(chrparams_path)

        animation = chrparams_file.createElement("Animation")
        animation.setAttribute("name", self.animation_name)
        animation.setAttribute("path", bpy.path.ensure_ext(self.animation_name, ".caf"))
        animation_list = chrparams_file.getElementsByTagName("AnimationList")[0]
        animation_list.appendChild(animation)

        pretty_xml = chrparams_file.toprettyxml(indent="  ")
        pretty_xml = "".join([s for s in pretty_xml.splitlines(True) if s.strip("\r\n\t ")])
        new_xml = open(chrparams_path, "w")
        new_xml.write(pretty_xml)
        new_xml.close()

        bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath)
        blend_path = bpy.data.filepath[:-6]
        blend_anim_path = bpy.path.ensure_ext("%s_anim_%s" % (blend_path, self.animation_name), ".blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_anim_path)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def rename_character_animation():
    old_blend_path = bpy.data.filepath
    new_blend_path = bpy.path.ensure_ext("%s_anim_%s" % (blend_path, self.animation_name), ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_anim_path)


class OpenCryDevWebpage(bpy.types.Operator):
    """A link to CryDev"""
    bl_label = "Visit CryDev Forums"
    bl_idname = "file.open_crydev_webpage"

    def execute(self, context):
        url = "http://www.crydev.net/viewtopic.php?f=315&t=103136"
        webbrowser.open(url, new=new)
        self.report({"INFO"}, self.message)
        cbPrint(self.message)
        return {"FINISHED"}


class OpenGitHubWebpage(bpy.types.Operator):
    """A link to GitHub"""
    bl_label = "Visit CryBlend Tutorial Wiki"
    bl_idname = "file.open_github_webpage"

    def execute(self, context):
        url = "https://github.com/travnick/CryBlend/wiki/users-area"
        webbrowser.open(url, new=new)
        self.report({"INFO"}, self.message)
        cbPrint(self.message)
        return {"FINISHED"}


class OpenCryEngineDocsWebpage(bpy.types.Operator):
    """A link to the CryEngine Docs"""
    bl_label = "Visit CryEngine Docs Page"
    bl_idname = "file.open_cryengine_docs_webpage"

    def execute(self, context):
        url = "http://docs.cryengine.com/display/SDKDOC1/Home"
        webbrowser.open(url, new=new)
        self.report({"INFO"}, self.message)
        cbPrint(self.message)
        return {"FINISHED"}


#------------------------------------------------------------------------------
# CryEngine User
# Defined Properties:
#------------------------------------------------------------------------------


class OpenUDPWebpage(bpy.types.Operator):
    """A link to UDP"""
    bl_label = "Open Web Page for UDP"
    bl_idname = "file.open_udp_webpage"

    def execute(self, context):
        url = "http://freesdk.crydev.net/display/SDKDOC3/UDP+Settings"
        webbrowser.open(url, new=new)
        self.report({"INFO"}, self.message)
        cbPrint(self.message)
        return {"FINISHED"}


# Rendermesh:
class AddEntityProperty(bpy.types.Operator):
    """Click to add an entity property"""
    bl_label = "Entity"
    bl_idname = "object.add_entity_property"

    def execute(self, context):
        message = "Adding Entity Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_entity_property(self, context)


class AddMassProperty(bpy.types.Operator):
    """Click to add a mass value"""
    bl_label = "Mass"
    bl_idname = "object.add_mass_property"
    mass = FloatProperty(name="Mass")

    def execute(self, context):
        message = "Adding Mass of %s" % (self.mass)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_mass_property(self, context, self.mass)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddDensityProperty(bpy.types.Operator):
    """Click to add a density value"""
    bl_label = "Density"
    bl_idname = "object.add_density_property"
    density = FloatProperty(name="Density")

    def execute(self, context):
        message = "Adding Density of %s" % (self.density)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_density_property(self, context, self.density)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddPiecesProperty(bpy.types.Operator):
    """Click to add a pieces value"""
    bl_label = "Pieces"
    bl_idname = "object.add_pieces_property"
    pieces = FloatProperty(name="Pieces")

    def execute(self, context):
        message = "Adding %s Pieces" % (self.pieces)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_pieces_property(self, context, self.pieces)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddDynamicProperty(bpy.types.Operator):
    """Click to add a dynamic property"""
    bl_label = "Dynamic"
    bl_idname = "object.add_dynamic_property"

    def execute(self, context):
        message = "Adding Dynamic Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_dynamic_property(self, context)


class AddNoHitRefinementProperty(bpy.types.Operator):
    """Click to add a no hit refinement property"""
    bl_label = "No Hit Refinement"
    bl_idname = "object.add_no_hit_refinement_property"

    def execute(self, context):
        message = "Adding No Hit Refinement Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_no_hit_refinement_property(self, context)


# Phys Proxy:
class AddBoxProxyProperty(bpy.types.Operator):
    """Click to add a col proxy"""
    bl_label = "Box"
    bl_idname = "object.add_box_proxy_property"

    def execute(self, context):
        message = "Adding Box Proxy Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_box_proxy_property(self, context)


class AddCylinderProxyProperty(bpy.types.Operator):
    """Click to add a cylinder proxy"""
    bl_label = "Cylinder"
    bl_idname = "object.add_cylinder_proxy_property"

    def execute(self, context):
        message = "Adding Cylinder Proxy Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_cylinder_proxy_property(self, context)


class AddCapsuleProxyProperty(bpy.types.Operator):
    """Click to add a capsule proxy"""
    bl_label = "Capsule"
    bl_idname = "object.add_capsule_proxy_property"

    def execute(self, context):
        message = "Adding Capsule Proxy Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_capsule_proxy_property(self, context)


class AddSphereProxyProperty(bpy.types.Operator):
    """Click to add a sphere proxy"""
    bl_label = "Sphere"
    bl_idname = "object.add_sphere_proxy_property"

    def execute(self, context):
        message = "Adding Sphere Proxy Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_sphere_proxy_property(self, context)


class AddNotaprimProxyProperty(bpy.types.Operator):
    """Click to add a 'not a primitive' proxy property"""
    bl_label = "Not a Primitive"
    bl_idname = "object.add_notaprim_proxy_property"

    def execute(self, context):
        message = "Adding 'Not a Primitive' Proxy Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_notaprim_proxy_property(self, context)


class AddNoExplosionOcclusionProperty(bpy.types.Operator):
    """Click to add a no explosion occlusion property"""
    bl_label = "No Explosion Occlusion"
    bl_idname = "object.add_no_explosion_occlusion_property"

    def execute(self, context):
        message = "Adding No Explosion Occlusion Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_no_explosion_occlusion_property(self, context)


class AddOtherRendermeshProperty(bpy.types.Operator):
    """Click to add an other rendermesh property"""
    bl_label = "Other Rendermesh"
    bl_idname = "object.add_other_rendermesh_property"

    def execute(self, context):
        message = "Adding Other Rendermesh Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_other_rendermesh_property(self, context)


class AddColltypePlayerProperty(bpy.types.Operator):
    """Click to add a colltype player property"""
    bl_label = "Colltype Player"
    bl_idname = "object.add_colltype_player_property"

    def execute(self, context):
        message = "Adding Colltype Player Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_colltype_player_property(self, context)


# Joint Node:
class AddBendProperty(bpy.types.Operator):
    """Click to add a bend property"""
    bl_label = "Bend"
    bl_idname = "object.add_bend_property"
    bendValue = FloatProperty(name="Bend Value")

    def execute(self, context):
        message = "Adding Bend Value of %s" % (self.bendValue)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_bend_property(self, context, self.bendValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddTwistProperty(bpy.types.Operator):
    """Click to add a twist property"""
    bl_label = "Twist"
    bl_idname = "object.add_twist_property"
    twistValue = FloatProperty(name="Twist Value")

    def execute(self, context):
        message = "Adding Twist Value of %s" % (self.twistValue)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_twist_property(self, context, self.twistValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddPullProperty(bpy.types.Operator):
    """Click to add a pull property"""
    bl_label = "Pull"
    bl_idname = "object.add_pull_property"
    pullValue = FloatProperty(name="Pull Value")

    def execute(self, context):
        message = "Adding Pull Value of %s" % (self.pullValue)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_pull_property(self, context, self.pullValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddPushProperty(bpy.types.Operator):
    """Click to add a push property"""
    bl_label = "Push"
    bl_idname = "object.add_push_property"
    pushValue = FloatProperty(name="Push Value")

    def execute(self, context):
        message = "Adding Push Value of %s" % (self.pushValue)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_push_property(self, context, self.pushValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddShiftProperty(bpy.types.Operator):
    """Click to add a shift property"""
    bl_label = "Shift"
    bl_idname = "object.add_shift_property"
    shiftValue = FloatProperty(name="Shift Value")

    def execute(self, context):
        message = "Adding Shift Value of %s" % (self.shiftValue)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_shift_property(self, context, self.shiftValue)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddGameplayCriticalProperty(bpy.types.Operator):
    """Click to add a critical property"""
    bl_label = "Gameplay Critical"
    bl_idname = "object.add_gameplay_critical_property"

    def execute(self, context):
        message = "Adding Gameplay Critical Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_gameplay_critical_property(self, context)


class AddPlayerCanBreakProperty(bpy.types.Operator):
    """Click to add a breakable property"""
    bl_label = "Player Can Break"
    bl_idname = "object.add_player_can_break_property"

    def execute(self, context):
        message = "Adding Player Can Break Property"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_player_can_break_property(self, context)


# Constraints:
class AddLimitConstraint(bpy.types.Operator):
    """Click to add a limit constraint"""
    bl_label = "Limit"
    bl_idname = "object.add_limit_constraint"
    limit = FloatProperty(name="Limit")

    def execute(self, context):
        message = "Adding Limit of %s" % (self.limit)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_limit_constraint(self, context, self.limit)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddMinAngleConstraint(bpy.types.Operator):
    """Click to add a min angle constraint"""
    bl_label = "Min Angle"
    bl_idname = "object.add_min_angle_constraint"
    minAngle = FloatProperty(name="Min Angle")

    def execute(self, context):
        message = "Adding Min Angle of %s" % (self.minAngle)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_min_angle_constraint(self, context, self.minAngle)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class AddMaxAngleConstraint(bpy.types.Operator):
    """Click to add a max angle constraint"""
    bl_label = "Max Angle"
    bl_idname = "object.add_max_angle_constraint"
    maxAngle = FloatProperty(name="Max Angle")

    def execute(self, context):
        message = "Adding Max Angle of %s" % (self.maxAngle)
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_max_angle_constraint(self, context, self.maxAngle)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddDampingConstraint(bpy.types.Operator):
    """Click to add a damping constraint"""
    bl_label = "Damping"
    bl_idname = "object.add_damping_constraint"

    def execute(self, context):
        message = "Adding Damping Constraint"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_damping_constraint(self, context)


class AddCollisionConstraint(bpy.types.Operator):
    """Click to add a collision constraint"""
    bl_label = "Collision"
    bl_idname = "object.add_collision_constraint"

    def execute(self, context):
        message = "Adding Collision Constraint"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_collision_constraint(self, context)


# Deformables:
class AddDeformableProperties(bpy.types.Operator):
    """Click to add a deformable mesh property"""
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
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_deformable_properties(self, context, self.mass, self.stiffness, self.hardness,
        self.max_stretch, self.max_impulse, self.skin_dist, self.thickness, self.explosion_scale, self.is_primitive)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


# Vehicles:
class AddWheelProperty(bpy.types.Operator):
    """Click to add a wheels property"""
    bl_label = "Add Wheel Properties"
    bl_idname = "object.add_wheel_property"

    def execute(self, context):
        message = "Adding Wheel Properties"
        self.report({"INFO"}, message)
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

        return {"FINISHED"}


# Material Physics:
class AddMaterialPhysDefault(bpy.types.Operator):
    """__physDefault will be added to the material name"""
    bl_label = "__physDefault"
    bl_idname = "material.add_phys_default"

    def execute(self, context):
        message = "Adding __physDefault"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_phys_default(self, context)


class AddMaterialPhysProxyNoDraw(bpy.types.Operator):
    """__physProxyNoDraw will be added to the material name"""
    bl_label = "Add __physProxyNoDraw to Material Name"
    bl_idname = "material.add_phys_proxy_no_draw"

    def execute(self, context):
        message = "Adding __physProxyNoDraw"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_phys_proxy_no_draw(self, context)


class AddMaterialPhysNone(bpy.types.Operator):
    """__physNone will be added to the material name"""
    bl_label = "__physNone"
    bl_idname = "material.add_phys_none"

    def execute(self, context):
        message = "Adding __physNone"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_phys_none(self, context)


class AddMaterialPhysObstruct(bpy.types.Operator):
    """__physObstruct will be added to the material name"""
    bl_label = "__physObstruct"
    bl_idname = "material.add_phys_obstruct"

    def execute(self, context):
        return add.add_phys_obstruct(self, context)


class AddMaterialPhysNoCollide(bpy.types.Operator):
    """__physNoCollide will be added to the material name"""
    bl_label = "__physNoCollide"
    bl_idname = "material.add_phys_no_collide"

    def execute(self, context):
        message = "Adding __physNoCollide"
        self.report({"INFO"}, message)
        cbPrint(message)
        return add.add_phys_no_collide(self, context)


#------------------------------------------------------------------------------
# Mesh and Weight
# Repair Tools:
#------------------------------------------------------------------------------


class FindDegenerateFaces(bpy.types.Operator):
    """Select the object to test in object mode with nothing selected in \
it"s mesh before running this."""
    bl_label = "Find Degenerate Faces"
    bl_idname = "object.find_degenerate_faces"

    # Minimum face area to be considered non-degenerate
    area_epsilon = 0.000001

    def execute(self, context):
        """ Vertices data should be actually manipulated in Object mode
            to be displayed in Edit mode correctly"""
        saved_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        active_object = bpy.context.active_object

        vert_list = [vert for vert in active_object.data.vertices]
        context.tool_settings.mesh_select_mode = (True, False, False)
        cbPrint("Locating degenerate faces.")
        degenerate_count = 0

        for poly in active_object.data.polygons:
            if poly.area < self.area_epsilon:
                cbPrint("Found a degenerate face.")
                degenerate_count += 1

                for vert in poly.vertices:
                    cbPrint("Selecting face vertices.")
                    vert_list[vert].select = True

        if degenerate_count > 0:
            bpy.ops.object.mode_set(mode="EDIT")
            self.report({"WARNING"},
                        "Found %i degenerate faces." % degenerate_count)
        else:
            self.report({"INFO"}, "No degenerate faces found.")
            # Restore the original mode
            bpy.ops.object.mode_set(mode=saved_mode)

        return {"FINISHED"}


# Duo Oratar
class FindMultifaceLines(bpy.types.Operator):
    """Select the object to test in object mode with nothing selected in \
it"s mesh before running this."""
    bl_label = "Find Lines with 3+ Faces."
    bl_idname = "mesh.find_multiface_lines"

    def execute(self, context):
        active_object = bpy.context.active_object
        vert_list = [vert for vert in active_object.data.vertices]
        context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.object.mode_set(mode="OBJECT")
        cbPrint("Locating degenerate faces.")
        for edge in active_object.data.edges:
            counter = 0
            for poly in active_object.data.polygons:
                if (edge.vertices[0] in poly.vertices
                    and edge.vertices[1] in poly.vertices):
                    counter += 1
            if counter > 2:
                cbPrint("Found a multi-face line")
                for v in edge.vertices:
                    cbPrint("Selecting line vertices.")
                    vert_list[v].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


class FindWeightless(bpy.types.Operator):
    """Select the object in object mode with nothing in its mesh selected before running this"""
    bl_label = "Find Weightless Vertices"
    bl_idname = "mesh.find_weightless"

    def execute(self, context):
        active_object = bpy.context.active_object
        if active_object.type == "MESH":
            for vert in active_object.data.vertices:
                vert.select = True
                for group in vert.groups:
                    vert.select = False
                    break
        return {"FINISHED"}


class RemoveAllWeight(bpy.types.Operator):
    """Select vertices from which to remove weight in edit mode"""
    bl_label = "Remove All Weight from Selected Vertices"
    bl_idname = "mesh.remove_weight"

    def execute(self, context):
        active_object = bpy.context.active_object
        if active_object.type == "MESH":
            verts = []
            for vert in active_object.data.vertices:
                if vert.select:
                    verts.append(vert)
            for vert in verts:
                for group in vert.groups:
                    group.weight = 0
        return {"FINISHED"}


class FindNoUVs(bpy.types.Operator):
    """Use this with no objects selected in object mode
to find all items without UVs"""
    bl_label = "Find All Objects with No UVs"
    bl_idname = "scene.find_no_uvs"

    def execute(self, context):
        for object_ in bpy.data.objects:
            object_.select = False

        for object_ in bpy.context.selectable_objects:
            if object_.type == "MESH":
                if (not object_.data.uv_textures):
                    object_.select = True
        return {"FINISHED"}

#------------------------------------------------------------------------------
# Regarding Fakebones
# And BoneGeometry:
#------------------------------------------------------------------------------

# WARNING!!
# This cleans out all meshes without users!!!

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

    # Apply size
    for index, vert in enumerate(verts):
        verts[index] = vert[0] * width, vert[1] * depth, vert[2] * height

    return verts, faces


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


# Duo Oratar
class RenamePhysBones(bpy.types.Operator):
    """Renames phys bones"""
    bl_label = "Rename Phys Bones"
    bl_idname = "armature.rename_phys_bones"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for object_ in bpy.context.scene.objects:
            if ("_Phys" == object_.name[-5:]
                and object_.type == "ARMATURE"):
                for bone in object_.data.bones:
                    bone.name = "%s_Phys" % bone.name
        return {"FINISHED"}


class AddBoneGeometry(bpy.types.Operator):
    """Add BoneGeometry for bones in selected armatures"""
    bl_label = "Add BoneGeometry"
    bl_idname = "armature.add_bone_geometry"
    bl_options = {"REGISTER", "UNDO"}

    view_align = BoolProperty(
            name="Align to View",
            default=False,
            )
    location = FloatVectorProperty(
            name="Location",
            subtype="TRANSLATION",
            )
    rotation = FloatVectorProperty(
            name="Rotation",
            subtype="EULER",
            )

    def execute(self, context):
        verts_loc, faces = add_bone_geometry()

        nameList = []
        for object_ in bpy.context.scene.objects:
            nameList.append(object_.name)

        for object_ in bpy.context.scene.objects:
            if object_.type == "ARMATURE" and object_.select:

                physBonesList = []
                if "%s_Phys" % object_.name in nameList:
                    for bone in bpy.data.objects["%s_Phys" % object_.name].data.bones:
                        physBonesList.append(bone.name)

                for bone in object_.data.bones:
                    if (("%s_boneGeometry" % bone.name not in nameList
                            and "%s_Phys" % object_.name not in nameList)
                        or ("%s_Phys" % object_.name in nameList
                            and "%s_Phys" % bone.name in physBonesList
                            and "%s_boneGeometry" % bone.name not in nameList)
                        ):
                        mesh = bpy.data.meshes.new(
                                    "%s_boneGeometry" % bone.name
                        )
                        bm = bmesh.new()

                        for vert_co in verts_loc:
                            bm.verts.new(vert_co)

                        for face_index in faces:
                            bm.faces.new([bm.verts[i] for i in face_index])

                        bm.to_mesh(mesh)
                        mesh.update()
                        bone_matrix = bone.head_local
                        self.location[0] = bone_matrix[0]
                        self.location[1] = bone_matrix[1]
                        self.location[2] = bone_matrix[2]
                        # add the mesh as an object into the scene
                        # with this utility module
                        from bpy_extras import object_utils
                        object_utils.object_data_add(
                            context, mesh, operator=self
                        )
                        bpy.ops.mesh.uv_texture_add()

        return {"FINISHED"}


class RemoveBoneGeometry(bpy.types.Operator):
    """Remove BoneGeometry for bones in selected armatures"""
    bl_label = "Remove BoneGeometry"
    bl_idname = "armature.remove_bone_geometry"
    bl_options = {"REGISTER", "UNDO"}

    view_align = BoolProperty(
            name="Align to View",
            default=False,
            )
    location = FloatVectorProperty(
            name="Location",
            subtype="TRANSLATION",
            )
    rotation = FloatVectorProperty(
            name="Rotation",
            subtype="EULER",
            )

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")

        armature_list = []  # Get list of armatures requiring attention
        for object_ in bpy.context.scene.objects:
            if object_.type == "ARMATURE" and object_.select:  # Get selected armatures
                armature_list.append(object_.name)

        name_list = []  # Get list of objects
        for object_ in bpy.context.scene.objects:
            name_list.append(object_.name)
            object_.select = False

        for name in armature_list:
            object_ = bpy.context.scene.objects[name]
            phys_bone_list = []
            # Get list of phys bones in matching phys skel
            if "%s_Phys" % object_.name in name_list:
                for bone in bpy.data.objects["%s_Phys" % object_.name].data.bones:
                    phys_bone_list.append(bone.name)

            for bone in object_.data.bones:  # For each bone
                if "%s_boneGeometry" % bone.name in name_list:
                    bpy.data.objects["%s_boneGeometry" % bone.name].select = True

            bpy.ops.object.delete()

        return {"FINISHED"}


# verts and faces
# find bone heads and add at that location
class AddFakeBone(bpy.types.Operator):
    """Add a simple box mesh"""
    bl_label = "Add FakeBone"
    bl_idname = "armature.add_fake_bone"
    bl_options = {"REGISTER", "UNDO"}

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
            subtype="TRANSLATION",
            )
    rotation = FloatVectorProperty(
            name="Rotation",
            subtype="EULER",
            )

    def execute(self, context):
        verts_loc, faces = add_fake_bone(1, 1, 1)
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        scene_objects = bpy.context.scene.objects
        for armature in scene_objects:
            if armature.type == "ARMATURE":

                for posebone in armature.pose.bones:
                    mesh = bpy.data.meshes.new("%s" % posebone.name)
                    bm = bmesh.new()

                    for vert_co in verts_loc:
                        bm.verts.new(vert_co)

                    for face_index in faces:
                        bm.faces.new([bm.verts[i] for i in face_index])

                    bm.to_mesh(mesh)
                    mesh.update()
                    bone_matrix = posebone.bone.head_local
                    self.location[0] = bone_matrix[0]
                    self.location[1] = bone_matrix[1]
                    self.location[2] = bone_matrix[2]
                    # add the mesh as an object into the scene
                    # with this utility module
                    from bpy_extras import object_utils
                    object_utils.object_data_add(context, mesh, operator=self)
                    bpy.ops.mesh.uv_texture_add()
                    for object_ in scene_objects:
                        if object_.name == posebone.name:
                            object_["fakebone"] = "fakebone"
                    bpy.context.scene.objects.active = armature
                    armature.data.bones.active = posebone.bone
                    bpy.ops.object.parent_set(type="BONE")

        return {"FINISHED"}


class RemoveFakeBones(bpy.types.Operator):
        """Select to remove all fakebones from the scene"""
        bl_label = "Remove All FakeBones"
        bl_idname = "scene.remove_fake_bones"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            for object_ in bpy.data.objects:
                object_.select = False

            for object_ in bpy.context.selectable_objects:
                is_fake_bone = False
                try:
                    throwaway = object_["fakebone"]
                    is_fake_bone = True
                except:
                    pass
                if (object_.name == object_.parent_bone
                    and is_fake_bone
                    and object_.type == "MESH"):
                    object_.select = True
                    bpy.ops.object.delete(use_global=False)
            return {"FINISHED"}


# fakebones
# keyframe insert for fake bones
location_list = []
rotation_list = []


def add_fake_bone_keyframe_list(self, context):
    """do the inverse parent times current to get proper info here"""
    scene = bpy.context.scene
    armature = None
    for object_ in bpy.context.scene.objects:
        if object_.type == "ARMATURE":
            armature = object_
    bpy.ops.screen.animation_play()

    if armature is not None:
        for frame in range(scene.frame_end + 1):
            cbPrint("Stage 1 auto-keyframe.")
            scene.frame_set(frame)
            for posebone in armature.pose.bones:
                if posebone.parent is not None:
                    if posebone.parent.parent is not None:
                        for parent_bone in bpy.context.scene.objects:
                            if parent_bone.name == posebone.parent.name:
                                parent_bone_matrix = parent_bone.matrix_local
                        for child_bone in bpy.context.scene.objects:
                            if child_bone.name == posebone.name:
                                child_bone_matrix = child_bone.matrix_local
                        animatrix = parent_bone_matrix.inverted() * child_bone_matrix
                        location_matrix, rotation_matrix, scale_matrix = animatrix.decompose()
                        location = [frame, posebone.name, location_matrix]
                        rotation = [frame, posebone.name, rotation_matrix.to_euler()]
                        location_list.append(location)
                        rotation_list.append(rotation)
                    else:
                        for i in bpy.context.scene.objects:
                            if i.name == posebone.name:
                                location_matrix, rotation_matrix, scale_matrix = i.matrix_local.decompose()
                                location = [frame, posebone.name, location_matrix]
                                rotation = [frame, posebone.name, rotation_matrix.to_euler()]
                                location_list.append(location)
                                rotation_list.append(rotation)
                else:
                    for i in bpy.context.scene.objects:
                        if i.name == posebone.name:
                            location_matrix, rotation_matrix, scale_matrix = i.matrix_local.decompose()
                            location = [frame, posebone.name, location_matrix]
                            rotation = [frame, posebone.name, rotation_matrix.to_euler()]
                            location_list.append(location)
                            rotation_list.append(rotation)
        bpy.ops.screen.animation_play()
    return {"FINISHED"}


def add_fake_bone_keyframe(self, context):
    scene = bpy.context.scene
    current_frame = scene.frame_current
    armature = None
    for object_ in bpy.context.scene.objects:
        if object_.type == "ARMATURE":
            armature = object_
            break

    if armature is not None:
        for posebone in armature.pose.bones:
            fakebone = bpy.context.scene.objects.get(posebone.name)
            if fakebone is not None:
                for index in len(location_list):
                    location = location_list[index]
                    rotation = rotation_list[index]
                    if location[0] == current_frame:
                        if location[1] == posebone.name:
                            cbPrint("location: %s" % location[2])
                            fakebone.location = location[2]
                            fakebone.keyframe_insert(data_path="location")
                    if rotation[0] == current_frame:
                        if rotation[1] == posebone.name:
                            cbPrint("rotation: %s" % rotation[2])
                            fakebone.rotation_euler = rotation[2]
                            fakebone.keyframe_insert(data_path="rotation_euler")
    return {"FINISHED"}


# fakebone keyframe
class AddFakeBoneKeyframeList(bpy.types.Operator):
    """Adds a key frame list to fakebones"""
    bl_label = "Make Fakebone Keyframes List"
    bl_idname = "armature.add_fakebone_keyframe_list"

    def execute(self, context):
        return add_fake_bone_keyframe_list(self, context)


class AddFakeBoneKeyframe(bpy.types.Operator):
    """Adds a key frame to fakebone"""
    bl_label = "Add Fakebone Keyframe"
    bl_idname = "armature.add_fakebone_keyframe"

    def execute(self, context):
        return add_fake_bone_keyframe(self, context)


def fix_name():
    name = getattr(bpy.context.scene, "project_name")
    setattr(bpy.context.scene, "project_name", name.replace("\\", "/"))
    return {"FINISHED"}


def validify_project():
    name = getattr(bpy.context.scene, "project_name")
    if (name == ""):
        return False
    elif ("." in name):
        return False

    if ("\\" in name):
        fix_name()
    return True


class ExportSettings(bpy.types.Operator):
    """Select to edit export settings"""
    bl_label = "Export Settings"
    bl_idname = "scene.export_settings"

    bpy.types.Scene.merge_anm = BoolProperty(
            name="Merge Animations",
            description="For animated models - merge animations into 1.",
            default=False,
            )
    bpy.types.Scene.donot_merge = BoolProperty(
            name="Do Not Merge Nodes",
            description="Generally a good idea.",
            default=True,
            )
    bpy.types.Scene.avg_pface = BoolProperty(
            name="Average Planar Face Normals",
            description="Help align face normals that have normals that are within 1 degree.",
            default=False,
            )
    bpy.types.Scene.run_rc = BoolProperty(
            name="Run RC",
            description="Run the RC on export.",
            default=True,
            )
    bpy.types.Scene.do_materials = BoolProperty(
            name="Run RC and Do Materials",
            description="Create material files on export.",
            default=True,
            )
    bpy.types.Scene.convert_source_image_to_dds = BoolProperty(
            name="Convert Textures to DDS",
            description="Converts source textures to DDS while exporting materials.",
            default=True,
            )
    bpy.types.Scene.save_tiff_during_conversion = BoolProperty(
            name="Save TIFF During Conversion",
            description="Saves TIFF images that are generated during conversion to DDS.",
            default=False,
            )
    bpy.types.Scene.refresh_rc = BoolProperty(
            name="Refresh RC Output",
            description="Generally a good idea.",
            default=True,
            )
    bpy.types.Scene.include_ik = BoolProperty(
            name="Include IK in Character",
            description="Adds IK from your skeleton to the phys skeleton upon export.",
            default=True,
            )
    bpy.types.Scene.correct_weight = BoolProperty(
            name="Correct Weights",
            description="For use with .chr files.",
            default=True,
            )
    bpy.types.Scene.make_layer = BoolProperty(
            name="Make .lyr File",
            description="Makes a .lyr to reassemble your scene in the CryEngine 3.",
            default=False,
            )
    bpy.types.Scene.run_in_profiler = BoolProperty(
            name="Profile CryBlend",
            description="Select only if you want to profile CryBlend.",
            default=False,
            )
    bpy.types.Scene.generate_scripts = BoolProperty(
            name="Auto-Generate Scripts",
            description="Automatically generates necessary scripts.",
            default=True,
            )

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout

        layout.label("General", icon="MESH_DATA")
        row = layout.row()
        split = row.split(percentage=0.05)
        col = split.column()
        col = split.column()
        col.prop(context.scene, "generate_scripts")
        col.prop(context.scene, "donot_merge")
        col.prop(context.scene, "avg_pface")
        col.separator()

        layout.label("RC", icon="PLAY")
        row = layout.row()
        split = row.split(percentage=0.05)
        col = split.column()
        col = split.column()
        col.prop(context.scene, "run_rc")
        col.prop(context.scene, "refresh_rc")
        col.separator()

        layout.label("Image and Material", icon="TEXTURE_DATA")
        row = layout.row()
        split = row.split(percentage=0.05)
        col = split.column()
        col = split.column()
        col.prop(context.scene, "do_materials")
        col.prop(context.scene, "convert_source_image_to_dds")
        col.prop(context.scene, "save_tiff_during_conversion")
        col.separator()

        layout.label("Animation", icon="ANIM_DATA")
        row = layout.row()
        split = row.split(percentage=0.05)
        col = split.column()
        col = split.column()
        col.prop(context.scene, "merge_anm")
        col.prop(context.scene, "include_ik")
        col.separator()

        layout.label("Weight Correction", icon="WPAINT_HLT")
        row = layout.row()
        split = row.split(percentage=0.05)
        col = split.column()
        col = split.column()
        col.prop(context.scene, "correct_weight")
        col.separator()

        layout.label("CryEngine Editor", icon="SEQ_SEQUENCER")
        row = layout.row()
        split = row.split(percentage=0.05)
        col = split.column()
        col = split.column()
        col.prop(context.scene, "make_layer")
        col.separator()

        layout.label("Developer Tools", icon="WORDWRAP_ON")
        row = layout.row()
        split = row.split(percentage=0.05)
        col = split.column()
        col = split.column()
        col.prop(context.scene, "run_in_profiler")


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class Export(bpy.types.Operator):
    """Select to export to game"""
    bl_label = "Export to Game"
    bl_idname = "scene.export_to_game"

    class Config:
        def __init__(self, config):
            setattr(self, "cryblend_version", VERSION)
            setattr(self, "rc_path", Configuration.rc_path)
            setattr(self, "rc_for_textures_conversion_path",
                    Configuration.rc_for_texture_conversion_path)

    def execute(self, context):
        valid = validify_project()
        if (not valid):
            cbPrint("Project name is not valid.  Please correct.", "error")
            bpy.ops.screen.display_error("INVOKE_DEFAULT", message="Project name is not valid.  Please correct.")
        cbPrint(Configuration.rc_path, "debug")
        try:
            config = Export.Config(config=self)
            if getattr(bpy.context.scene, "run_in_profiler"):
                import cProfile
                cProfile.runctx("export.save(config)", {},
                                {"export": export, "config": config})
            else:
                export.save(config)
        except exceptions.CryBlendException as exception:
            cbPrint(exception.what(), "error")
            bpy.ops.error.message("INVOKE_DEFAULT", message=exception.what())
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ErrorHandler(bpy.types.Operator):
    bl_label = "Error:"
    bl_idname = "screen.display_error"

    WIDTH = 400
    HEIGHT = 200

    message = bpy.props.StringProperty()

    def execute(self, context):
        self.report({"ERROR"}, self.message)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, self.WIDTH, self.HEIGHT)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(self.bl_label, icon="ERROR")
        col.split()
        multiline_label(col, self.message)
        col.split()
        col.split(0.2)


def multiline_label(col, text):
    for line in text.splitlines():
        row = col.split()
        row.label(line)


@persistent
def on_scene_update(scene):
    renumber_wheels()
    update_properties()


bpy.app.handlers.scene_update_post.append(on_scene_update)


def update_properties():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'UI':
                    region.tag_redraw()


def renumber_wheels():
    i = 0
    for object_ in bpy.data.objects:
        if ( object_.type == "MESH" and object_.name.startswith("wheel")
            and not (object_.name.endswith("_rim") or object_.name.endswith("_damaged")) ):
            object_.name = "wheel%s" % (i + 1)
            i += 1
    cbPrint(MakeWheels.wheels_intact)
    del MakeWheels.wheels_intact[i:]
    cbPrint(MakeWheels.wheels_intact)

    i = 0
    for object_ in bpy.data.objects:
        if ( object_.type == "MESH" and object_.name.startswith("wheel")
            and object_.name.endswith("_damaged") ):
            object_.name = "wheel%s_damaged" % (i + 1)
            i += 1
    del MakeWheels.wheels_damaged[i:]

    i = 0
    for object_ in bpy.data.objects:
        if ( object_.type == "MESH" and object_.name.startswith("wheel")
            and object_.name.endswith("_rim") ):
            object_.name = "wheel%s_rim" % (i + 1)
            i += 1
    del MakeWheels.wheels_popped[i:]


class MakeWheels(bpy.types.Operator):
    bl_label = "Make Wheels"
    bl_idname = "object.make_wheels"

    wheels_intact = []
    wheels_damaged = []
    wheels_popped = []

    def execute(self, context):
        type = "INTACT"
        if (len(bpy.context.selected_objects) > 1):
            name_multiple_wheels(type)
        elif (bpy.context.scene.objects.active is not None):
            name_single_wheel(type)

        message = "Processing Wheel(s)"
        self.report({"INFO"}, message)
        cbPrint(message)

        # if (ExportListPanel):
            # previous_wheel = ExportListPanel.wheels[-1]
            # next_wheel = previous_wheel[:5].join()
        # if (name not in ExportListPanel.wheels):
            # bpy.context.scene.objects.active.name = name
        # ExportListPanel.wheels.append("wheel1")
        # for area in bpy.context.screen.areas:
            # if area.type == 'VIEW_3D':
                # for region in area.regions:
                    # if region.type == 'UI':
                        # region.tag_redraw()
        return {"FINISHED"}

def find_highest_wheel_number(type):
    highest_wheel_number = 0
    if (type == "INTACT"):
        for object_ in bpy.context.scene.objects:
            if ( object_.type == "MESH" and object_.name.startswith("wheel")
                and not (object_.name.endswith("_rim") or object_.name.endswith("_damaged")) ):
                wheel_number = 0
                try:
                    wheel_number = int(object_.name[5:])
                except ValueError:
                    cbPrint("ValueError")
                if (wheel_number > highest_wheel_number):
                    highest_wheel_number = wheel_number
    elif (type == "DAMAGED"):
        for object_ in bpy.context.scene.objects:
            if ( object_.type == "MESH" and object_.name.startswith("wheel")
                and object_.name.endswith("_damaged") ):
                wheel_number = 0
                try:
                    wheel_number = int(object_.name[5:-8])
                except ValueError:
                    cbPrint("ValueError")
                if (wheel_number > highest_wheel_number):
                    highest_wheel_number = wheel_number
    elif (type == "POPPED"):
        for object_ in bpy.context.scene.objects:
            if ( object_.type == "MESH" and object_.name.startswith("wheel")
                and object_.name.endswith("_rim") ):
                wheel_number = 0
                try:
                    wheel_number = int(object_.name[5:-4])
                except ValueError:
                    cbPrint("ValueError")
                if (wheel_number > highest_wheel_number):
                    highest_wheel_number = wheel_number
    return highest_wheel_number


def name_single_wheel(type):
    highest_wheel_number = find_highest_wheel_number(type)
    wheel = bpy.context.scene.objects.active
    if (wheel.type == "MESH" and not wheel.name.startswith("wheel")):
        if (type == "INTACT"):
            wheel.name = "wheel%s" % (highest_wheel_number + 1)
            wheel.data.name = wheel.name
            MakeWheels.wheels_intact.append(wheel.name)
        elif (type == "DAMAGED"):
            wheel.name = "wheel%s_damaged" % (highest_wheel_number + 1)
            wheel.data.name = wheel.name
            MakeWheels.wheels_damaged.append(wheel.name)
        elif (type == "POPPED"):
            wheel.name = "wheel%s_rim" % (highest_wheel_number + 1)
            wheel.data.name = wheel.name
            MakeWheels.wheels_popped.append(wheel.name)


def name_multiple_wheels(type):
    highest_wheel_number = find_highest_wheel_number(type)
    wheels = bpy.context.selected_objects
    i = 0
    for wheel in wheels:
        if (wheel.type == "MESH" and not wheel.name.startswith("wheel")):
            if (type == "INTACT"):
                wheel.name = "wheel%s" % (highest_wheel_number + i + 1)
                wheel.data.name = wheel.name
                MakeWheels.wheels_intact.append(wheel.name)
            elif (type == "DAMAGED"):
                wheel.name = "wheel%s_damaged" % (highest_wheel_number + i + 1)
                wheel.data.name = wheel.name
                MakeWheels.wheels_damaged.append(wheel.name)
            elif (type == "POPPED"):
                wheel.name = "wheel%s_rim" % (highest_wheel_number + i + 1)
                wheel.data.name = wheel.namea
                MakeWheels.wheels_popped.append(wheel.name)
            i += 1


def hide_all_animations():
    for scene in bpy.data.scenes:
        bpy.data.screens["Default"].scene = scene
        bpy.context.screen.scene = scene
        setattr(bpy.context.scene, "toggle_visible", False)


def add_basis():
    scene = bpy.context.scene
    scene.name = "Basis"
    try:
        getattr(scene, "toggle_visible")
    except AttributeError:
        cbPrint("Blubber")
        bpy.types.Scene.toggle_export = BoolProperty(
                name="",
                description="",
                default=True
                )
        bpy.types.Scene.toggle_visible = BoolProperty(
                name="",
                description="",
                default=True
                )
        setattr(scene, "toggle_visible", True)
        setattr(scene, "toggle_export", True)


class AddAnimation(bpy.types.Operator):
    bl_label = "Add Animation"
    bl_idname = "scene.add_animation"

    def execute(self, context):
        if (len(bpy.data.scenes) == 1):
            add_basis()
        highest_number = 0
        for scene in bpy.data.scenes:
            if scene.name.startswith("Scene_Animation_"):
                number = int(scene.name[16:])
                if (number > highest_number):
                    highest_number = number
        name = "Scene_Animation_%s" % (highest_number + 1)
        bpy.ops.scene.new(type="LINK_OBJECTS")
        bpy.context.scene.name = name
        bpy.types.Scene.animation_name = StringProperty(
                name="",
                description="",
                default=""
                )
        bpy.types.Scene.toggle_export = BoolProperty(
                name="",
                description="",
                default=True
                )
        bpy.types.Scene.toggle_visible = BoolProperty(
                name="",
                description="",
                default=True
                )
        active_scene = bpy.context.scene
        hide_all_animations()
        bpy.data.screens["Default"].scene = active_scene
        bpy.context.screen.scene = active_scene
        setattr(bpy.context.scene, "animation_name", "")
        setattr(bpy.context.scene, "toggle_export", True)
        setattr(bpy.context.scene, "toggle_visible", True)
        return {"FINISHED"}

class ToggleAnimation(bpy.types.Operator):
    bl_label = "Toggle Visible"
    bl_idname = "scene.toggle_animation"

    active_scene = bpy.props.StringProperty()

    def execute(self, context):
        hide_all_animations()
        bpy.data.screens["Default"].scene = bpy.data.scenes[self.active_scene]
        bpy.context.screen.scene = bpy.data.scenes[self.active_scene]
        setattr(bpy.context.scene, "toggle_visible", True)
        return {"FINISHED"}


class DeleteAnimation(bpy.types.Operator):
    bl_label = "Toggle Visible"
    bl_idname = "scene.delete_animation"
    bl_options = {"UNDO"}

    active_scene = bpy.props.StringProperty()

    def execute(self, context):
        old_active_scene = bpy.context.scene
        if (getattr(old_active_scene, "toggle_visible")):
            old_active_scene = None
        bpy.data.screens["Default"].scene = bpy.data.scenes[self.active_scene]
        bpy.context.screen.scene = bpy.data.scenes[self.active_scene]
        bpy.ops.scene.delete()
        if (old_active_scene is not None):
            bpy.data.screens["Default"].scene = old_active_scene
            bpy.context.screen.scene = old_active_scene
        else:
            hide_all_animations()
            setattr(bpy.context.scene, "toggle_visible", True)
        return {"FINISHED"}


class DeleteAllAnimations(bpy.types.Operator):
    bl_label = "Delete All Animations"
    bl_idname = "scene.delete_all_animations"
    bl_options = {"UNDO"}

    def execute(self, context):
        for scene in bpy.data.scenes:
            if (scene.name.startswith("Scene_Animation_")):
                bpy.data.screens["Default"].scene = scene
                bpy.context.screen.scene = scene
                bpy.ops.scene.delete()
        setattr(bpy.data.scenes["Basis"], "toggle_visible", True)
        return {"FINISHED"}


class ToggleAllExports(bpy.types.Operator):
    bl_label = "Toggle Visible"
    bl_idname = "scene.toggle_all_exports"

    def execute(self, context):
        if (AnimationsPanel.toggle_exports):
            AnimationsPanel.toggle_exports = False
            AnimationsPanel.toggle_exports_icon = "CHECKBOX_HLT"
        else:
            AnimationsPanel.toggle_exports = True
            AnimationsPanel.toggle_exports_icon = "CHECKBOX_DEHLT"

        for scene in bpy.data.scenes:
            bpy.data.screens["Default"].scene = scene
            bpy.context.screen.scene = scene
            if (AnimationsPanel.toggle_exports):
                setattr(scene, "toggle_export", True)
            else:
                setattr(scene, "toggle_export", False)
        return {"FINISHED"}


#------------------------------------------------------------------------------
# CryBlend
# Interface:
#------------------------------------------------------------------------------


class View3DPanel():
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"


class ExportPanel(View3DPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Export"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.separator()
        col.operator("scene.export_to_game", icon="GAME")


class ProjectPanel(View3DPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Project"

    bpy.types.Scene.project_type = EnumProperty(
            name="",
            description="Select a file type to export.",
            items=(
                ("CGF", "CGF",
                 "Static geometry project"),
                ("CGA", "CGA",
                 "Hard-body animated geometry project"),
                ("CHR", "CHR",
                 "Character project"),
                ("Entity", "Entity",
                 "Hard-body animated geometry project"),
                ("Vehicle", "Vehicle",
                 "Hard-body animated geometry project"),
                ("Player", "Player",
                 "Hard-body animated geometry project"),
                ("FPS", "FPS",
                 "First person shooter project")
            ),
            default="CGF",
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label("Project Type")
        col.prop(context.scene, "project_type")


class ExportListPanel(View3DPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Export List"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label("Intact")
        col.label("Damaged")
        col.label("Helpers")
        col.label("Seats")
        col.label("Wheels")


class AnimationsPanel(View3DPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Animations" 

    toggle_exports = True
    toggle_exports_icon = "CHECKBOX_DEHLT"

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        row1 = column.row()
        col_a = row1.column()
        col_b = row1.column()
        col_a.operator("scene.add_animation", text="Add")
        col_b.operator("scene.toggle_all_exports", text="", icon=AnimationsPanel.toggle_exports_icon)

        row2 = column.row(align=True)
        col1 = row2.column()  # Toggle Animation
        col2 = row2.column()  # Animation Name
        col3 = row2.column()  # Delete Animation
        row2.separator()
        col4 = row2.column()  # Toggle Export

        for scene in bpy.data.scenes:
            if (scene.name == "Basis"):
                if (getattr(scene, "toggle_visible")):
                    toggle_visible_icon = "RESTRICT_VIEW_OFF"
                else:
                    toggle_visible_icon = "RESTRICT_VIEW_ON"
                toggle_basis = col1.operator("scene.toggle_animation", text="", icon=toggle_visible_icon)
                col2.label("Basis")
                col3.operator("scene.delete_all_animations", text="", icon="ZOOMOUT")
                col4.prop(scene, "toggle_export")

                toggle_basis.active_scene = scene.name
        for i in range(1, len(bpy.data.scenes)):
            scene_name = "Scene_Animation_%s" % i
            scene = bpy.data.scenes[scene_name]
            if (getattr(scene, "toggle_visible")):
                toggle_visible_icon = "RESTRICT_VIEW_OFF"
            else:
                toggle_visible_icon = "RESTRICT_VIEW_ON"
            toggle_animation = col1.operator("scene.toggle_animation", text="", icon=toggle_visible_icon)
            col2.prop(scene, "animation_name")
            delete_animation = col3.operator("scene.delete_animation", text="", icon="ZOOMOUT")
            col4.prop(scene, "toggle_export")

            toggle_animation.active_scene = scene.name
            delete_animation.active_scene = scene.name

            row3 = column.row()
            row3.label("")


class ToolsPanel(View3DPanel, Panel):
    bl_label = "Tools"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="General")
        col.operator("object.add_cry_export_node", text="Add Export Node")
        col.separator()

        col.label(text="Characters")
        col.operator("armature.add_bone_geometry")
        col.operator("armature.remove_bone_geometry")
        col.operator("armature.rename_phys_bones")
        col.separator()

        col.label(text="Touch-Bending")
        col.operator("mesh.add_branch")
        col.operator("mesh.add_branch_joint")
        col.separator()

        col.label(text="Breakables")
        col.operator("object.add_joint", text="Add Joint")


class MeshRepairPanel(View3DPanel, Panel):
    bl_label = "Mesh Repair"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        row1 = col.row(align=True)
        col1 = row1.column()
        col2 = row1.column()

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("Tris")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("N-Gons")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("Nonmanifold")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("Degenerate")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("Multi-Face")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("Weightless")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("No UV's")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("Bad Names")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("Bad Materials")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("Off-Axis Scaling")

        col1.operator("object.add_cry_export_node", text="", icon="RESTRICT_VIEW_OFF")
        col2.label("No Export Nodes")


class MaterialPhysicsPanel(View3DPanel, Panel):
    bl_label = "Material Physics"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="Add Ending...")
        col.separator()
        col.operator("material.add_phys_default", text = "physDefault")
        col.operator("material.add_phys_proxy_no_draw", text = "physProxyNoDraw")
        col.operator("material.add_phys_none", text = "physNone")
        col.operator("material.add_phys_obstruct", text = "physObstruct")
        col.operator("material.add_phys_no_collide", text = "physNoCollide")


class CustomPropertiesPanel(View3DPanel, Panel):
    bl_label = "Custom Properties"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("file.open_udp_webpage", text="Open UDP Page")
        col.separator()

        col.label(text="Rendermesh:")
        col.separator()
        col.operator("object.add_mass_property", text="Mass")
        col.operator("object.add_density_property", text="Density")
        col.operator("object.add_pieces_property", text="Pieces")
        col.separator()

        col.operator("object.add_entity_property", text="Entity")
        col.operator("object.add_dynamic_property", text="Dynamic")
        col.operator("object.add_no_hit_refinement_property", text="No Hit Refinement")
        col.separator()

        col.label(text="Phys Proxy:")
        col.separator()
        col.operator("object.add_box_proxy_property", text="Box")
        col.operator("object.add_cylinder_proxy_property", text="Cylinder")
        col.operator("object.add_capsule_proxy_property", text="Capsule")
        col.operator("object.add_sphere_proxy_property", text="Sphere")
        col.operator("object.add_notaprim_proxy_property", text="Not a Primitive")
        col.separator()

        col.operator("object.add_no_explosion_occlusion_property", text="No Explosion Occlusion")
        col.operator("object.add_other_rendermesh_property", text="Other Rendermesh")
        col.operator("object.add_colltype_player_property", text="Colltype Player")
        col.separator()

        col.label(text="Joint Node:")
        col.separator()
        col.operator("object.add_bend_property", text="Bend")
        col.operator("object.add_twist_property", text="Twist")
        col.operator("object.add_pull_property", text="Pull")
        col.operator("object.add_push_property", text="Push")
        col.operator("object.add_shift_property", text="Shift")
        col.separator()

        col.operator("object.add_gameplay_critical_property", text="Gameplay Critical")
        col.operator("object.add_player_can_break_property", text="Player Can Break")
        col.separator()

        col.label(text="Constraints:")
        col.separator()
        col.operator("object.add_limit_constraint", text="Limit")
        col.operator("object.add_min_angle_constraint", text="MinAngle")
        col.operator("object.add_max_angle_constraint", text="Max Angle")
        col.separator()

        col.operator("object.add_damping_constraint", text="Damping")
        col.operator("object.add_collision_constraint", text="Collision")
        col.separator()

        col.label(text="Deformables:")
        col.separator()
        col.operator("object.add_deformable_properties", text="Deformable Props")
        col.separator()

        col.label(text="Vehicles:")
        col.separator()
        col.operator("object.add_wheel_property", text="Wheel Props")


class ConfigurationsPanel(View3DPanel, Panel):
    bl_label = "Configurations"
    bl_category = "CryBlend"

    def draw(self, context):

        layout = self.layout
        col = layout.column(align=True)

        if (Configuration.rc_path == "" or not "rc.exe" in Configuration.rc_path):
            col.label(text=Configuration.rc_path, icon="CANCEL")
        else:
            col.label(text=Configuration.rc_path, icon="FILE_TICK")
        col.operator("file.find_rc")
        col.separator()

        if (Configuration.rc_path == "" or not "rc.exe" in Configuration.rc_path):
            col.label(text=Configuration.rc_for_texture_conversion_path, icon="CANCEL")
        else:
            col.label(text=Configuration.rc_for_texture_conversion_path, icon="FILE_TICK")
        col.operator("file.find_rc_for_texture_conversion")


class HelpPanel(View3DPanel, Panel):
    bl_label = "Help"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="Resources", icon="QUESTION")
        col.separator()
        col.operator("file.open_crydev_webpage", text = "CryDev Forums")
        col.operator("file.open_github_webpage", text = "CryBlend Wiki")
        col.operator("file.open_cryengine_docs_webpage", text = "CryEngine Docs")

class CryBlendPanel(bpy.types.Operator):
    bl_idname = "file.export"
    bl_label = "Export"
    bl_options = {'PRESET'}

    # -------------------------------------------------------------------------
    # Source Options
    source = EnumProperty(
            name="Source",
            items=(('VERT_OWN', "Own Verts", "Use own vertices"),
                   ('VERT_CHILD', "Child Verts", "Use child object vertices"),
                   ('PARTICLE_OWN', "Own Particles", ("All particle systems of the "
                                                      "source object")),
                   ('PARTICLE_CHILD', "Child Particles", ("All particle systems of the "
                                                          "child objects")),
                   ('PENCIL', "Grease Pencil", "This object's grease pencil"),
                   ),
            options={'ENUM_FLAG'},
            default={'PARTICLE_OWN'},
            )

    source_limit = IntProperty(
            name="Source Limit",
            description="Limit the number of input points, 0 for unlimited",
            min=0, max=5000,
            default=100,
            )

    source_noise = FloatProperty(
            name="Noise",
            description="Randomize point distribution",
            min=0.0, max=1.0,
            default=0.0,
            )

    cell_scale = FloatVectorProperty(
            name="Scale",
            description="Scale Cell Shape",
            size=3,
            min=0.0, max=1.0,
            default=(1.0, 1.0, 1.0),
            )

    # -------------------------------------------------------------------------
    # Recursion

    recursion = IntProperty(
            name="Recursion",
            description="Break shards recursively",
            min=0, max=5000,
            default=0,
            )

    recursion_source_limit = IntProperty(
            name="Source Limit",
            description="Limit the number of input points, 0 for unlimited (applies to recursion only)",
            min=0, max=5000,
            default=8,
            )

    recursion_clamp = IntProperty(
            name="Clamp Recursion",
            description="Finish recursion when this number of objects is reached (prevents recursing for extended periods of time), zero disables",
            min=0, max=10000,
            default=250,
            )

    recursion_chance = FloatProperty(
            name="Random Factor",
            description="Likelihood of recursion",
            min=0.0, max=1.0,
            default=0.25,
            )

    recursion_chance_select = EnumProperty(
            name="Recurse Over",
            items=(('RANDOM', "Random", ""),
                   ('SIZE_MIN', "Small", "Recursively subdivide smaller objects"),
                   ('SIZE_MAX', "Big", "Recursively subdivide bigger objects"),
                   ('CURSOR_MIN', "Cursor Close", "Recursively subdivide objects closer to the cursor"),
                   ('CURSOR_MAX', "Cursor Far", "Recursively subdivide objects farther from the cursor"),
                   ),
            default='SIZE_MIN',
            )

    # -------------------------------------------------------------------------
    # Mesh Data Options

    use_smooth_faces = BoolProperty(
            name="Smooth Faces",
            default=False,
            )

    use_sharp_edges = BoolProperty(
            name="Sharp Edges",
            description="Set sharp edges when disabled",
            default=True,
            )

    use_sharp_edges_apply = BoolProperty(
            name="Apply Split Edge",
            description="Split sharp hard edges",
            default=True,
            )

    use_data_match = BoolProperty(
            name="Match Data",
            description="Match original mesh materials and data layers",
            default=True,
            )

    use_island_split = BoolProperty(
            name="Split Islands",
            description="Split disconnected meshes",
            default=True,
            )

    margin = FloatProperty(
            name="Margin",
            description="Gaps for the fracture (gives more stable physics)",
            min=0.0, max=1.0,
            default=0.001,
            )

    material_index = IntProperty(
            name="Material",
            description="Material index for interior faces",
            default=0,
            )

    use_interior_vgroup = BoolProperty(
            name="Interior VGroup",
            description="Create a vertex group for interior verts",
            default=False,
            )

    # -------------------------------------------------------------------------
    # Physics Options
    
    mass_mode = EnumProperty(
            name="Mass Mode",
            items=(('VOLUME', "Volume", "Objects get part of specified mass based on their volume"),
                   ('UNIFORM', "Uniform", "All objects get the specified mass"),
                   ),
            default='VOLUME',
            )
    
    mass = FloatProperty(
            name="Mass",
            description="Mass to give created objects",
            min=0.001, max=1000.0,
            default=1.0,
            )


    # -------------------------------------------------------------------------
    # Object Options

    use_recenter = BoolProperty(
            name="Recenter",
            description="Recalculate the center points after splitting",
            default=True,
            )

    use_remove_original = BoolProperty(
            name="Remove Original",
            description="Removes the parents used to create the shatter",
            default=True,
            )

    # -------------------------------------------------------------------------
    # Scene Options
    #
    # .. different from object options in that this controls how the objects
    #    are setup in the scene.  

    use_layer_index = IntProperty(
            name="Layer Index",
            description="Layer to add the objects into or 0 for existing",
            default=0,
            min=0, max=20,
            )

    use_layer_next = BoolProperty(
            name="Next Layer",
            description="At the object into the next layer (layer index overrides)",
            default=True,
            )

    group_name = StringProperty(
            name="Group",
            description="Create objects int a group "
                        "(use existing or create new)",
            )

    # -------------------------------------------------------------------------
    # Debug
    use_debug_points = BoolProperty(
            name="Debug Points",
            description="Create mesh data showing the points used for fracture",
            default=False,
            )
            
    use_debug_redraw = BoolProperty(
            name="Show Progress Realtime",
            description="Redraw as fracture is done",
            default=True,
            )

    use_debug_bool = BoolProperty(
            name="Debug Boolean",
            description="Skip applying the boolean modifier",
            default=False,
            )

    def execute(self, context):
        keywords = self.as_keywords()  # ignore=("blah",)

        main(context, **keywords)

        return {'FINISHED'}


    def invoke(self, context, event):
        print(self.recursion_chance_select)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()
        col.label("Point Source")
        rowsub = col.row()
        rowsub.prop(self, "source")
        rowsub = col.row()
        rowsub.prop(self, "source_limit")
        rowsub.prop(self, "source_noise")
        rowsub = col.row()
        rowsub.prop(self, "cell_scale")

        box = layout.box()
        col = box.column()
        col.label("Recursive Shatter")
        rowsub = col.row(align=True)
        rowsub.prop(self, "recursion")
        rowsub.prop(self, "recursion_source_limit")
        rowsub.prop(self, "recursion_clamp")
        rowsub = col.row()
        rowsub.prop(self, "recursion_chance")
        rowsub.prop(self, "recursion_chance_select", expand=True)

        box = layout.box()
        col = box.column()
        col.label("Mesh Data")
        rowsub = col.row()
        rowsub.prop(self, "use_smooth_faces")
        rowsub.prop(self, "use_sharp_edges")
        rowsub.prop(self, "use_sharp_edges_apply")
        rowsub.prop(self, "use_data_match")
        rowsub = col.row()

        # on same row for even layout but infact are not all that related
        rowsub.prop(self, "material_index")
        rowsub.prop(self, "use_interior_vgroup")

        # could be own section, control how we subdiv        
        rowsub.prop(self, "margin")
        rowsub.prop(self, "use_island_split")


        box = layout.box()
        col = box.column()
        col.label("Physics")
        rowsub = col.row(align=True)
        rowsub.prop(self, "mass_mode")
        rowsub.prop(self, "mass")


        box = layout.box()
        col = box.column()
        col.label("Object")
        rowsub = col.row(align=True)
        rowsub.prop(self, "use_recenter")


        box = layout.box()
        col = box.column()
        col.label("Scene")
        rowsub = col.row(align=True)
        rowsub.prop(self, "use_layer_index")
        rowsub.prop(self, "use_layer_next")
        rowsub.prop(self, "group_name")

        box = layout.box()
        col = box.column()
        col.label("Debug")
        rowsub = col.row(align=True)
        rowsub.prop(self, "use_debug_redraw")
        rowsub.prop(self, "use_debug_points")
        rowsub.prop(self, "use_debug_bool")


class CryBlendMainMenu(bpy.types.Menu):
    bl_label = "CryBlend"
    bl_idname = "view3d.cryblend_main_menu"

    def draw(self, context):
        layout = self.layout
        layout.menu(ExportUtilitiesMenu.bl_idname, icon="VIEW3D_VEC")
        layout.separator()
        layout.menu(BoneUtilitiesMenu.bl_idname, icon="BONE_DATA")
        layout.separator()
        layout.menu(TouchBendingMenu.bl_idname, icon="OUTLINER_OB_EMPTY")
        layout.separator()
        layout.menu(MeshUtilitiesMenu.bl_idname, icon="MESH_CUBE")
        layout.separator()
        layout.menu(MaterialPhysicsMenu.bl_idname, icon="MATERIAL")
        layout.separator()
        layout.menu(CustomPropertiesMenu.bl_idname, icon="SCRIPT")
        layout.separator()
        layout.menu(HelpMenu.bl_idname, icon="QUESTION")


class ExportUtilitiesMenu(bpy.types.Menu):
    bl_label = "Export Utilities"
    bl_idname = "view3d.export_utilities"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Nodes")
        layout.operator("object.add_cry_export_node", icon="VIEW3D_VEC")
        layout.operator("object.add_anim_node", icon="POSE_HLT")
        layout.separator()

        layout.label(text="Helpers")
        layout.operator("object.add_joint", icon="PROP_ON")


class BoneUtilitiesMenu(bpy.types.Menu):
    bl_label = "Bone Utilities"
    bl_idname = "view3d.bone_utilities"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Skeleton")
        layout.operator("armature.add_fake_bone", text="Add Fakebone", icon="BONE_DATA")
        layout.operator("scene.remove_fake_bones", text="Remove Fakebones", icon="BONE_DATA")
        layout.separator()

        layout.label(text="Animation")
        layout.operator("armature.add_fakebone_keyframe_list", text="Add FakeBone Keyframe List", icon="KEY_HLT")
        layout.operator("armature.add_fakebone_keyframe", text="Add FakeBone Keyframe", icon="KEY_HLT")
        layout.separator()

        layout.label(text="Physics")
        layout.operator("armature.add_bone_geometry", icon="PHYSICS")
        layout.operator("armature.remove_bone_geometry", icon="PHYSICS")
        layout.operator("armature.rename_phys_bones", icon="PHYSICS")


class TouchBendingMenu(bpy.types.Menu):
    bl_label = "Touch Bending"
    bl_idname = "view3d.touch_bending"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Helpers")
        layout.operator("mesh.add_branch", icon="MOD_SIMPLEDEFORM")
        layout.operator("mesh.add_branch_joint", icon="EMPTY_DATA")


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
        layout.operator("object.find_degenerate_faces", text="Find Degenerate", icon="ZOOM_ALL")
        layout.operator("mesh.find_multiface_lines", text="Find Multi-face", icon="ZOOM_ALL")
        layout.separator()

        layout.label(text="UV Repair")
        layout.operator("scene.find_no_uvs", text="Find No UV's", icon="UV_FACESEL")


class MaterialPhysicsMenu(bpy.types.Menu):
    bl_label = "Material Physics"
    bl_idname = "view3d.material_physics"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Add Ending...")
        layout.operator("material.add_phys_default", text = "physDefault", icon="FILE_TICK")
        layout.operator("material.add_phys_proxy_no_draw", text = "physProxyNoDraw", icon="FILE_TICK")
        layout.operator("material.add_phys_none", text = "physNone", icon="FILE_TICK")
        layout.operator("material.add_phys_obstruct", text = "physObstruct", icon="FILE_TICK")
        layout.operator("material.add_phys_no_collide", text = "physNoCollide", icon="FILE_TICK")


class CustomPropertiesMenu(bpy.types.Menu):
    bl_label = "Custom Properties"
    bl_idname = "view3d.custom_properties"

    def draw(self, context):
        layout = self.layout

        layout.operator("file.open_udp_webpage")
        layout.separator()

        layout.menu(RendermeshPropertiesMenu.bl_idname, icon="OBJECT_DATA")
        layout.menu(PhysProxyPropertiesMenu.bl_idname, icon="PHYSICS")
        layout.menu(JointNodePropertiesMenu.bl_idname, icon="PROP_ON")
        layout.menu(ConstraintPropetiesMenu.bl_idname, icon="CONSTRAINT")
        layout.operator("object.add_deformable_properties", text="Deformable Props", icon="MOD_SIMPLEDEFORM")
        layout.operator("object.add_wheel_property", text="Wheel Props", icon="ROTATECOLLECTION")


class RendermeshPropertiesMenu(bpy.types.Menu):
    bl_label = "Rendemesh"
    bl_idname = "view3d.rendermesh_properties"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.add_mass_property", text="Mass", icon="SCRIPT")
        layout.operator("object.add_density_property", text="Density", icon="SCRIPT")
        layout.operator("object.add_pieces_property", text="Pieces", icon="SCRIPT")
        layout.separator()

        layout.operator("object.add_entity_property", text="Entity", icon="FILE_TICK")
        layout.operator("object.add_dynamic_property", text="Dynamic", icon="FILE_TICK")
        layout.operator("object.add_no_hit_refinement_property", text="No Hit Refinement", icon="FILE_TICK")


class PhysProxyPropertiesMenu(bpy.types.Menu):
    bl_label = "Phys Proxy"
    bl_idname = "view3d.phys_proxy_properties"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.add_box_proxy_property", text="col", icon="META_CUBE")
        layout.operator("object.add_cylinder_proxy_property", text="Cylinder", icon="META_CAPSULE")
        layout.operator("object.add_capsule_proxy_property", text="Capsule", icon="META_ELLIPSOID")
        layout.operator("object.add_sphere_proxy_property", text="Sphere", icon="META_BALL")
        layout.operator("object.add_notaprim_proxy_property", text="Not a Primitive", icon="X")
        layout.separator()

        layout.operator("object.add_no_explosion_occlusion_property", text="No Explosion Occlusion", icon="FILE_TICK")
        layout.operator("object.add_other_rendermesh_property", text="Other Rendermesh", icon="FILE_TICK")
        layout.operator("object.add_colltype_player_property", text="Colltype Player", icon="FILE_TICK")


class JointNodePropertiesMenu(bpy.types.Menu):
    bl_label = "Joint Node"
    bl_idname = "view3d.joint_node_properties"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.add_bend_property", text="Bend", icon="LINCURVE")
        layout.operator("object.add_twist_property", text="Twist", icon="MOD_SCREW")
        layout.operator("object.add_pull_property", text="Pull", icon="FULLSCREEN_ENTER")
        layout.operator("object.add_push_property", text="Push", icon="FULLSCREEN_EXIT")
        layout.operator("object.add_shift_property", text="Shift", icon="NEXT_KEYFRAME")
        layout.separator()

        layout.operator("object.add_gameplay_critical_property", text="Gameplay Critical", icon="FILE_TICK")
        layout.operator("object.add_player_can_break_property", text="Player Can Break", icon="FILE_TICK")


class ConstraintPropetiesMenu(bpy.types.Menu):
    bl_label = "Constraint"
    bl_idname = "view3d.constraint_properties"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.add_limit_constraint", text="Limit", icon="SCRIPT")
        layout.operator("object.add_min_angle_constraint", text="MinAngle", icon="SCRIPT")
        layout.operator("object.add_max_angle_constraint", text="Max Angle", icon="SCRIPT")
        layout.separator()

        layout.operator("object.add_damping_constraint", text="Damping", icon="FILE_TICK")
        layout.operator("object.add_collision_constraint", text="Collision", icon="FILE_TICK")


class HelpMenu(bpy.types.Menu):
    bl_label = "Help"
    bl_idname = "view3d.help"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Resources")
        layout.operator("file.open_crydev_webpage", text = "Ask a Question on the CryDev Forums", icon="SPACE2")
        layout.operator("file.open_github_webpage", text = "Visit the CryBlend Tutorial Wiki", icon="SPACE2")
        layout.operator("file.open_cryengine_docs_webpage", text = "Open the CryEngine Docs Page", icon="SPACE2")


def get_classes_to_register():
    classes = (
        FindRc,
        FindRcForTextureConversion,
        SaveCryBlendConfiguration,

        AddBreakableJoint,
        AddCryExportNode,
        AddBranch,
        AddBranchJoint,
        AddAnimNode,
        AddCharacterAnimation,
        OpenCryDevWebpage,
        OpenGitHubWebpage,
        OpenCryEngineDocsWebpage,

        OpenUDPWebpage,
        AddWheelProperty,
        FixWheelTransforms,

        AddEntityProperty,
        AddMassProperty,
        AddDensityProperty,
        AddPiecesProperty,

        AddGameplayCriticalProperty,
        AddPlayerCanBreakProperty,
        AddBendProperty,
        AddTwistProperty,
        AddPullProperty,
        AddPushProperty,
        AddShiftProperty,

        AddLimitConstraint,
        AddMinAngleConstraint,
        AddMaxAngleConstraint,
        AddDampingConstraint,
        AddCollisionConstraint,
        AddDeformableProperties,

        AddMaterialPhysDefault,
        AddMaterialPhysProxyNoDraw,
        AddMaterialPhysNone,
        AddMaterialPhysObstruct,
        AddMaterialPhysNoCollide,

        AddNoExplosionOcclusionProperty,
        AddOtherRendermeshProperty,
        AddColltypePlayerProperty,
        AddBoxProxyProperty,
        AddCylinderProxyProperty,
        AddCapsuleProxyProperty,
        AddSphereProxyProperty,
        AddNotaprimProxyProperty,
        AddNoHitRefinementProperty,
        AddDynamicProperty,

        FindDegenerateFaces,
        FindMultifaceLines,
        FindWeightless,
        RemoveAllWeight,
        FindNoUVs,

        RenamePhysBones,
        AddBoneGeometry,
        RemoveBoneGeometry,
        AddFakeBone,
        RemoveFakeBones,
        AddFakeBoneKeyframeList,
        AddFakeBoneKeyframe,
        MakeWheels,

        ExportSettings,
        Export,
        ErrorHandler,
        AddAnimation,
        ToggleAnimation,
        DeleteAnimation,
        DeleteAllAnimations,
        ToggleAllExports,

        ExportPanel,
        ProjectPanel,
        ExportListPanel,
        AnimationsPanel,

        CryBlendPanel,
        ToolsPanel,
        MeshRepairPanel,
        MaterialPhysicsPanel,
        CustomPropertiesPanel,
        ConfigurationsPanel,
        HelpPanel,

        CryBlendMainMenu,
        ExportUtilitiesMenu,
        BoneUtilitiesMenu,
        TouchBendingMenu,
        MeshUtilitiesMenu,
        MaterialPhysicsMenu,
        CustomPropertiesMenu,
        RendermeshPropertiesMenu,
        PhysProxyPropertiesMenu,
        JointNodePropertiesMenu,
        ConstraintPropetiesMenu,
        HelpMenu
    )
    return classes


def register():
    for class_to_register in get_classes_to_register():
        bpy.utils.register_class(class_to_register)
    key_config = bpy.context.window_manager.keyconfigs.addon
    if key_config is not None:
        keymap = key_config.keymaps.new(name="3D View", space_type="VIEW_3D")
        keymap_item = keymap.keymap_items.new("wm.call_menu", "Q", "PRESS", ctrl=False, shift=True)
        keymap_item.properties.name = "view3d.cryblend_main_menu"


def unregister():
    # you guys already know this but for my reference,
    # unregister your classes or when you do new scene
    # your script wont import other modules properly.
    for class_to_register in get_classes_to_register():
        bpy.utils.unregister_class(class_to_register)
    key_config = bpy.context.window_manager.keyconfigs.addon
    if key_config is not None:
        keymap = key_config.keymaps["3D View"]
        for keymap_item in keymap.keymap_items:
            if keymap_item.idname == "wm.call_menu":
                if keymap_item.properties.name == "view3d.mymenu":
                    keymap.keymap_items.remove(keymap_item)
                    break


if __name__ == "__main__":
    register()

    # The menu can also be called from scripts
    bpy.ops.wm.call_menu(name=ExportUtilitiesPanel.bl_idname)
