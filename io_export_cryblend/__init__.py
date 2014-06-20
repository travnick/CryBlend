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
    "version": (4, 12, 2, 4, 'dev'),
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
else:
    import bpy
    from io_export_cryblend import add, export, exceptions

from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, \
    FloatProperty, StringProperty
from bpy.types import Menu, Panel
from bpy_extras.io_utils import ExportHelper
from io_export_cryblend.configuration import Configuration
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


class PathSelectTemplate(ExportHelper):
    check_existing = True

    def execute(self, context):
        self.process(self.filepath)

        Configuration.save()
        return {'FINISHED'}


class FindRC(bpy.types.Operator, PathSelectTemplate):
    '''Select the Resource Compiler executable'''

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
to be able to export your textures as dds files'''

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
    '''operator: Saves current CryBlend configuration'''
    bl_label = "Save Config File"
    bl_idname = "config.save"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        Configuration.save()
        return {'FINISHED'}


class AddBreakableJoint(bpy.types.Operator):
    '''Click to add a pre-broken breakable joint to current selection'''
    bl_label = "Add Joint"
    bl_idname = "object.add_joint"

    def execute(self, context):
        return add.add_joint(self, context)


class AddCryExportNode(bpy.types.Operator):
    '''Click to add selection to a CryExportNode'''
    bl_label = "Add CryExportNode"
    bl_idname = "object.add_cry_export_node"
    my_string = StringProperty(name="CryExportNode name")

    def execute(self, context):
        bpy.ops.group.create(name="CryExportNode_%s" % (self.my_string))
        message = "Adding CryExportNode_'%s'" % (self.my_string)
        self.report({'INFO'}, message)
        cbPrint(message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddAnimNode(bpy.types.Operator):
    '''Click to add an AnimNode to selection or with nothing selected
add an AnimNode to the scene'''
    bl_label = "Add AnimNode"
    bl_idname = "object.add_anim_node"
    my_string = StringProperty(name="Animation Name")
    start_frame = FloatProperty(name="Start Frame")
    end_frame = FloatProperty(name="End Frame")

    def execute(self, context):
        object_ = bpy.context.active_object

        # 'add' selects added object
        bpy.ops.object.add(type='EMPTY')
        empty_object = bpy.context.active_object
        empty_object.name = 'animnode'
        empty_object["animname"] = self.my_string
        empty_object["startframe"] = self.start_frame
        empty_object["endframe"] = self.end_frame

        if object_:
            object_.select = True
            bpy.context.scene.objects.active = object_

        bpy.ops.object.parent_set(type='OBJECT')
        message = "Adding AnimNode '%s'" % (self.my_string)
        self.report({'INFO'}, message)
        cbPrint(message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


#------------------------------------------------------------------------------
# CryEngine User
# Defined Properties:
#------------------------------------------------------------------------------


class OpenUDPWebpage(bpy.types.Operator):
    '''A link to UDP'''
    bl_label = "Open Web Page for UDP"
    bl_idname = "file.open_udp_webpage"

    def execute(self, context):
        url = "http://freesdk.crydev.net/display/SDKDOC3/UDP+Settings"
        webbrowser.open(url, new=new)
        self.report({'INFO'}, self.message)
        cbPrint(self.message)
        return {'FINISHED'}


# Rendermesh:
class AddEntityProperty(bpy.types.Operator):
    '''Click to add an entity property'''
    bl_label = "Entity"
    bl_idname = "object.add_entity_property"

    def execute(self, context):
        message = "Adding Entity Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_entity_property(self, context)


class AddMassProperty(bpy.types.Operator):
    '''Click to add a mass value'''
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
    '''Click to add a density value'''
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
    '''Click to add a pieces value'''
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


class AddDynamicProperty(bpy.types.Operator):
    '''Click to add a dynamic property'''
    bl_label = "Dynamic"
    bl_idname = "object.add_dynamic_property"

    def execute(self, context):
        message = "Adding Dynamic Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_dynamic_property(self, context)


class AddNoHitRefinementProperty(bpy.types.Operator):
    '''Click to add a no hit refinement property'''
    bl_label = "No Hit Refinement"
    bl_idname = "object.add_no_hit_refinement_property"

    def execute(self, context):
        message = "Adding No Hit Refinement Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_no_hit_refinement_property(self, context)


# Phys Proxy:
class AddBoxProxyProperty(bpy.types.Operator):
    '''Click to add a box proxy'''
    bl_label = "Box"
    bl_idname = "object.add_box_proxy_property"

    def execute(self, context):
        message = "Adding Box Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_box_proxy_property(self, context)


class AddCylinderProxyProperty(bpy.types.Operator):
    '''Click to add a cylinder proxy'''
    bl_label = "Cylinder"
    bl_idname = "object.add_cylinder_proxy_property"

    def execute(self, context):
        message = "Adding Cylinder Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_cylinder_proxy_property(self, context)


class AddCapsuleProxyProperty(bpy.types.Operator):
    '''Click to add a capsule proxy'''
    bl_label = "Capsule"
    bl_idname = "object.add_capsule_proxy_property"

    def execute(self, context):
        message = "Adding Capsule Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_capsule_proxy_property(self, context)


class AddSphereProxyProperty(bpy.types.Operator):
    '''Click to add a sphere proxy'''
    bl_label = "Sphere"
    bl_idname = "object.add_sphere_proxy_property"

    def execute(self, context):
        message = "Adding Sphere Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_sphere_proxy_property(self, context)


class AddNotaprimProxyProperty(bpy.types.Operator):
    '''Click to add a 'not a primitive' proxy property'''
    bl_label = "Not a Primitive"
    bl_idname = "object.add_notaprim_proxy_property"

    def execute(self, context):
        message = "Adding 'Not a Primitive' Proxy Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_notaprim_proxy_property(self, context)


class AddNoExplosionOcclusionProperty(bpy.types.Operator):
    '''Click to add a no explosion occlusion property'''
    bl_label = "No Explosion Occlusion"
    bl_idname = "object.add_no_explosion_occlusion_property"

    def execute(self, context):
        message = "Adding No Explosion Occlusion Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_no_explosion_occlusion_property(self, context)


class AddOtherRendermeshProperty(bpy.types.Operator):
    '''Click to add an other rendermesh property'''
    bl_label = "Other Rendermesh"
    bl_idname = "object.add_other_rendermesh_property"

    def execute(self, context):
        message = "Adding Other Rendermesh Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_other_rendermesh_property(self, context)


class AddColltypePlayerProperty(bpy.types.Operator):
    '''Click to add a colltype player property'''
    bl_label = "Colltype Player"
    bl_idname = "object.add_colltype_player_property"

    def execute(self, context):
        message = "Adding Colltype Player Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_colltype_player_property(self, context)


# Joint Node:
class AddBendProperty(bpy.types.Operator):
    '''Click to add a bend property'''
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
    '''Click to add a twist property'''
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
    '''Click to add a pull property'''
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
    '''Click to add a push property'''
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
    '''Click to add a shift property'''
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
    '''Click to add a critical property'''
    bl_label = "Gameplay Critical"
    bl_idname = "object.add_gameplay_critical_property"

    def execute(self, context):
        message = "Adding Gameplay Critical Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_gameplay_critical_property(self, context)


class AddPlayerCanBreakProperty(bpy.types.Operator):
    '''Click to add a breakable property'''
    bl_label = "Player Can Break"
    bl_idname = "object.add_player_can_break_property"

    def execute(self, context):
        message = "Adding Player Can Break Property"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_player_can_break_property(self, context)


# Constraints:
class AddLimitConstraint(bpy.types.Operator):
    '''Click to add a limit constraint'''
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
    '''Click to add a min angle constraint'''
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
    '''Click to add a max angle constraint'''
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
    '''Click to add a damping constraint'''
    bl_label = "Damping"
    bl_idname = "object.add_damping_constraint"

    def execute(self, context):
        message = "Adding Damping Constraint"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_damping_constraint(self, context)


class AddCollisionConstraint(bpy.types.Operator):
    '''Click to add a collision constraint'''
    bl_label = "Collision"
    bl_idname = "object.add_collision_constraint"

    def execute(self, context):
        message = "Adding Collision Constraint"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_collision_constraint(self, context)


# Deformables:
class AddDeformableProperties(bpy.types.Operator):
    '''Click to add a deformable mesh property'''
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
    '''Click to add a wheels property'''
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
    '''__physDefault will be added to the material name'''
    bl_label = "__physDefault"
    bl_idname = "material.add_phys_default"

    def execute(self, context):
        message = "Adding __physDefault"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_default(self, context)


class AddMaterialPhysProxyNoDraw(bpy.types.Operator):
    '''__physProxyNoDraw will be added to the material name'''
    bl_label = "Add __physProxyNoDraw to Material Name"
    bl_idname = "material.add_phys_proxy_no_draw"

    def execute(self, context):
        message = "Adding __physProxyNoDraw"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_proxy_no_draw(self, context)


class AddMaterialPhysNone(bpy.types.Operator):
    '''__physNone will be added to the material name'''
    bl_label = "__physNone"
    bl_idname = "material.add_phys_none"

    def execute(self, context):
        message = "Adding __physNone"
        self.report({'INFO'}, message)
        cbPrint(message)
        return add.add_phys_none(self, context)


class AddMaterialPhysObstruct(bpy.types.Operator):
    '''__physObstruct will be added to the material name'''
    bl_label = "__physObstruct"
    bl_idname = "material.add_phys_obstruct"

    def execute(self, context):
        return add.add_phys_obstruct(self, context)


class AddMaterialPhysNoCollide(bpy.types.Operator):
    '''__physNoCollide will be added to the material name'''
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
            to be displayed in Edit mode correctly'''
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
    '''Select the object in object mode with nothing in its mesh selected before running this'''
    bl_label = "Find Weightless Vertices"
    bl_idname = "mesh.find_weightless"

    def execute(self, context):
        obj = bpy.context.active_object
        if obj.type == 'MESH':
            for v in obj.data.vertices:
                v.select = True
                for g in v.groups:
                    v.select = False
                    break
        return {'FINISHED'}


class RemoveAllWeight(bpy.types.Operator):
        '''Select vertices from which to remove weight in edit mode'''
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
to find all items without UVs'''
        bl_label = "Find All Objects with No UVs"
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

#------------------------------------------------------------------------------
# Regarding Fakebones
# And BoneGeometry:
#------------------------------------------------------------------------------

# WARNING!!
#this cleans out all meshes without users!!!

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
    '''Renames phys bones'''
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


class AddBoneGeometry(bpy.types.Operator):
    '''Add BoneGeometry for bones in selected armatures'''
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


# verts and faces
# find bone heads and add at that location
class AddFakeBone(bpy.types.Operator):
    '''Add a simple box mesh'''
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


class RemoveFakeBones(bpy.types.Operator):
        '''Select to remove all fakebones from the scene'''
        bl_label = "Remove All FakeBones"
        bl_idname = "scene.remove_fake_bones"

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


# fakebones
# keyframe insert for fake bones
loclist = []
rotlist = []
# scene = bpy.context.scene


def add_fake_bone_keyframe_list(self, context):
    scene = bpy.context.scene
    object_ = None
    for a in bpy.context.scene.objects:
        if a.type == 'ARMATURE':
            object_ = a
    bpy.ops.screen.animation_play()

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
                        ltmp = [frame, bone.name, lm]
                        rtmp = [frame, bone.name, rm.to_euler()]
                        loclist.append(ltmp)
                        rotlist.append(rtmp)
                    else:
                        for i in bpy.context.scene.objects:
                            if i.name == bone.name:
                                lm, rm, sm = i.matrix_local.decompose()
                                ltmp = [frame, bone.name, lm]
                                rtmp = [frame, bone.name, rm.to_euler()]
                                loclist.append(ltmp)
                                rotlist.append(rtmp)
                else:
                    for i in bpy.context.scene.objects:
                        if i.name == bone.name:
                            lm, rm, sm = i.matrix_local.decompose()
                            ltmp = [frame, bone.name, lm]
                            rtmp = [frame, bone.name, rm.to_euler()]
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


def add_fake_bone_keyframe(self, context):
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
                # TODO: merge those two for loops if possible
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
class AddFakeBoneKeyframeList(bpy.types.Operator):
    '''Adds a key frame list to fakebones'''
    bl_label = "Make Fakebone Keyframes List"
    bl_idname = "armature.add_fakebone_keyframe_list"

    def execute(self, context):
        return add_fake_bone_keyframe_list(self, context)


class AddFakeBoneKeyframe(bpy.types.Operator):
    '''Adds a key frame to fakebone'''
    bl_label = "Add Fakebone Keyframe"
    bl_idname = "armature.add_fakebone_keyframe"

    def execute(self, context):
        return add_fake_bone_keyframe(self, context)


class Export(bpy.types.Operator, ExportHelper):
    '''Select to export to game'''
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
        col = self.col

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
# CryBlend
# Interface:
#------------------------------------------------------------------------------


class View3DPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'


class ExportUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Export Utilities"
    bl_category = "CryBlend"

    def draw(self, context):
        userpref = context.user_preferences
        paths = userpref.filepaths
        layout = self.layout
        col = layout.column(align=True)

        col.operator("object.add_cry_export_node")
        col.operator("object.add_anim_node")
        col.separator()
        col.operator("object.add_joint")
        col.separator()

        col.label(text="Configuration Paths")
        col.separator()
        col.operator("file.find_rc", text="Find RC")
        col.operator("file.find_rc_for_texture_conversion", text="Find Texture RC")
        col.operator("file.select_textures_directory", text="Select Textures Folder")
        col.separator()
        col.label(text="Export")
        col.operator("scene.export_to_game")


class BoneUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Bone Utilities"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator("armature.add_fake_bone", text="Add Fakebone")
        col.operator("scene.remove_fake_bones", text="Remove Fakebones")
        col.separator()

        col.label(text="Animation")
        col.operator("armature.add_fakebone_keyframe_list", text="FakeBone Keyframe List")
        col.operator("armature.add_fakebone_keyframe", text="FakeBone Keyframe")


class BonePhysicsPanel(View3DPanel, Panel):
    bl_label = "Bone Physics"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator("armature.add_bone_geometry")
        col.operator("armature.remove_bone_geometry")
        col.separator()

        col.operator("armature.rename_phys_bones")


class MeshUtilitiesPanel(View3DPanel, Panel):
    bl_label = "Mesh Utilities"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator_context = 'INVOKE_REGION_WIN'

        col.label(text="Weight Repair")
        col.separator()
        col.operator("mesh.find_weightless", text="Find Weightless")
        col.operator("mesh.remove_weight", text="Remove Weight")
        col.separator()

        col.label(text="Mesh Repair")
        col.separator()
        col.operator("object.find_degenerate_faces", text="Find Degenerate")
        col.operator("mesh.find_multiface_lines", text="Find Multi-face")
        col.separator()

        col.label(text="UV Repair")
        col.separator()
        col.operator("scene.find_no_uvs", text="Find No UV's")


class MaterialPhysicsPanel(View3DPanel, Panel):
    bl_label = "Material Physics"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator_context = 'INVOKE_REGION_WIN'

        col.label(text="Add Material Physics")
        col.separator()
        col.operator("material.add_phys_default", text = "__physDefault")
        col.operator("material.add_phys_proxy_no_draw", text = "__physProxyNoDraw")
        col.operator("material.add_phys_none", text = "__physNone")
        col.operator("material.add_phys_obstruct", text = "__physObstruct")
        col.operator("material.add_phys_no_collide", text = "__physNoCollide")


class CustomPropertiesPanel(View3DPanel, Panel):
    bl_label = "Custom Properties"
    bl_category = "CryBlend"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator_context = 'INVOKE_REGION_WIN'
        col.operator("file.open_udp_webpage")

        col.label(text="Rendermesh:")
        col.separator()
        col.operator("object.add_entity_property", text="Entity")
        col.operator("object.add_mass_property", text="Mass")
        col.operator("object.add_density_property", text="Density")
        col.operator("object.add_pieces_property", text="Pieces")
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
        col.operator("object.add_gameplay_critical_property", text="Gameplay Critical")
        col.operator("object.add_player_can_break_property", text="Player Can Break")
        col.separator()

        col.label(text="Constraints:")
        col.separator()
        col.operator("object.add_limit_constraint", text="Limit")
        col.operator("object.add_min_angle_constraint", text="MinAngle")
        col.operator("object.add_max_angle_constraint", text="Max Angle")
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


def get_classes_to_register():
    classes = (

        FindRC,
        FindRCForTextureConversion,
        SelectTexturesDirectory,
        SaveCryBlendConfiguration,

        AddBreakableJoint,
        AddCryExportNode,
        AddAnimNode,

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

        Export,
        ErrorHandler,

        View3DPanel,
        ExportUtilitiesPanel,
        BoneUtilitiesPanel,
        BonePhysicsPanel,
        MeshUtilitiesPanel,
        MaterialPhysicsPanel,
        CustomPropertiesPanel
    )

    return classes


def draw_item(self, context):
    col = self.col
    col.menu(ExportUtilitiesPanel.bl_idname)


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
    bpy.ops.wm.call_menu(name=ExportUtilitiesPanel.bl_idname)
