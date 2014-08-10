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
# Name:        export.py
# Purpose:     Main exporter to CryEngine
#
# Author:      Angelo J. Miner,
#                some code borrowed from fbx exporter Campbell Barton
# Extended by: Duo Oratar
#
# Created:     23/01/2012
# Copyright:   (c) Angelo J. Miner 2012
# License:     GPLv2+
#------------------------------------------------------------------------------


if "bpy" in locals():
    import imp
    imp.reload(utils)
    imp.reload(exceptions)
else:
    import bpy
    from io_export_cryblend import utils, exceptions


from bpy_extras.io_utils import ExportHelper
from datetime import datetime
from io_export_cryblend.dds_converter import DdsConverterRunner
from io_export_cryblend.outPipe import cbPrint
from mathutils import Matrix, Vector
from time import clock
from xml.dom.minidom import Document, Element, parse
import copy
import os
import threading
import time
import xml.dom.minidom
import shutil
import fileinput
import sys
import tempfile
import re
import bmesh


AXES = {
    "X": 0,
    "Y": 1,
    "Z": 2,
}


# replace minidom's function with ours
xml.dom.minidom.Element.writexml = utils.fix_write_xml


class CrytekDaeExporter:
    def __init__(self, config):
        self.__config = config
        self.__doc = Document()

        # If you have all your textures in 'Texture', then path should be like:
        # Textures/some/path
        # so 'Textures' has to be removed from start path
        textures_path = "%s/%s/%s/%s" % (utils.get_cry_root_path(), "Objects", utils.get_project_path(), "Textures")
        normalized_path = os.path.normpath(textures_path)
        self.__textures_parent_directory = os.path.dirname(normalized_path)
        cbPrint("Normalized textures directory: {!r}".format(normalized_path),
                'debug')
        cbPrint("Textures parent directory: {!r}".format(
                                            self.__textures_parent_directory),
                "debug")

    def export(self):
        self.__create_project()

        # Ensure the correct extension for chosen path
        filepath = bpy.path.ensure_ext("%s/%s/%s/%s" % (utils.get_cry_root_path(), "Objects", utils.get_project_path(), utils.get_project_name()), ".dae")
        self.__select_all_export_nodes()

        if getattr(bpy.context.scene, "correct_weight"):
            self.__correct_weights()

        # Duo Oratar
        # This is a small bit risky (I don't know if including more things
        # in the selected objects will mess things up or not...
        # Easiest solution to the problem though
        cbPrint("Searching for boneGeoms...")
        for object_ in bpy.context.selectable_objects:
            if "_boneGeometry" in object_.name:
                bpy.data.objects[object_.name].select = True
                cbPrint("Bone Geometry found: %s" % object_.name)

        root_element = self.__doc.createElement('collada')
        root_element.setAttribute("xmlns",
                               "http://www.collada.org/2005/11/COLLADASchema")
        root_element.setAttribute("version", "1.4.1")
        self.__doc.appendChild(root_element)

        self.__export_asset(root_element)

        # just here for future use
        libcam = self.__doc.createElement("library_cameras")
        root_element.appendChild(libcam)
        liblights = self.__doc.createElement("library_lights")
        root_element.appendChild(liblights)

        self.__export_library_images(root_element)
        self.__export_library_effects(root_element)
        self.__export_library_materials(root_element)
        self.__export_library_geometries(root_element)

        # Duo Oratar
        # Remove the boneGeometry from the selection so we can get on
        # with business as usual
        for object_ in bpy.context.selected_objects:
            if "_boneGeometry" in object_.name:
                bpy.data.objects[object_.name].select = False

        self.__export_library_controllers(root_element)
        self.__export_library_animation_clips_and_animations(root_element)
        self.__export_library_visual_scenes(root_element)
        self.__export_scene(root_element)

        write_to_file(self.__config,
                      self.__doc, filepath,
                      self.__config.rc_path)


    def __get_bones(self, armature):
        return [bone for bone in armature.data.bones]

    # verts and faces
    def __add_fake_bone(self, width, height, depth):
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

    def __add_fake_bones(self, scene):
        old_active_scene = utils.make_active_scene(scene)

        verts_loc, faces = self.__add_fake_bone(1, 1, 1,)
        for om in bpy.data.meshes:
            if om.users == 0:
                bpy.data.meshes.remove(om)

        scene_objects = bpy.context.scene.objects
        for armature in scene_objects:
            if armature.type == 'ARMATURE':

                for pbone in armature.pose.bones:
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
                    bpy.context.scene.objects.active = armature
                    armature.data.bones.active = pbone.bone
                    bpy.ops.object.parent_set(type='BONE')

        utils.make_active_scene(old_active_scene)

    def __remove_fake_bones(self, scene):
        old_active_scene = utils.make_active_scene(scene)

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

        utils.make_active_scene(old_active_scene)
    
    def __create_project(self):
        project_path = "%s/%s/%s" % (utils.get_cry_root_path(), "Objects", utils.get_project_path())
        textures_path = "%s/%s/%s/%s" % (utils.get_cry_root_path(), "Objects", utils.get_project_path(), "Textures")

        if (not os.path.exists(project_path)):
            os.makedirs(project_path)
        if (not os.path.exists(textures_path)):
            os.makedirs(textures_path)

        if (getattr(bpy.context.scene, "generate_scripts")):
            if (getattr(bpy.context.scene, "project_type") == "CHR"):
                self.__create_chr_files()
            elif (getattr(bpy.context.scene, "project_type") == "Entity"):
                self.__create_entity_files()
            elif (getattr(bpy.context.scene, "project_type") == "Vehicle"):
                self.__create_vehicle_files()
            elif (getattr(bpy.context.scene, "project_type") == "Player"):
                self.__create_chr_files()
                self.__create_player_files()
            elif (getattr(bpy.context.scene, "project_type") == "FPS"):
                self.__create_chr_files()
                self.__create_fps_files()

    def __create_chr_files(self):
        animations_path = "%s/%s/%s" % (utils.get_cry_root_path(), "Animations", utils.get_project_path())
        chr_path = bpy.path.ensure_ext("%s/%s/%s" % ("Objects", utils.get_project_path(), utils.get_project_name()), ".chr")
        chrparams_path = bpy.path.ensure_ext("%s/%s/%s/%s" % (utils.get_cry_root_path(), "Objects", utils.get_project_path(), utils.get_project_name()), ".chrparams")
        chrparams_contents = """<Params>
\t<AnimationList>
\t</AnimationList>
</Params>"""
        cdf_path = bpy.path.ensure_ext("%s/%s/%s/%s" % (utils.get_cry_root_path(), "Objects", utils.get_project_path(), utils.get_project_name()), ".cdf")
        cdf_contents = """<CharacterDefinition>
\t<Model File="%s"/>
\t<AttachmentList>
\t</AttachmentList>
\t<ShapeDeformation COL0="0" COL1="0" COL2="0" COL3="0" COL4="0" COL5="0" COL6="0" COL7="0"/>
</CharacterDefinition>""" % chr_path

        if (not os.path.exists(animations_path)):
            os.makedirs(animations_path)

        chrparams_file = open(chrparams_path, "w")
        chrparams_file.write(chrparams_contents)
        chrparams_file.close()

        cdf_file = open(cdf_path, "w")
        cdf_file.write(cdf_contents)
        cdf_file.close()
    
    def __create_entity_files(self):
        entity_path = bpy.path.ensure_ext("%s/%s/%s" % (utils.get_cry_root_path(), "Entities", utils.get_project_name()), ".ent")
        entity_contents = """<Entity
\tName="%s"
\tScript="Scripts/Entities/%s/%s.lua"
/>""" % (utils.get_project_name(), utils.get_project_path(), utils.get_project_name())

        if (not os.path.exists(os.path.dirname(entity_path))):
            os.makedirs(os.path.dirname(entity_path))
        entity_file = open(entity_path, "w")
        entity_file.write(entity_contents)
        entity_file.close()

        self.__create_lua_file()

    def __create_lua_file(self):
        lua_path = bpy.path.ensure_ext("%s/%s/%s/%s" % (utils.get_cry_root_path(), "Scripts/Entities", utils.get_project_path(), utils.get_project_name()), ".lua")
        lua_contents = ""

        if (not os.path.exists(os.path.dirname(lua_path))):
            os.makedirs(os.path.dirname(lua_path))
        lua_file = open(lua_path, "w")
        lua_file.write(lua_contents)
        lua_file.close()

    def __create_vehicle_files(self):
        cbPrint("")

    def __create_player_files(self):
        animation_graph_path_old = bpy.path.ensure_ext("%s/%s" % (utils.fix_name(sys.path[0]), "io_export_cryblend/resources/base_animation_graph"), ".xml")
        animation_graph_path_new = bpy.path.ensure_ext("%s/%s/%s" % (utils.get_cry_root_path(), "Animations/Graphs", utils.get_project_name()), ".xml")
        if (not os.path.exists(os.path.dirname(animation_graph_path_new))):
            os.makedirs(os.path.dirname(animation_graph_path_new))
        shutil.copy(animation_graph_path_old, animation_graph_path_new)

        self.__edit_player_lua_third_person()

    def __create_player_lua(self):
        player_lua_path_old = bpy.path.ensure_ext("%s/%s" % (utils.fix_name(sys.path[0]), "io_export_cryblend/resources/player"), ".lua")
        player_lua_path_new = bpy.path.ensure_ext("%s/%s" % (utils.get_cry_root_path(), "Scripts/Entities/actor/player"), ".lua")
        if (not os.path.exists(os.path.dirname(player_lua_path_new))):
            os.makedirs(os.path.dirname(player_lua_path_new))
        shutil.copy(player_lua_path_old, player_lua_path_new)

    def __edit_player_lua_third_person(self):
        animation_graph_path = bpy.path.ensure_ext("%s" % (utils.get_project_name()), ".xml")
        model_path = bpy.path.ensure_ext("%s/%s/%s" % ("Objects", utils.get_project_path(), utils.get_project_name()), ".cdf")
        player_lua_path = bpy.path.ensure_ext("%s/%s" % (utils.get_cry_root_path(), "Scripts/Entities/actor/player"), ".lua")
        if (not os.path.exists(player_lua_path)):
            self.__create_player_lua()

        fh, target_file_path = tempfile.mkstemp()
        with open(target_file_path, "w") as target_file:
            with open(player_lua_path, "r") as source_file:
                for line in source_file:
                    line_stripped = re.sub("[ \t\n]", "", line)
                    line_components = line_stripped.split("=")
                    if ("AnimationGraph" in line_components):
                        target_file.write(line.replace(line_components[1], '"%s"' % animation_graph_path))
                    elif ("UpperBodyGraph" in line_components):
                        target_file.write(line.replace(line_components[1], '"%s"' % animation_graph_path))
                    elif ("fileModel" in line_components):
                        target_file.write(line.replace(line_components[1], '"%s"' % model_path))
                    elif ("clientFileModel" in line_components):
                        target_file.write(line.replace(line_components[1], '"%s"' % model_path))
                    elif ("objFrozenModel" in line_components):
                        target_file.write(line.replace(line_components[1], '"%s"' % model_path))
                    else:
                        target_file.write(line)
        os.remove(player_lua_path)
        shutil.copy(target_file_path, player_lua_path)

    def __create_fps_files(self):
        weapon_script_path_old = bpy.path.ensure_ext("%s/%s" % (utils.fix_name(sys.path[0]), "io_export_cryblend/resources/base_weapon_script"), ".xml")
        weapon_script_path_new = bpy.path.ensure_ext("%s/%s/%s" % (utils.get_cry_root_path(), "Scripts/Entities/Items/XML/Weapons", utils.get_project_name()), ".xml")
        if (not os.path.exists(weapon_script_path_new)):
            if (not os.path.exists(os.path.dirname(weapon_script_path_new))):
                os.makedirs(os.path.dirname(weapon_script_path_new))
            shutil.copy(weapon_script_path_old, weapon_script_path_new)

        self.__edit_weapon_script(weapon_script_path_new)
        self.__edit_player_lua_first_person()

    def __edit_weapon_script(self, script):
        fp_weapon_path = bpy.path.ensure_ext("%s/%s/%s" % ("Objects", utils.get_project_path(), utils.get_project_name()), ".chr")
        tp_weapon_path = bpy.path.ensure_ext("%s/%s/%s" % ("Objects", utils.get_project_path(), utils.get_project_name()), ".cgf")

        weapon_script = parse(script)

        item = weapon_script.getElementsByTagName("item")[0]
        item.setAttribute("name", utils.get_project_name())
        geometry = weapon_script.getElementsByTagName("geometry")[0]
        firstperson = geometry.getElementsByTagName("firstperson")[0]
        thirdperson = geometry.getElementsByTagName("thirdperson")[0]
        firstperson.setAttribute("name", fp_weapon_path)
        thirdperson.setAttribute("name", tp_weapon_path)

        new_xml = open(script, "w")
        weapon_script.writexml(new_xml)
        new_xml.close()

    def __edit_player_lua_first_person(self):
        fp_arms_model_path = bpy.path.ensure_ext("%s/%s/%s" % ("Objects", utils.get_project_path(), utils.get_project_name()), ".chr")
        player_lua_path = bpy.path.ensure_ext("%s/%s" % (utils.get_cry_root_path(), "Scripts/Entities/actor/player"), ".lua")
        if (not os.path.exists(player_lua_path)):
            self.__create_player_lua()

        fh, target_file_path = tempfile.mkstemp()
        with open(target_file_path, 'w') as target_file:
            with open(player_lua_path, 'r') as source_file:
                for line in source_file:
                    line_stripped = re.sub("[ \t\n]", "", line)
                    line_components = line_stripped.split("=")
                    if ("fpItemHandsModel" in line_components):
                        target_file.write(line.replace(line_components[1], '"%s"' % fp_arms_model_path))
                    else:
                        target_file.write(line)
        os.remove(player_lua_path)
        shutil.copy(target_file_path, player_lua_path)

    def __correct_weights(self):
        scene = bpy.data.scenes[0]
        if (getattr(bpy.context.scene, "project_type") == ""):
            for group in bpy.context.blend_data.groups:
                for object_ in group.objects:
                    if object_.type == "MESH":
                        override = {"weight_paint_object": object_}
                        try:
                            bpy.ops.object.vertex_group_normalize_all(override, lock_active=False)
                        except:
                            bpy.ops.screen.display_error("INVOKE_DEFAULT", message="Please fix weightless vertices first.")
            cbPrint("Weights Corrected.")

    def __select_all_export_nodes(self):
        for group in bpy.context.blend_data.groups:
            for object_ in group.objects:
                object_.select = True
                cbPrint("{!r} selected.".format(object_.name))

    def __get_object_children(self, Parent):
        return [Object for Object in Parent.children
                if Object.type in {"ARMATURE", "EMPTY", "MESH"}]

    def write_bone_list(self, pname, bones, obj, node):
        cbPrint("{!r} bones".format(len(bones)))
        boneExtendedNames = []
        for bone in bones:
            bprnt = bone.parent
            if bprnt:
                cbPrint("Bone {!r} has parent {!r}".format(bone.name,
                                                           bone.parent.name))
            bname = bone.name
            nodename = self.__doc.createElement("node")

            pExtension = ''

            # Name Extension
            if (self.__config.include_ik and "_Phys" == bone.name[-5:]):
                exportNodeName = node1.getAttribute('id')[14:]
                starredBoneName = bone.name.replace("_", "*")
                pExtension += '%' + exportNodeName + '%'
                pExtension += '--PRprops_name=' + starredBoneName + '_'

            # IK
            if ("_Phys" == bone.name[-5:] and self.__config.include_ik):
                poseBone = (bpy.data.objects[obj.name[:-5]]
                    ).pose.bones[bone.name[:-5]]

                # Start IK props
                pExtension += 'xmax={!s}_'.format(poseBone.ik_max_x)
                pExtension += 'xmin={!s}_'.format(poseBone.ik_min_x)
                pExtension += 'xdamping={!s}_'.format(
                                                poseBone.ik_stiffness_x)
                pExtension += 'xspringangle={!s}_'.format(0.0)
                pExtension += 'xspringtension={!s}_'.format(1.0)

                pExtension += 'ymax={!s}_'.format(poseBone.ik_max_y)
                pExtension += 'ymin={!s}_'.format(poseBone.ik_min_y)
                pExtension += 'ydamping={!s}_'.format(
                                                poseBone.ik_stiffness_y)
                pExtension += 'yspringangle={!s}_'.format(0.0)
                pExtension += 'yspringtension={!s}_'.format(1.0)

                pExtension += 'zmax={!s}_'.format(poseBone.ik_max_z)
                pExtension += 'zmin={!s}_'.format(poseBone.ik_min_z)
                pExtension += 'zdamping={!s}_'.format(
                                                poseBone.ik_stiffness_z)
                pExtension += 'zspringangle={!s}_'.format(0.0)
                pExtension += 'zspringtension={!s}_'.format(1.0)
                # End IK props

            nodename.setAttribute("id", "%s" % (bname + pExtension))
            nodename.setAttribute("name", "%s" % (bname + pExtension))
            boneExtendedNames.append(bname + pExtension)
            nodename.setIdAttribute('id')

            bpy.data.objects[obj.name].select = True
            arm = bpy.data.armatures[obj.name]
            bpy.ops.object.mode_set(mode='EDIT')
            editBone = arm.edit_bones[bone.name]
            bmatrix = editBone.head
            # ----------------------------------------------------
            # <translate sid="translation">
            trans = self.__doc.createElement("translate")
            trans.setAttribute("sid", "translation")
            transnum = self.__doc.createTextNode("%.4f %.4f %.4f"
                                          % bmatrix[:])
            trans.appendChild(transnum)
            
            # <rotate sid="rotation_Z">
            rotz = self.__doc.createElement("rotate")
            rotz.setAttribute("sid", "rotation_Z")
            rotzn = self.__doc.createTextNode("0 0 1 %.4f"
                                       % 0)
            rotz.appendChild(rotzn)
            
            # <rotate sid="rotation_Y">
            roty = self.__doc.createElement("rotate")
            roty.setAttribute("sid", "rotation_Y")
            rotyn = self.__doc.createTextNode("0 1 0 %.4f"
                                       % 0)
            roty.appendChild(rotyn)
            
            # <rotate sid="rotation_X">
            rotx = self.__doc.createElement("rotate")
            rotx.setAttribute("sid", "rotation_X")
            rotxn = self.__doc.createTextNode("1 0 0 %.4f"
                                       % 0)
            rotx.appendChild(rotxn)
            
            # <scale sid="scale">
            sc = self.__doc.createElement("scale")
            sc.setAttribute("sid", "scale")
            scn = self.__doc.createTextNode(
                    utils.floats_to_string([1,1,1], " ", "%s"))
            sc.appendChild(scn)
            
            nodename.appendChild(trans)
            nodename.appendChild(rotz)
            nodename.appendChild(roty)
            nodename.appendChild(rotx)
            nodename.appendChild(sc)
            cbPrint("Found fakebone for...")
            cbPrint(bmatrix[:])
            # Find the boneGeometry object
            for i in bpy.context.selectable_objects:
                if i.name == bone.name + "_boneGeometry":
                    ig = self.__doc.createElement("instance_geometry")
                    ig.setAttribute("url", "#%s"
                                    % (bone.name
                                       + "_boneGeometry"))
                    bm = self.__doc.createElement("bind_material")
                    tc = self.__doc.createElement("technique_common")
                    # mat = mesh.materials[:]
                    for mat in i.material_slots:
                        # yes lets go through them 1 at a time
                        im = self.__doc.createElement(
                                        "instance_material")
                        im.setAttribute("symbol", "%s"
                                        % (mat.name))
                        im.setAttribute("target", "#%s"
                                        % (mat.name))
                        bvi = self.__doc.createElement(
                                        "bind_vertex_input")
                        bvi.setAttribute("semantic", "UVMap")
                        bvi.setAttribute("input_semantic",
                                         "TEXCOORD")
                        bvi.setAttribute("input_set", "0")
                        im.appendChild(bvi)
                        tc.appendChild(im)
                    bm.appendChild(tc)
                    ig.appendChild(bm)
                    nodename.appendChild(ig)

            if bprnt:
                for name in boneExtendedNames:
                    if name[:len(bprnt.name)] == bprnt.name:
                        nodeparent = self.__doc.getElementById(name)
                        cbPrint(bprnt.name)
                        nodeparent.appendChild(nodename)
            else:
                node1.appendChild(nodename)

    def write_visual_scene(self, objects, node1):
        for object_ in objects:
            if (len(bpy.data.scenes) > 1):
                if (object_ not in bpy.data.scenes["Basis"]):
                     continue
            fby = 0
            for ai in object_.rna_type.id_data.items():
                if ai:
                    if ai[1] == "fakebone":
                        fby = 1
                        break
            if fby == 1:  # object_.parent_bone:
                pass
            else:
                cname = object_.name

                nodename = self.__doc.createElement("node")
                nodename.setAttribute("id", "%s" % (cname))
                nodename.setIdAttribute('id')
                # <translate sid="translation">
                trans = self.__doc.createElement("translate")
                trans.setAttribute("sid", "translation")
                transnum = self.__doc.createTextNode("%.4f %.4f %.4f"
                                              % object_.location[:])
                trans.appendChild(transnum)
                # <rotate sid="rotation_Z">
                rotz = self.__doc.createElement("rotate")
                rotz.setAttribute("sid", "rotation_Z")
                rotzn = self.__doc.createTextNode("0 0 1 %s"
                                           % (object_.rotation_euler[2]
                                              * utils.toDegrees))
                rotz.appendChild(rotzn)
                # <rotate sid="rotation_Y">
                roty = self.__doc.createElement("rotate")
                roty.setAttribute("sid", "rotation_Y")
                rotyn = self.__doc.createTextNode("0 1 0 %s"
                                           % (object_.rotation_euler[1]
                                              * utils.toDegrees))
                roty.appendChild(rotyn)
                # <rotate sid="rotation_X">
                rotx = self.__doc.createElement("rotate")
                rotx.setAttribute("sid", "rotation_X")
                rotxn = self.__doc.createTextNode("1 0 0 %s"
                                           % (object_.rotation_euler[0]
                                              * utils.toDegrees))
                rotx.appendChild(rotxn)
                # <scale sid="scale">
                sc = self.__doc.createElement("scale")
                sc.setAttribute("sid", "scale")
                scn = self.__doc.createTextNode(
                            utils.floats_to_string(object_.scale, " ", "%s"))
                sc.appendChild(scn)
                nodename.appendChild(trans)
                nodename.appendChild(rotz)
                nodename.appendChild(roty)
                nodename.appendChild(rotx)
                nodename.appendChild(sc)

                # List of all the armature deformation modifiers
                ArmatureList = [Modifier
                                for Modifier in object_.modifiers
                                if Modifier.type == "ARMATURE"]
                if ArmatureList:
                    ic = self.__doc.createElement("instance_controller")
                    # This binds the meshObject to the armature
                    # in control of it
                    ic.setAttribute("url", "#%s_%s"
                                    % (ArmatureList[0].object.name,
                                       object_.name))

                name = str(object_.name)
                if (name[:6] != "_joint"):
                    if (object_.type == "MESH"):
                        ig = self.__doc.createElement("instance_geometry")
                        ig.setAttribute("url", "#%s" % (cname))
                        bm = self.__doc.createElement("bind_material")
                        tc = self.__doc.createElement("technique_common")

                        for mat in object_.material_slots:
                            im = self.__doc.createElement("instance_material")
                            im.setAttribute("symbol", "%s"
                                            % (mat.name))
                            im.setAttribute("target", "#%s"
                                            % (mat.name))
                            bvi = self.__doc.createElement(
                                                "bind_vertex_input")
                            bvi.setAttribute("semantic", "UVMap")
                            bvi.setAttribute("input_semantic",
                                             "TEXCOORD")
                            bvi.setAttribute("input_set", "0")
                            im.appendChild(bvi)
                            tc.appendChild(im)
                        bm.appendChild(tc)
                        if ArmatureList:
                            ic.appendChild(bm)
                            nodename.appendChild(ic)
                        else:
                            ig.appendChild(bm)
                            nodename.appendChild(ig)

                ex = self.__doc.createElement("extra")
                techcry = self.__doc.createElement("technique")
                techcry.setAttribute("profile", "CryEngine")
                prop2 = self.__doc.createElement("properties")
                # tagging properties onto the end of the item
                for ai in object_.rna_type.id_data.items():
                    if ai:
                        cryprops = self.__doc.createTextNode("%s" % ai[1])
                        prop2.appendChild(cryprops)
                techcry.appendChild(prop2)
                if (name[:6] == "_joint"):
                    b = object_.bound_box
                    vmin = Vector([b[0][0], b[0][1], b[0][2]])
                    vmax = Vector([b[6][0], b[6][1], b[6][2]])
                    ht = self.__doc.createElement("helper")
                    ht.setAttribute("type", "dummy")
                    bbmn = self.__doc.createElement("bound_box_min")
                    vmin0 = str(vmin[0])
                    vmin1 = str(vmin[1])
                    vmin2 = str(vmin[2])
                    bbmnval = self.__doc.createTextNode("%s %s %s"
                                                        % (vmin0[:6],
                                                           vmin1[:6],
                                                           vmin2[:6]))
                    bbmn.appendChild(bbmnval)
                    bbmx = self.__doc.createElement("bound_box_max")
                    vmax0 = str(vmax[0])
                    vmax1 = str(vmax[1])
                    vmax2 = str(vmax[2])
                    bbmxval = self.__doc.createTextNode("%s %s %s"
                                                        % (vmax0[:6],
                                                           vmax1[:6],
                                                           vmax2[:6]))
                    bbmx.appendChild(bbmxval)
                    ht.appendChild(bbmn)
                    ht.appendChild(bbmx)
                    techcry.appendChild(ht)
                ex.appendChild(techcry)
                nodename.appendChild(ex)
                if object_.type == 'ARMATURE':
                    cbPrint("Armature appended.")
                    bonelist = self.__get_bones(object_)
                    self.write_bone_list(cname, bonelist, object_, node1)

                if object_.children:
                    if object_.parent:
                        if object_.parent.type != 'ARMATURE':
                            nodeparent = self.__doc.getElementById("%s"
                                                    % object_.parent.name)
                            cbPrint(nodeparent)
                            if nodeparent:
                                cbPrint("Appending object_ to parent.")
                                cbPrint(nodename)
                                chk = self.__doc.getElementById("%s"
                                                         % object_.name)
                                if chk:
                                    cbPrint(
                                    "Object already appended to parent.")
                                else:
                                    nodeparent.appendChild(nodename)
                            ChildList = self.__get_object_children(object_)
                            self.write_visual_scene(ChildList, node1)
                    else:
                        if object_.type != 'ARMATURE':
                            node1.appendChild(nodename)
                            ChildList = self.__get_object_children(object_)
                            self.write_visual_scene(ChildList, node1)

                else:
                    if object_.parent:
                        if object_.parent.type != 'ARMATURE':
                            nodeparent = self.__doc.getElementById("%s"
                                                    % object_.parent.name)
                            cbPrint(nodeparent)
                            if nodeparent:
                                cbPrint("Appending object_ to parent.")
                                cbPrint(nodename)
                                chk = self.__doc.getElementById("%s"
                                                         % object_.name)
                                if chk:
                                    cbPrint(
                                    "Object already appended to parent.")
                                else:
                                    nodeparent.appendChild(nodename)

                            cbPrint("Armparent.")
                        else:
                            node1.appendChild(nodename)
                    else:
                        if object_.name == "animnode":
                            cbPrint("Animnode.")
                        else:
                            node1.appendChild(nodename)
        return node1

    def __get_animation_location(self, object_, axis):
        attribute_type = "location"
        multiplier = 1
        target = "{!s}{!s}{!s}".format(object_.name, "/translation.", axis)

        animation_element = self.__get_animation_attribute(object_,
                                                           axis,
                                                           attribute_type,
                                                           multiplier,
                                                           target)
        return animation_element

    def __get_animation_rotation(self, object_, axis):
        attribute_type = "rotation_euler"
        multiplier = utils.toDegrees
        target = "{!s}{!s}{!s}{!s}".format(object_.name,
                                           "/rotation_",
                                           axis,
                                           ".ANGLE")

        animation_element = self.__get_animation_attribute(object_,
                                                           axis,
                                                           attribute_type,
                                                           multiplier,
                                                           target)
        return animation_element

    def __get_animation_attribute(self,
                                  object_,
                                  axis,
                                  attribute_type,
                                  multiplier,
                                  target):
        id_prefix = "{!s}_{!s}_{!s}".format(object_.name, attribute_type, axis)
        source_prefix = "#{!s}".format(id_prefix)

        for curve in object_.animation_data.action.fcurves:
            if (curve.data_path == attribute_type and
                curve.array_index == AXES[axis]):
                animation_element = self.__doc.createElement("animation")
                animation_element.setAttribute("id", id_prefix)
                intangx = ""
                outtangx = ""
                inpx = ""
                outpx = ""
                intx = ""
                keyframe_points = curve.keyframe_points
                ii = len(keyframe_points)
                for keyframe_point in keyframe_points:
                    khlx = keyframe_point.handle_left[0]
                    khly = keyframe_point.handle_left[1]
                    khrx = keyframe_point.handle_right[0]
                    khry = keyframe_point.handle_right[1]
                    frame, value = keyframe_point.co
                    time = utils.convert_time(frame)
                    intx += "%s " % (keyframe_point.interpolation)
                    inpx += "%.6f " % (time)
                    outpx += "%.6f " % (value * multiplier)
                    intangfirst = utils.convert_time(khlx)
                    outangfirst = utils.convert_time(khrx)
                    intangx += "%.6f %.6f " % (intangfirst, khly)
                    outtangx += "%.6f %.6f " % (outangfirst, khry)

                # input
                sinpx = self.__doc.createElement("source")
                sinpx.setAttribute("id", id_prefix + "-input")
                inpxfa = self.__doc.createElement("float_array")
                inpxfa.setAttribute("id", id_prefix + "-input-array")
                inpxfa.setAttribute("count", "%s" % (ii))
                sinpxdat = self.__doc.createTextNode("%s" % (inpx))
                inpxfa.appendChild(sinpxdat)
                tcinpx = self.__doc.createElement("technique_common")
                accinpx = self.__doc.createElement("accessor")
                accinpx.setAttribute("source", source_prefix + "-input-array")
                accinpx.setAttribute("count", "%s" % (ii))
                accinpx.setAttribute("stride", "1")
                parinpx = self.__doc.createElement("param")
                parinpx.setAttribute("name", "TIME")
                parinpx.setAttribute("type", "float")
                accinpx.appendChild(parinpx)
                tcinpx.appendChild(accinpx)
                sinpx.appendChild(inpxfa)
                sinpx.appendChild(tcinpx)
                # output
                soutpx = self.__doc.createElement("source")
                soutpx.setAttribute("id", id_prefix + "-output")
                outpxfa = self.__doc.createElement("float_array")
                outpxfa.setAttribute("id", id_prefix + "-output-array")
                outpxfa.setAttribute("count", "%s" % (ii))
                soutpxdat = self.__doc.createTextNode("%s" % (outpx))
                outpxfa.appendChild(soutpxdat)
                tcoutpx = self.__doc.createElement("technique_common")
                accoutpx = self.__doc.createElement("accessor")
                accoutpx.setAttribute("source", source_prefix + "-output-array")
                accoutpx.setAttribute("count", "%s" % (ii))
                accoutpx.setAttribute("stride", "1")
                paroutpx = self.__doc.createElement("param")
                paroutpx.setAttribute("name", "VALUE")
                paroutpx.setAttribute("type", "float")
                accoutpx.appendChild(paroutpx)
                tcoutpx.appendChild(accoutpx)
                soutpx.appendChild(outpxfa)
                soutpx.appendChild(tcoutpx)
                # interpolation
                sintpx = self.__doc.createElement("source")
                sintpx.setAttribute("id", id_prefix + "-interpolation")
                intpxfa = self.__doc.createElement("Name_array")
                intpxfa.setAttribute("id", id_prefix + "-interpolation-array")
                intpxfa.setAttribute("count", "%s" % (ii))
                sintpxdat = self.__doc.createTextNode("%s" % (intx))
                intpxfa.appendChild(sintpxdat)
                tcintpx = self.__doc.createElement("technique_common")
                accintpx = self.__doc.createElement("accessor")
                accintpx.setAttribute("source", source_prefix + "-interpolation-array")
                accintpx.setAttribute("count", "%s" % (ii))
                accintpx.setAttribute("stride", "1")
                parintpx = self.__doc.createElement("param")
                parintpx.setAttribute("name", "INTERPOLATION")
                parintpx.setAttribute("type", "name")
                accintpx.appendChild(parintpx)
                tcintpx.appendChild(accintpx)
                sintpx.appendChild(intpxfa)
                sintpx.appendChild(tcintpx)
                # intangent
                sintangpx = self.__doc.createElement("source")
                sintangpx.setAttribute("id", id_prefix + "-intangent")
                intangpxfa = self.__doc.createElement("float_array")
                intangpxfa.setAttribute("id", id_prefix + "-intangent-array")
                intangpxfa.setAttribute("count", "%s" % ((ii) * 2))
                sintangpxdat = self.__doc.createTextNode("%s" % (intangx))
                intangpxfa.appendChild(sintangpxdat)
                tcintangpx = self.__doc.createElement("technique_common")
                accintangpx = self.__doc.createElement("accessor")
                accintangpx.setAttribute("source", source_prefix + "-intangent-array")
                accintangpx.setAttribute("count", "%s" % (ii))
                accintangpx.setAttribute("stride", "2")
                parintangpx = self.__doc.createElement("param")
                parintangpx.setAttribute("name", "X")
                parintangpx.setAttribute("type", "float")
                parintangpxy = self.__doc.createElement("param")
                parintangpxy.setAttribute("name", "Y")
                parintangpxy.setAttribute("type", "float")
                accintangpx.appendChild(parintangpx)
                accintangpx.appendChild(parintangpxy)
                tcintangpx.appendChild(accintangpx)
                sintangpx.appendChild(intangpxfa)
                sintangpx.appendChild(tcintangpx)
                # outtangent
                soutangpx = self.__doc.createElement("source")
                soutangpx.setAttribute("id", id_prefix + "-outtangent")
                outangpxfa = self.__doc.createElement("float_array")
                outangpxfa.setAttribute("id", id_prefix + "-outtangent-array")
                outangpxfa.setAttribute("count", "%s" % ((ii) * 2))
                soutangpxdat = self.__doc.createTextNode("%s" % (outtangx))
                outangpxfa.appendChild(soutangpxdat)
                tcoutangpx = self.__doc.createElement("technique_common")
                accoutangpx = self.__doc.createElement("accessor")
                accoutangpx.setAttribute("source", source_prefix + "-outtangent-array")
                accoutangpx.setAttribute("count", "%s" % (ii))
                accoutangpx.setAttribute("stride", "2")
                paroutangpx = self.__doc.createElement("param")
                paroutangpx.setAttribute("name", "X")
                paroutangpx.setAttribute("type", "float")
                paroutangpxy = self.__doc.createElement("param")
                paroutangpxy.setAttribute("name", "Y")
                paroutangpxy.setAttribute("type", "float")
                accoutangpx.appendChild(paroutangpx)
                accoutangpx.appendChild(paroutangpxy)
                tcoutangpx.appendChild(accoutangpx)
                soutangpx.appendChild(outangpxfa)
                soutangpx.appendChild(tcoutangpx)
                # sampler
                samx = self.__doc.createElement("sampler")
                samx.setAttribute("id", id_prefix + "-sampler")
                semip = self.__doc.createElement("input")
                semip.setAttribute("semantic", "INPUT")
                semip.setAttribute("source", source_prefix + "-input")
                semop = self.__doc.createElement("input")
                semop.setAttribute("semantic", "OUTPUT")
                semop.setAttribute("source", source_prefix + "-output")
                seminter = self.__doc.createElement("input")
                seminter.setAttribute("semantic", "INTERPOLATION")
                seminter.setAttribute("source", source_prefix + "-interpolation")
                semintang = self.__doc.createElement("input")
                semintang.setAttribute("semantic", "IN_TANGENT")
                semintang.setAttribute("source", source_prefix + "-intangent")
                semoutang = self.__doc.createElement("input")
                semoutang.setAttribute("semantic", "OUT_TANGENT")
                semoutang.setAttribute("source", source_prefix + "-outtangent")
                samx.appendChild(semip)
                samx.appendChild(semop)
                samx.appendChild(seminter)
                chanx = self.__doc.createElement("channel")
                chanx.setAttribute("source", source_prefix + "-sampler")
                chanx.setAttribute("target", target)
                animation_element.appendChild(sinpx)
                animation_element.appendChild(soutpx)
                animation_element.appendChild(sintpx)
                animation_element.appendChild(sintangpx)
                animation_element.appendChild(soutangpx)
                animation_element.appendChild(samx)
                animation_element.appendChild(chanx)

                cbPrint("keyframe_points count: {!s}".format(ii))
                cbPrint(inpx)
                cbPrint(outpx)
                cbPrint(intx)
                cbPrint(intangx)
                cbPrint(outtangx)
                cbPrint("done {!s} {!s}".format(attribute_type, axis))

        return animation_element

    def __get_bone_names_for_idref(self, bones):
        return " ".join(bone.name for bone in bones)

    def __export_float_array(self, armature_name, armature_bones, float_array):
        for bone in armature_bones:
            matrix_local = 0
            arm = bpy.data.armatures[armature_name]
            bpy.ops.object.mode_set(mode='EDIT')
            editBone = arm.edit_bones[bone.name]
            bmatrix = editBone.head
            # TODO: this loop is probably useless

            matrix_local = [
                [1.0, 0.0, 0.0, bmatrix[0]],
                [0.0, 1.0, 0.0, bmatrix[1]],
                [0.0, 0.0, 1.0, bmatrix[2]],
                [0.0, 0.0, 0.0, 1.0]
                ]

            if matrix_local == 0:
                return

            cbPrint("matrix_local %s" % matrix_local, 'debug')

            self.__negate_z_axis_of_matrix(matrix_local)

            for row in matrix_local:
                row_string = utils.floats_to_string(row)
                float_array.appendChild(self.__doc.createTextNode(row_string))

    def __negate_z_axis_of_matrix(self, matrix_local):
        for i in range(0, 3):
            matrix_local[i][3] = -matrix_local[i][3]

    def __export_asset(self, parent_element):
        # Attributes are x=y values inside a tag
        asset = self.__doc.createElement("asset")
        parent_element.appendChild(asset)
        contrib = self.__doc.createElement("contributor")
        asset.appendChild(contrib)
        auth = self.__doc.createElement("author")
        contrib.appendChild(auth)
        authname = self.__doc.createTextNode("Blender User")
        auth.appendChild(authname)
        authtool = self.__doc.createElement("authoring_tool")
        authtname = self.__doc.createTextNode(
            "CryBlend v%s" % self.__config.cryblend_version)
        authtool.appendChild(authtname)
        contrib.appendChild(authtool)
        created = self.__doc.createElement("created")
        created_value = self.__doc.createTextNode(datetime.now().isoformat(" "))
        created.appendChild(created_value)
        asset.appendChild(created)
        modified = self.__doc.createElement("modified")
        asset.appendChild(modified)
        unit = self.__doc.createElement("unit")
        unit.setAttribute("name", "meter")
        unit.setAttribute("meter", "1")
        asset.appendChild(unit)
        uax = self.__doc.createElement("up_axis")
        zup = self.__doc.createTextNode("Z_UP")
        uax.appendChild(zup)
        asset.appendChild(uax)

    def __export_library_images(self, parent_element):
        library_images = self.__doc.createElement("library_images")
        parent_element.appendChild(library_images)

        images_to_convert = []

        for image in self.__get_texture_images_for_selected_objects():
            image_element = self.__export_library_image(images_to_convert,
                                                        image)
            library_images.appendChild(image_element)

        if getattr(bpy.context.scene, "convert_source_image_to_dds"):
            self.__convert_images_to_dds(images_to_convert)

    def __export_library_image(self, images_to_convert, image):
        if getattr(bpy.context.scene, "convert_source_image_to_dds"):
            image_path = utils.get_path_with_new_extension(image.filepath,
                "dds")
            images_to_convert.append(image)

        else:
            image_path = image.filepath

        image_path = utils.get_relative_path(image_path,
                                             self.__textures_parent_directory)

        image_element = self.__doc.createElement("image")
        image_element.setAttribute("id", "%s" % image.name)
        image_element.setAttribute("name", "%s" % image.name)
        init_from = self.__doc.createElement("init_from")
        path_node = self.__doc.createTextNode("%s" % image_path)
        init_from.appendChild(path_node)
        image_element.appendChild(init_from)

        return image_element

    def __get_texture_images_for_selected_objects(self):
        images = []
        textures = self.__get_textures_for_selected_objects()

        for texture in textures:
            image = texture.image
            if self.is_valid_image(image):
                if (image.filepath.endswith(".tif")):
                    image.filepath = bpy.path.ensure_ext(image.filepath[:-4], ".tiff")
                try:
                    images.append(image)

                except AttributeError:
                    # don't care about non-image textures
                    pass

        # return only unique images
        return list(set(images))

    def __get_textures_for_selected_objects(self):
        materials = self.__get_materials_for_selected_objects()
        return self.__get_textures_for_materials(materials)

    def __get_materials_for_selected_objects(self):
        materials = []
        for object_ in bpy.context.selected_objects:
            for material_slot in object_.material_slots:
                material = material_slot.material
                materialName = material.name
                try:
                    materialComponents = materialName.split("__")
                    id = materialComponents[1]
                    if (len(id) == 1 and id.isdigit()):
                        id = id.rjust(2, '0')  # pad single digit ID's
                    material.name = "%s__%s__%s__%s" % (materialComponents[0], id, materialComponents[2], materialComponents[3])
                    materials.append(material)
                except:
                    materials.append(material)

        return materials

    def __get_textures_for_materials(self, materials):
        texture_slots = self.__get_texture_slots_for_materials(materials)
        return self.__get_textures_for_texture_slots(texture_slots)

    def __get_texture_slots_for_materials(self, materials):
        texture_slots = []

        for material in materials:
            texture_slots.extend(
                            self.__get_texture_slots_for_material(material))

        return texture_slots

    def __get_texture_slots_for_material(self, material):
        texture_slots = []
        for texture_slot in material.texture_slots:
            # texture_slot is able to be None
            if texture_slot and texture_slot.texture.type == 'IMAGE':
                texture_slots.append(texture_slot)

        self.__is_texture_slot_valid(texture_slots)

        return texture_slots

    def __is_texture_slot_valid(self, texture_slots):
        texture_types = self.__count_texture_types(texture_slots)

        self.__raise_exception_if_textures_have_same_type(texture_types)

    def __count_texture_types(self, texture_slots):
        texture_types = {
            'DIFFUSE': 0,
            'SPECULAR': 0,
            'NORMAL MAP': 0
        }

        for texture_slot in texture_slots:
            if texture_slot.use_map_color_diffuse:
                texture_types['DIFFUSE'] += 1
            if texture_slot.use_map_color_spec:
                texture_types['SPECULAR'] += 1
            if texture_slot.use_map_normal:
                texture_types['NORMAL MAP'] += 1

        return texture_types

    def __raise_exception_if_textures_have_same_type(self, texture_types):
        ERROR_TEMPLATE = "There is more than one texture of type {!r}."
        error_messages = []

        for type_name, type_count in  texture_types.items():
            if type_count > 1:
                error_messages.append(ERROR_TEMPLATE.format(type_name.lower()))

        if error_messages:
            raise exceptions.CryBlendException("\n".join(error_messages) + "\n"
                                        + "Please correct that and try again.")

    def __get_textures_for_texture_slots(self, texture_slots):
        return [texture_slot.texture for texture_slot in texture_slots]

    def is_valid_image(self, image):
        return image.has_data and image.filepath

    def __convert_images_to_dds(self, images_to_convert):
        converter = DdsConverterRunner(
                                self.__config.rc_for_textures_conversion_path)
        converter.start_conversion(images_to_convert,
                                   getattr(bpy.context.scene, "refresh_rc"),
                                   getattr(bpy.context.scene, "save_tiff_during_conversion"))

    def __export_library_effects(self, parent_element):
        current_element = self.__doc.createElement("library_effects")
        parent_element.appendChild(current_element)

        for material in self.__get_materials_for_selected_objects():
            self.__export_library_effects_material(material, current_element)

    def __export_library_effects_material(self, material, current_element):
        diffuse_count = 0
        specular_count = 0
        normal_map_count = 0
        diffuse_image = ""
        specular_image = ""
        normal_map_image = ""

        texture_slots = self.__get_texture_slots_for_material(material)
        for texture_slot in texture_slots:
            image = texture_slot.texture.image

            if not image:
                raise exceptions.CryBlendException(
                            "One of texture slots has no image assigned.")

            if texture_slot.use_map_color_diffuse:
                diffuse_count += 1
                diffuse_image = image.name
                dnpsurf = self.__doc.createElement("newparam")
                dnpsurf.setAttribute("sid", "%s-surface" % image.name)
                surface_node = self.__doc.createElement("surface")
                surface_node.setAttribute("type", "2D")
                init_from_node = self.__doc.createElement("init_from")
                temp_node = self.__doc.createTextNode(image.name)
                init_from_node.appendChild(temp_node)
                surface_node.appendChild(init_from_node)
                dnpsurf.appendChild(surface_node)
                dnpsamp = self.__doc.createElement("newparam")
                dnpsamp.setAttribute("sid", "%s-sampler" % image.name)
                sampler_node = self.__doc.createElement("sampler2D")
                source_node = self.__doc.createElement("source")
                temp_node = self.__doc.createTextNode(
                                                "%s-surface" % (image.name))
                source_node.appendChild(temp_node)
                sampler_node.appendChild(source_node)
                dnpsamp.appendChild(sampler_node)
            if texture_slot.use_map_color_spec:
                specular_count += 1
                specular_image = image.name
                snpsurf = self.__doc.createElement("newparam")
                snpsurf.setAttribute("sid", "%s-surface" % image.name)
                surface_node = self.__doc.createElement("surface")
                surface_node.setAttribute("type", "2D")
                init_from_node = self.__doc.createElement("init_from")
                temp_node = self.__doc.createTextNode(image.name)
                init_from_node.appendChild(temp_node)
                surface_node.appendChild(init_from_node)
                snpsurf.appendChild(surface_node)
                snpsamp = self.__doc.createElement("newparam")
                snpsamp.setAttribute("sid", "%s-sampler" % image.name)
                sampler_node = self.__doc.createElement("sampler2D")
                source_node = self.__doc.createElement("source")
                temp_node = self.__doc.createTextNode(
                                                "%s-surface" % (image.name))
                source_node.appendChild(temp_node)
                sampler_node.appendChild(source_node)
                snpsamp.appendChild(sampler_node)
            if texture_slot.use_map_normal:
                normal_map_count += 1
                normal_map_image = image.name
                nnpsurf = self.__doc.createElement("newparam")
                nnpsurf.setAttribute("sid", "%s-surface" % image.name)
                surface_node = self.__doc.createElement("surface")
                surface_node.setAttribute("type", "2D")
                init_from_node = self.__doc.createElement("init_from")
                temp_node = self.__doc.createTextNode(image.name)
                init_from_node.appendChild(temp_node)
                surface_node.appendChild(init_from_node)
                nnpsurf.appendChild(surface_node)
                nnpsamp = self.__doc.createElement("newparam")
                nnpsamp.setAttribute("sid", "%s-sampler" % image.name)
                sampler_node = self.__doc.createElement("sampler2D")
                source_node = self.__doc.createElement("source")
                temp_node = self.__doc.createTextNode(
                                                "%s-surface" % (image.name))
                source_node.appendChild(temp_node)
                sampler_node.appendChild(source_node)
                nnpsamp.appendChild(sampler_node)

        effect_node = self.__doc.createElement("effect")
        effect_node.setAttribute("id", "%s_fx" % (material.name))
        profile_node = self.__doc.createElement("profile_COMMON")
        if diffuse_count:
            profile_node.appendChild(dnpsurf)
            profile_node.appendChild(dnpsamp)
        if specular_count:
            profile_node.appendChild(snpsurf)
            profile_node.appendChild(snpsamp)
        if normal_map_count:
            profile_node.appendChild(nnpsurf)
            profile_node.appendChild(nnpsamp)
        tech_com = self.__doc.createElement("technique")
        tech_com.setAttribute("sid", "common")
        phong = self.__doc.createElement("phong")
        emis = self.__doc.createElement("emission")
        color = self.__doc.createElement("color")
        color.setAttribute("sid", "emission")
        cot = utils.color_to_string(material.emit,
                                    material.emit,
                                    material.emit,
                                    1.0)
        emit = self.__doc.createTextNode(cot)
        color.appendChild(emit)
        emis.appendChild(color)
        amb = self.__doc.createElement("ambient")
        color = self.__doc.createElement("color")
        color.setAttribute("sid", "ambient")
        cot = utils.color_to_string(material.ambient,
                                    material.ambient,
                                    material.ambient,
                                    1.0)
        ambcol = self.__doc.createTextNode(cot)
        color.appendChild(ambcol)
        amb.appendChild(color)
        dif = self.__doc.createElement("diffuse")
        if diffuse_count:
            dtexr = self.__doc.createElement("texture")
            dtexr.setAttribute("texture", "%s-sampler" % diffuse_image)
            dif.appendChild(dtexr)
        else:
            color = self.__doc.createElement("color")
            color.setAttribute("sid", "diffuse")
            cot = utils.color_to_string(material.diffuse_color.r,
                                        material.diffuse_color.g,
                                        material.diffuse_color.b,
                                        1.0)
            difcol = self.__doc.createTextNode(cot)
            color.appendChild(difcol)
            dif.appendChild(color)
        spec = self.__doc.createElement("specular")
        if specular_count:
            stexr = self.__doc.createElement("texture")
            stexr.setAttribute("texture", "%s-sampler" % specular_image)
            spec.appendChild(stexr)
        else:
            color = self.__doc.createElement("color")
            color.setAttribute("sid", "specular")
            cot = utils.color_to_string(material.specular_color.r,
                                        material.specular_color.g,
                                        material.specular_color.b,
                                        1.0)
            speccol = self.__doc.createTextNode(cot)
            color.appendChild(speccol)
            spec.appendChild(color)
        shin = self.__doc.createElement("shininess")
        flo = self.__doc.createElement("float")
        flo.setAttribute("sid", "shininess")
        shinval = self.__doc.createTextNode("%s" % material.specular_hardness)
        flo.appendChild(shinval)
        shin.appendChild(flo)
        ioref = self.__doc.createElement("index_of_refraction")
        flo = self.__doc.createElement("float")
        flo.setAttribute("sid", "index_of_refraction")
        iorval = self.__doc.createTextNode("%s" % material.alpha)
        flo.appendChild(iorval)
        ioref.appendChild(flo)
        phong.appendChild(emis)
        phong.appendChild(amb)
        phong.appendChild(dif)
        phong.appendChild(spec)
        phong.appendChild(shin)
        phong.appendChild(ioref)
        if normal_map_count:
            bump = self.__doc.createElement("normal")
            ntexr = self.__doc.createElement("texture")
            ntexr.setAttribute("texture", "%s-sampler" % normal_map_image)
            bump.appendChild(ntexr)
            phong.appendChild(bump)
        tech_com.appendChild(phong)
        profile_node.appendChild(tech_com)
        extra = self.__doc.createElement("extra")
        techn = self.__doc.createElement("technique")
        techn.setAttribute("profile", "GOOGLEEARTH")
        ds = self.__doc.createElement("double_sided")
        dsval = self.__doc.createTextNode("1")
        ds.appendChild(dsval)
        techn.appendChild(ds)
        extra.appendChild(techn)
        profile_node.appendChild(extra)
        effect_node.appendChild(profile_node)
        extra = self.__doc.createElement("extra")
        techn = self.__doc.createElement("technique")
        techn.setAttribute("profile", "MAX3D")
        ds = self.__doc.createElement("double_sided")
        dsval = self.__doc.createTextNode("1")
        ds.appendChild(dsval)
        techn.appendChild(ds)
        extra.appendChild(techn)
        effect_node.appendChild(extra)
        current_element.appendChild(effect_node)

    def __export_library_materials(self, parent_element):
        library_materials = self.__doc.createElement("library_materials")
        materials = self.__get_materials_for_selected_objects()

        for material in materials:
            material_element = self.__doc.createElement("material")
            material_element.setAttribute("id", "%s" % (material.name))
            material_element.setAttribute("name", "%s" % (material.name))
            instance_effect = self.__doc.createElement("instance_effect")
            instance_effect.setAttribute("url", "#%s_fx" % (material.name))
            material_element.appendChild(instance_effect)
            library_materials.appendChild(material_element)

        parent_element.appendChild(library_materials)

    def __export_library_geometries(self, parent_element):
        libgeo = self.__doc.createElement("library_geometries")
        parent_element.appendChild(libgeo)

        start_time = clock()
        for object_ in self.__get_objects_for_library_geometries():
            if object_.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
            object_.data.update(calc_tessface=1)
            mesh = object_.data
            mesh_verts = mesh.vertices[:]
            mesh_name = object_.name
            geo = self.__doc.createElement("geometry")
            geo.setAttribute("id", "%s" % (mesh_name))
            me = self.__doc.createElement("mesh")
            # positions
            sourcep = self.__doc.createElement("source")
            sourcep.setAttribute("id", "%s-positions" % (mesh_name))

            float_positions = []
            for vert in mesh_verts:
                float_positions.append("%.6f %.6g %.6f" % vert.co[:])

            cbPrint('vert loc took %.4f sec.' % (clock() - start_time))
            far = self.__doc.createElement("float_array")
            far.setAttribute("id", "%s-positions-array" % mesh_name)
            far.setAttribute("count", "%s" % (str(len(mesh.vertices) * 3)))
            mpos = self.__doc.createTextNode(" ".join(float_positions))
            far.appendChild(mpos)
            techcom = self.__doc.createElement("technique_common")
            acc = self.__doc.createElement("accessor")
            acc.setAttribute("source", "#%s-positions-array" % (mesh_name))
            acc.setAttribute("count", "%s" % (str(len(mesh.vertices))))
            acc.setAttribute("stride", "3")
            parx = self.__doc.createElement("param")
            parx.setAttribute("name", "X")
            parx.setAttribute("type", "float")
            pary = self.__doc.createElement("param")
            pary.setAttribute("name", "Y")
            pary.setAttribute("type", "float")
            parz = self.__doc.createElement("param")
            parz.setAttribute("name", "Z")
            parz.setAttribute("type", "float")
            acc.appendChild(parx)
            acc.appendChild(pary)
            acc.appendChild(parz)
            techcom.appendChild(acc)
            sourcep.appendChild(far)
            sourcep.appendChild(techcom)
            me.appendChild(sourcep)
            # positions
            # normals
            float_normals = ""
            float_normals_count = ""
            normal_count = 0
            normal_count = ""
            start_time = clock()
            use_sharp_edges = 0
            has_sharp_edges = 0
            bm = bmesh.new()
            bm.from_mesh(mesh)
            for face in bm.faces:
                for vert in face.verts:
                    for edge in face.edges:
                        if not edge.smooth:
                            use_sharp_edges = 1
                            has_sharp_edges = 1
                            cbPrint("use_sharp_edges = 1")
                        else:
                            use_sharp_edges = 2

                    if use_sharp_edges == 1:
                        vertex = mesh_verts[vert.index]
                        noKey = utils.veckey3d21(face.normal)
                        float_normals += '%.6f %.6f %.6f ' % noKey
                        normal_count += "1"
                    if use_sharp_edges == 2:
                        vertex = mesh_verts[vert.index]
                        noKey = utils.veckey3d21(vertex.normal)
                        float_normals += '%.6f %.6f %.6f ' % noKey
                        normal_count += "1"
                    use_sharp_edges = 0

                else:
                    fnc = ""
                    fns = 0
                    fnlx = 0
                    fnly = 0
                    fnlz = 0
                    if getattr(bpy.context.scene, "avg_pface"):
                        if fns == 0:
                            fnlx = face.normal.x
                            fnly = face.normal.y
                            fnlz = face.normal.z
                            fnc += "1"
                            cbPrint("face%s" % fnlx)
                        for fn in face_index_pairs:
                            if (face.normal.angle(fn.normal) <
                                .052):
                                if (face.normal.angle(fn.normal) >
                                    - .052):
                                    fnlx = fn.normal.x + fnlx
                                    fnly = fn.normal.x + fnly
                                    fnlz = fn.normal.x + fnlz
                                    fnc += "1"
                                    fns = 1

                        cbPrint("facen2%s" % (fnlx / len(fnc)))
                        normal_count += "1"
                        float_normals += '%.6f %.6f %.6f ' % (fnlx / len(fnc),
                            fnly / len(fnc),
                            fnlz / len(fnc))
                    else:
                        noKey = utils.veckey3d21(face.normal)
                        float_normals += '%.6f %.6f %.6f ' % noKey
                        normal_count += "1"  # for v_idx in face.vertices:

            # Hard, each vert gets normal
            # from the face.
            float_normals_count = len(normal_count) * 3
            cbPrint('normals took %.4f sec.' % (clock() - start_time))
            float_vertsc = len(normal_count)
            cbPrint(str(float_vertsc))
            normal_count = 0
            sourcenor = self.__doc.createElement("source")
            sourcenor.setAttribute("id", "%s-normals" % (mesh_name))
            farn = self.__doc.createElement("float_array")
            farn.setAttribute("id", "%s-normals-array" % (mesh_name))
            farn.setAttribute("count", "%s" % (float_normals_count))
            fpos = self.__doc.createTextNode("%s" % (float_normals))
            farn.appendChild(fpos)
            tcom = self.__doc.createElement("technique_common")
            acc = self.__doc.createElement("accessor")
            acc.setAttribute("source", "%s-normals-array" % (mesh_name))
            acc.setAttribute("count", "%s" % (float_vertsc))
            acc.setAttribute("stride", "3")
            parx = self.__doc.createElement("param")
            parx.setAttribute("name", "X")
            parx.setAttribute("type", "float")
            pary = self.__doc.createElement("param")
            pary.setAttribute("name", "Y")
            pary.setAttribute("type", "float")
            parz = self.__doc.createElement("param")
            parz.setAttribute("name", "Z")
            parz.setAttribute("type", "float")
            acc.appendChild(parx)
            acc.appendChild(pary)
            acc.appendChild(parz)
            tcom.appendChild(acc)
            sourcenor.appendChild(farn)
            sourcenor.appendChild(tcom)
            me.appendChild(sourcenor)
            # end normals
            # UVs, we will make assumptions here because this is
            # for a game export so there should always
            # be a uv set
            uvs = self.__doc.createElement("source")
            uvlay = []
            # lay = object_.data.uv_textures.active
            # if lay:
            start_time = clock()
            uvlay = object_.data.tessface_uv_textures
            if uvlay:
                cbPrint("Found UV map.")
            elif (object_.type == "MESH"):
                cbPrint("Your UV map is missing, adding.")
                override = {'object': object_}
                bpy.ops.mesh.uv_texture_add(override)

            for uvindex, uvlayer in enumerate(uvlay):
                mapslot = uvindex
                mapname = str(uvlayer.name)
                uvid = "%s-%s-%s" % (mesh_name, mapname, mapslot)
                i_n = -1
                ii = 0  # Count how many UVs we write
                test = ""
                for uf in uvlayer.data:
                # workaround, since uf.uv iteration
                # is wrong atm
                    for uv in uf.uv:
                        if i_n == -1:
                            test += '%.6f %.6f ' % uv[:]
                            i_n = 0
                        else:
                            if i_n == 7:
                        # fw('\n\t\t\t ')
                                i_n = 0
                            test += '%.6f %.6f ' % uv[:]
                        i_n += 1
                        ii += 1  # One more UV

                uvc1 = str((ii) * 2)
                uvc2 = str(ii)

            uvs.setAttribute("id", "%s-%s-%s" % (mesh_name, mapname, mapslot))
            cbPrint('UVs took %.4f sec.' % (clock() - start_time))
            fa = self.__doc.createElement("float_array")
            fa.setAttribute("id", "%s-array" % (uvid))
            fa.setAttribute("count", "%s" % (uvc1))
            uvp = self.__doc.createTextNode("%s" % (test))
            fa.appendChild(uvp)
            tc2 = self.__doc.createElement("technique_common")
            acc2 = self.__doc.createElement("accessor")
            acc2.setAttribute("source", "#%s-array" % (uvid))
            acc2.setAttribute("count", "%s" % (uvc2))
            acc2.setAttribute("stride", "2")
            pars = self.__doc.createElement("param")
            pars.setAttribute("name", "S")
            pars.setAttribute("type", "float")
            part = self.__doc.createElement("param")
            part.setAttribute("name", "T")
            part.setAttribute("type", "float")
            acc2.appendChild(pars)
            acc2.appendChild(part)
            tc2.appendChild(acc2)
            uvs.appendChild(fa)
            uvs.appendChild(tc2)
            me.appendChild(uvs)
            # enduv
            # vertcol
            # from fbx exporter
            vcols = self.__doc.createElement("source")
            cn = 0
            # list for vert alpha if found
            alpha_found = 0
            alpha_list = []
            if object_.data.tessface_vertex_colors:
                collayers = object_.data.tessface_vertex_colors
                # TODO merge these two for loops
                for collayer in collayers:
                    ni = -1
                    colname = str(collayer.name)
                    if colname == "alpha":
                        alpha_found = 1
                        for fi, cf in enumerate(collayer.data):
                            cbPrint(str(fi))
                            if len(mesh.tessfaces[fi].vertices) == 4:
                                colors = [cf.color1[:],
                                          cf.color2[:],
                                          cf.color3[:],
                                          cf.color4[:]]
                            else:
                                colors = [cf.color1[:],
                                          cf.color2[:],
                                          cf.color3[:]]
                            for colr in colors:
                                tmp = [fi, colr[0]]

                            alpha_list.append(tmp)

                        for vca in alpha_list:
                            cbPrint(str(vca))

                for collayer in collayers:
                    ni = -1
                    ii = 0  # Count how many Colors we write
                    vcol = ""
                    colname = str(collayer.name)
                    if colname == "alpha":
                        cbPrint("Alpha.")
                    else:
                        for fi, cf in enumerate(collayer.data):
                            colors = [cf.color1[:], cf.color2[:], cf.color3[:]]
                            if len(mesh.tessfaces[fi].vertices) == 4:
                                colors.append(cf.color4[:])

                            for colr in colors:
                                if ni == -1:
                                    if alpha_found == 1:
                                        tmp = alpha_list[fi]
                                        vcol += '%.6f %.6f %.6f ' % colr
                                        vcol += '%.6f ' % tmp[1]
                                        cbPrint(colr[0])
                                    else:
                                        vcol += '%.6f %.6f %.6f ' % colr
                                    ni = 0
                                else:
                                    if ni == 7:
                                        ni = 0
                                    if alpha_found == 1:
                                        tmp = alpha_list[fi]
                                        vcol += '%.6f %.6f %.6f ' % colr
                                        vcol += '%.6f ' % tmp[1]
                                        cbPrint(colr[0])
                                    else:
                                        vcol += '%.6f %.6f %.6f ' % colr
                                ni += 1
                                ii += 1  # One more Color

                        if cn == 1:
                            vcolc1 = str((ii) * 4)
                        else:
                            vcolc1 = str((ii) * 3)
                        # vcolc1=str((ii)*3)
                        vcolc2 = str(ii)

                vcols.setAttribute("id", "%s-colors" % (mesh_name))
                fa = self.__doc.createElement("float_array")
                fa.setAttribute("id", "%s-colors-array" % (mesh_name))
                fa.setAttribute("count", "%s" % (vcolc1))
                vcolp = self.__doc.createTextNode("%s" % (vcol))
                fa.appendChild(vcolp)
                tc2 = self.__doc.createElement("technique_common")
                acc3 = self.__doc.createElement("accessor")
                acc3.setAttribute("source", "#%s-colors-array" % (mesh_name))
                acc3.setAttribute("count", "%s" % (vcolc2))
                if alpha_found == 1:
                    acc3.setAttribute("stride", "4")
                else:
                    acc3.setAttribute("stride", "3")
                parr = self.__doc.createElement("param")
                parr.setAttribute("name", "R")
                parr.setAttribute("type", "float")
                parg = self.__doc.createElement("param")
                parg.setAttribute("name", "G")
                parg.setAttribute("type", "float")
                parb = self.__doc.createElement("param")
                parb.setAttribute("name", "B")
                parb.setAttribute("type", "float")
                para = self.__doc.createElement("param")
                para.setAttribute("name", "A")
                para.setAttribute("type", "float")
                acc3.appendChild(parr)
                acc3.appendChild(parg)
                acc3.appendChild(parb)
                if alpha_found == 1:
                    acc3.appendChild(para)
                alpha_found = 0
                tc2.appendChild(acc3)
                vcols.appendChild(fa)
                vcols.appendChild(tc2)
            me.appendChild(vcols)
            # endvertcol
            # vertices
            vertic = self.__doc.createElement("vertices")
            vertic.setAttribute("id", "%s-vertices" % (mesh_name))
            inputsem1 = self.__doc.createElement("input")
            inputsem1.setAttribute("semantic", "POSITION")
            inputsem1.setAttribute("source", "#%s-positions" % (mesh_name))
            vertic.appendChild(inputsem1)
            me.appendChild(vertic)
            # end vertices
            # polylist
            mat = mesh.materials[:]
            start_time = clock()
            if mat:
                for im in enumerate(mat):
                    polyl = self.__doc.createElement("polylist")
                    polyl.setAttribute("material", im[1].name)
                    verts = ""
                    face_count = ""
                    face_counter = 0
                    ni = 0
                    texindex = 0
                    nverts = ""
                    for f in mesh.tessfaces:
                        fi = f.vertices[:]
                        if f.material_index == im[0]:
                            nverts += str(len(f.vertices)) + " "
                            face_count += str(
                                "%s" % (face_counter))
                            for v in f.vertices:
                                verts += str(v) + " "
                                if f.use_smooth:
                                    if has_sharp_edges == 1:
                                        verts += str("%s " % (ni))
                                        ni += 1
                                    else:
                                        verts += str(v) + " "
                                    # verts += str("%s "%(ni))
                                    # ni += 1
                                else:
                                    verts += str("%s " % (ni))
                                verts += str("%s " % (texindex))
                                if mesh.vertex_colors:
                                    verts += str(
                                        "%s " % (texindex))
                                texindex += 1

                        if f.use_smooth:
                            if has_sharp_edges != 1:
                                ni += len(f.vertices)
                        else:
                            ni += 1  # #<--naughty naughty
                        if f.material_index == im[0]:
                            texindex = texindex
                        else:
                            texindex += len(fi)  # 4#3

                    cbPrint(str(ni))
                    verts += ""
                    cbPrint('polylist took %.4f sec.' % (clock() - start_time))
                    polyl.setAttribute("count", "%s" % (len(face_count)))
                    inpv = self.__doc.createElement("input")
                    inpv.setAttribute("semantic", "VERTEX")
                    inpv.setAttribute("source", "#%s-vertices" % (mesh_name))
                    inpv.setAttribute("offset", "0")
                    polyl.appendChild(inpv)
                    inpn = self.__doc.createElement("input")
                    inpn.setAttribute("semantic", "NORMAL")
                    inpn.setAttribute("source", "#%s-normals" % (mesh_name))
                    inpn.setAttribute("offset", "1")
                    polyl.appendChild(inpn)
                    inpuv = self.__doc.createElement("input")
                    inpuv.setAttribute("semantic", "TEXCOORD")
                    inpuv.setAttribute("source", "#%s" % (uvid))
                    # will always be 2, vcolors can be 2 or 3
                    inpuv.setAttribute("offset", "2")
                    inpuv.setAttribute("set", "%s" % (mapslot))
                    polyl.appendChild(inpuv)
                    if mesh.vertex_colors:
                        inpvcol = self.__doc.createElement("input")
                        inpvcol.setAttribute("semantic", "COLOR")
                        inpvcol.setAttribute("source", "#%s-colors" % (mesh_name))
                        # vcolors can be 2 or 3
                        inpvcol.setAttribute("offset", "3")
                        polyl.appendChild(inpvcol)
                    vc = self.__doc.createElement("vcount")
                    vcl = self.__doc.createTextNode("%s" % (nverts))
                    vc.appendChild(vcl)
                    pl = self.__doc.createElement("p")
                    pltn = self.__doc.createTextNode("%s" % (verts))
                    pl.appendChild(pltn)
                    polyl.appendChild(vc)
                    polyl.appendChild(pl)
                    me.appendChild(polyl)

                    # endpolylist
            has_sharp_edges = 0
            emt = self.__doc.createElement("extra")
            emtt = self.__doc.createElement("technique")
            emtt.setAttribute("profile", "MAYA")
            dsd = self.__doc.createElement("double_sided")
            dsdtn = self.__doc.createTextNode("1")
            dsd.appendChild(dsdtn)
            emtt.appendChild(dsd)
            emt.appendChild(emtt)
            me.appendChild(emt)
            geo.appendChild(me)
            libgeo.appendChild(geo)

            # bpy.data.meshes.remove(mesh)

    def __get_objects_for_library_geometries(self):
        objects = []
        for object_ in bpy.context.selected_objects:
            if (object_.name[:6] != "_joint"):
                if (object_.type == "MESH"):
                    objects.append(object_)

        return objects

    def __export_library_controllers(self, parent_element):
        library_node = self.__doc.createElement("library_controllers")

        for selected_object in bpy.context.selected_objects:
            if not "_boneGeometry" in selected_object.name:
                # "some" code borrowed from dx exporter
                armatures = self.__get_armatures(selected_object)

                if armatures:
                    self.__process_bones(library_node,
                                         selected_object,
                                         armatures)

        parent_element.appendChild(library_node)

    def __get_armatures(self, object_):
        return [modifier for modifier in object_.modifiers
                if modifier.type == "ARMATURE"]

    def __process_bones(self, parent_node, object_, armatures):
        armature = armatures[0].object

        controller_node = self.__doc.createElement("controller")
        parent_node.appendChild(controller_node)

        controller_node.setAttribute("id", "%s_%s" % (armature.name,
                                                      object_.name))
        skin_node = self.__doc.createElement("skin")
        skin_node.setAttribute("source", "#%s" % object_.name)
        controller_node.appendChild(skin_node)
        bsm = self.__doc.createElement("bind_shape_matrix")
        bsmv = self.__doc.createTextNode(utils.matrix_to_string(Matrix()))
        bsm.appendChild(bsmv)
        skin_node.appendChild(bsm)

        armature_bones = self.__get_bones(armature)

        self.__process_bones_joints(object_.name,
                                    skin_node,
                                    armature.name,
                                    armature_bones)

        self.__process_bones_matrices(object_.name,
                                      skin_node,
                                      armature.name,
                                      armature_bones)

        vertex_groups_lengths, vw = self.__process_bones_weights(object_,
                                                 skin_node,
                                                 armature.name,
                                                 armature_bones)

        jnts = self.__doc.createElement("joints")
        is1 = self.__doc.createElement("input")
        is1.setAttribute("semantic", "JOINT")
        is1.setAttribute("source", "#%s_%s_joints"
                         % (armature.name, object_.name))
        jnts.appendChild(is1)

        is2 = self.__doc.createElement("input")
        is2.setAttribute("semantic", "INV_BIND_MATRIX")
        is2.setAttribute("source", "#%s_%s_matrices"
                         % (armature.name, object_.name))
        jnts.appendChild(is2)
        skin_node.appendChild(jnts)

        vertw = self.__doc.createElement("vertex_weights")
        vertw.setAttribute("count", "%s" % len(object_.data.vertices))

        is3 = self.__doc.createElement("input")
        is3.setAttribute("semantic", "JOINT")
        is3.setAttribute("offset", "0")
        is3.setAttribute("source", "#%s_%s_joints"
                         % (armature.name, object_.name))
        vertw.appendChild(is3)

        is4 = self.__doc.createElement("input")
        is4.setAttribute("semantic", "WEIGHT")
        is4.setAttribute("offset", "1")
        is4.setAttribute("source", "#%s_%s_weights"
                         % (armature.name, object_.name))
        vertw.appendChild(is4)

        vcnt = self.__doc.createElement("vcount")
        vcnt1 = self.__doc.createTextNode(vertex_groups_lengths)
        vcnt.appendChild(vcnt1)
        vertw.appendChild(vcnt)

        vlst = self.__doc.createElement("v")
        vlst1 = self.__doc.createTextNode(vw)
        vlst.appendChild(vlst1)
        vertw.appendChild(vlst)
        skin_node.appendChild(vertw)

    def __process_bones_joints(self,
                               object_name,
                               skin_node,
                               armature_name,
                               armature_bones):
        source_node = self.__doc.createElement("source")
        source_node.setAttribute("id", "%s_%s_joints" % (armature_name,
                                                         object_name))

        skin_node.appendChild(source_node)

        idref_array_node = self.__doc.createElement("IDREF_array")
        idref_array_node.setAttribute("id", "%s_%s_joints_array"
                                      % (armature_name, object_name))
        idref_array_node.setAttribute("count", "%s" % len(armature_bones))
        bone_names = self.__get_bone_names_for_idref(armature_bones)

        cbPrint(bone_names)

        idref_array_node.appendChild(self.__doc.createTextNode(bone_names))
        source_node.appendChild(idref_array_node)

        technique_node = self.__doc.createElement("technique_common")
        accessor_node = self.__doc.createElement("accessor")
        accessor_node.setAttribute("source", "#%s_%s_joints_array"
                                   % (armature_name, object_name))
        accessor_node.setAttribute("count", "%s" % len(armature_bones))
        accessor_node.setAttribute("stride", "1")

        param_node = self.__doc.createElement("param")
        param_node.setAttribute("type", "IDREF")
        accessor_node.appendChild(param_node)
        technique_node.appendChild(accessor_node)
        source_node.appendChild(technique_node)

    def __process_bones_matrices(self,
                                 object_name,
                                 skin_node,
                                 armature_name,
                                 armature_bones):
        source_matrices_node = self.__doc.createElement("source")
        source_matrices_node.setAttribute("id", "%s_%s_matrices"
                                          % (armature_name, object_name))

        skin_node.appendChild(source_matrices_node)

        float_array_node = self.__doc.createElement("float_array")
        float_array_node.setAttribute("id", "%s_%s_matrices_array"
                                      % (armature_name, object_name))
        float_array_node.setAttribute("count", "%s"
                                      % (len(armature_bones) * 16))
        self.__export_float_array(armature_name, armature_bones, float_array_node)
        source_matrices_node.appendChild(float_array_node)

        technique_node = self.__doc.createElement("technique_common")
        accessor_node = self.__doc.createElement("accessor")
        accessor_node.setAttribute("source", "#%s_%s_matrices_array"
                                   % (armature_name, object_name))
        accessor_node.setAttribute("count", "%s" % (len(armature_bones)))
        accessor_node.setAttribute("stride", "16")
        param_node = self.__doc.createElement("param")
        param_node.setAttribute("type", "float4x4")
        accessor_node.appendChild(param_node)
        technique_node.appendChild(accessor_node)
        source_matrices_node.appendChild(technique_node)

    def __process_bones_weights(self,
                                object_,
                                skin_node,
                                armature_name,
                                armature_bones):
        source_node = self.__doc.createElement("source")
        source_node.setAttribute("id", "%s_%s_weights"
                                         % (armature_name, object_.name))

        skin_node.appendChild(source_node)

        float_array = self.__doc.createElement("float_array")
        float_array.setAttribute("id", "%s_%s_weights_array"
                                 % (armature_name, object_.name))

        group_weights = []
        vw = ""
        vertex_groups_lengths = []
        vertex_count = 0

        # TODO: review that loop to find bugs and useless code
        for vertex in object_.data.vertices:
            for group in vertex.groups:
                group_weights.append(group.weight)
                for vertex_group in object_.vertex_groups:
                    if vertex_group.index == group.group:
                        for bone_id, bone in enumerate(armature_bones):
                            if bone.name == vertex_group.name:
                                vw += "%s " % bone_id

                vw += "%s " % vertex_count
                vertex_count += 1

            vertex_groups_lengths.append("%s" % len(vertex.groups))

        float_array.setAttribute("count", "%s" % vertex_count)
        lfarwa = self.__doc.createTextNode(
                        utils.floats_to_string(group_weights, " ", "%.6f"))

        float_array.appendChild(lfarwa)

        technique_node = self.__doc.createElement("technique_common")

        accessor_node = self.__doc.createElement("accessor")
        accessor_node.setAttribute("source", "#%s_%s_weights_array"
                                      % (armature_name, object_.name))
        accessor_node.setAttribute("count", "%s" % vertex_count)
        accessor_node.setAttribute("stride", "1")

        param_node = self.__doc.createElement("param")
        param_node.setAttribute("type", "float")
        accessor_node.appendChild(param_node)
        technique_node.appendChild(accessor_node)
        source_node.appendChild(float_array)
        source_node.appendChild(technique_node)

        return " ".join(vertex_groups_lengths), vw

    def __export_library_animation_clips_and_animations(self, parent_element):
        libanmcl = self.__doc.createElement("library_animation_clips")
        libanm = self.__doc.createElement("library_animations")
        parent_element.appendChild(libanmcl)
        parent_element.appendChild(libanm)

        is_merge_inprogress = 0
        ande = 0
        ande2 = 0
        for object_ in bpy.context.selected_objects:
            lnname = str(object_.name)
            for item in bpy.context.blend_data.groups:
                if item:
                    ename = str(item.id_data.name)

            if lnname[:8] == "animnode":
                ande2 = 1
                actname = object_["animname"]
                sf = object_["startframe"]
                ef = object_["endframe"]
                cbPrint(actname)
                cbPrint(sf)
                cbPrint(ef)
                animation_clip = self.__doc.createElement("animation_clip")
                animation_clip.setAttribute("id",
                                            "%s-%s" % (actname, ename[14:]))
                animation_clip.setAttribute("start",
                                            "%s" % (utils.convert_time(sf)))
                animation_clip.setAttribute("end",
                                            "%s" % (utils.convert_time(ef)))
                for object_ in bpy.context.selected_objects:
                    if object_.animation_data:
                        if object_.type == 'ARMATURE':
                            cbPrint("Object is armature, cannot process animations.")
                        elif object_.animation_data.action:

                            for axis in iter(AXES):
                                anm = self.__get_animation_location(object_, axis)
                                libanm.appendChild(anm)

                            for axis in iter(AXES):
                                anm = self.__get_animation_rotation(object_, axis)
                                libanm.appendChild(anm)

                            self.__export_instance_animation_parameters(object_,
                                                                animation_clip)

                libanmcl.appendChild(animation_clip)

        if ande2 == 0:
            for object_ in bpy.context.selected_objects:
                if object_.animation_data:
                    if object_.type == 'ARMATURE':
                        cbPrint("Object is armature, cannot process animations.")
                    else:
                        if object_.animation_data.action:
                            for item in bpy.context.blend_data.groups:
                                if item:
                                    ename = str(item.id_data.name)

                            act = object_.animation_data.action
                            curves = act.fcurves
                            frstrt = curves.data.frame_range[0]
                            frend = curves.data.frame_range[1]
                            anmlx = self.__get_animation_location(object_, 'X')
                            anmly = self.__get_animation_location(object_, 'Y')
                            anmlz = self.__get_animation_location(object_, 'Z')
                            anmrx = self.__get_animation_rotation(object_, 'X')
                            anmry = self.__get_animation_rotation(object_, 'Y')
                            anmrz = self.__get_animation_rotation(object_, 'Z')
                            # animation clip name and frame range
                            for ai in object_.children:
                                aname = str(ai.name)
                                if aname[:8] == "animnode":
                                    ande = 1
                                    cbPrint(ai["animname"])
                                    cbPrint(ai["startframe"])
                                    cbPrint(ai["endframe"])
                                    act_name = ai["animname"]
                                    start_frame = ai["startframe"]
                                    end_frame = ai["endframe"]

                                    animation_clip = self.__export__animation_clip(
                                                                object_,
                                                                ename,
                                                                act_name,
                                                                start_frame,
                                                                end_frame)
                                    libanmcl.appendChild(animation_clip)

                            if ande == 0:
                                if getattr(bpy.context.scene, "merge_anm"):
                                    if is_merge_inprogress == 0:
                                        animation_clip = self.__export__animation_clip(
                                                                object_,
                                                                ename,
                                                                act.name,
                                                                frstrt,
                                                                frend)
                                        is_merge_inprogress = 1
                                    else:
                                        cbPrint("Merging clips.")
                                        self.__export_merge_animation_clip(
                                                                object_,
                                                                animation_clip,
                                                                frstrt,
                                                                frend)
                                else:
                                    animation_clip = self.__export__animation_clip(
                                                                object_,
                                                                ename,
                                                                act.name,
                                                                frstrt,
                                                                frend)
                        if is_merge_inprogress == 0:
                            libanmcl.appendChild(animation_clip)
                        libanm.appendChild(anmlx)
                        libanm.appendChild(anmly)
                        libanm.appendChild(anmlz)
                        libanm.appendChild(anmrx)
                        libanm.appendChild(anmry)
                        libanm.appendChild(anmrz)

            if is_merge_inprogress == 1:
                libanmcl.appendChild(animation_clip)

    def __export_merge_animation_clip(self, object_, animation_clip,
                                      start_frame, end_frame):
        if self.__merged_clip_start > start_frame:
            animation_clip.setAttribute("start",
                                      "%f" % (utils.convert_time(start_frame)))
            self.__merged_clip_start = start_frame
        if self.__merged_clip_end < end_frame:
            animation_clip.setAttribute("end",
                                        "%f" % (utils.convert_time(end_frame)))
            self.__merged_clip_end = end_frame
        self.__export_instance_animation_parameters(object_, animation_clip)

    def __export__animation_clip(self, object_, ename, act_name,
                                 start_frame, end_frame):
        animation_clip = self.__doc.createElement("animation_clip")
        animation_clip.setAttribute("id", "%s-%s" % (act_name, ename[14:]))
        # RC does not seem to like doubles and truncates them to integers
        animation_clip.setAttribute("start",
                                    "%f" % (utils.convert_time(start_frame)))
        animation_clip.setAttribute("end",
                                    "%f" % (utils.convert_time(end_frame)))
        self.__merged_clip_start = start_frame
        self.__merged_clip_end = end_frame
        self.__export_instance_animation_parameters(object_, animation_clip)

        return animation_clip

    def __export_instance_animation_parameters(self, object_, animation_clip):
        self.__export_instance_parameter(object_, animation_clip, "location")
        self.__export_instance_parameter(object_, animation_clip,
                                         "rotation_euler")

    def __export_instance_parameter(self, object_, animation_clip, parameter):
        for axis in iter(AXES):
            inst = self.__doc.createElement("instance_animation")
            inst.setAttribute("url",
                              "#%s_%s_%s" % (object_.name, parameter, axis))
            animation_clip.appendChild(inst)

    def __export_library_visual_scenes(self, parent_element):
        current_element = self.__doc.createElement("library_visual_scenes")
        visual_scene = self.__doc.createElement("visual_scene")
        current_element.appendChild(visual_scene)
        parent_element.appendChild(current_element)

        # doesn't matter what name we have here as long as it is
        # the same for <scene>
        visual_scene.setAttribute("id", "scene")
        visual_scene.setAttribute("name", "scene")
        for item in bpy.context.blend_data.groups:
            if item:
                ename = str(item.id_data.name)
                node1 = self.__doc.createElement("node")
                node1.setAttribute("id", "%s" % (ename))
                node1.setIdAttribute('id')
            visual_scene.appendChild(node1)
            node1 = self.write_visual_scene(item.objects, node1)
            # export node settings
            ext1 = self.__doc.createElement("extra")
            tc3 = self.__doc.createElement("technique")
            tc3.setAttribute("profile", "CryEngine")
            prop1 = self.__doc.createElement("properties")
            if getattr(bpy.context.scene, "project_type") == 'CGF':
                pcgf = self.__doc.createTextNode("fileType=cgf")
                prop1.appendChild(pcgf)
            elif getattr(bpy.context.scene, "project_type") == 'CGA':
                pcga = self.__doc.createTextNode("fileType=cgf")
                prop1.appendChild(pcga)
            elif getattr(bpy.context.scene, "project_type") == 'CHR':
                pchrcaf = self.__doc.createTextNode("fileType=chrcaf")
                prop1.appendChild(pchrcaf)
            else:
                pcgf = self.__doc.createTextNode("fileType=cgf")
                prop1.appendChild(pcgf)
            if getattr(bpy.context.scene, "donot_merge"):
                pdnm = self.__doc.createTextNode("DoNotMerge")
                prop1.appendChild(pdnm)
            tc3.appendChild(prop1)
            ext1.appendChild(tc3)
            node1.appendChild(ext1)

    def __export_scene(self, parent_element):
        # <scene> nothing really changes here or rather it doesn't need to.
        scene = self.__doc.createElement("scene")
        ivs = self.__doc.createElement("instance_visual_scene")
        ivs.setAttribute("url", "#scene")
        scene.appendChild(ivs)
        parent_element.appendChild(scene)


def write_to_file(config, doc, file_name, exe):
    xml_string = doc.toprettyxml(indent="  ")
    file = open(file_name, "w")
    file.write(xml_string)
    file.close()

    dae_file_for_rc = utils.get_absolute_path_for_rc(file_name)
    rc_params = ["/verbose", "/threads=processors", "/realignchunks"]

    if getattr(bpy.context.scene, "refresh_rc"):
        rc_params.append("/refresh")

    if getattr(bpy.context.scene, "run_rc") or getattr(bpy.context.scene, "do_materials"):
        if getattr(bpy.context.scene, "do_materials"):
            rc_params.append("/createmtl=1")

        rc_process = utils.run_rc(exe, dae_file_for_rc, rc_params)

        if getattr(bpy.context.scene, "do_materials"):
            mtl_fix_thread = threading.Thread(
                target=fix_normalmap_in_mtls,
                args=(rc_process, file_name)
            )
            mtl_fix_thread.start()

    if getattr(bpy.context.scene, "make_layer"):
        layer = make_layer(file_name)
        lyr_file_name = os.path.splitext(file_name)[0] + ".lyr"
        file = open(lyr_file_name, 'w')
        file.write(layer)
        file.close()


def make_layer(fname):
    lName = "ExportedLayer"
    layerDoc = Document()
    # ObjectLayer
    objLayer = layerDoc.createElement("ObjectLayer")
    # Layer
    layer = layerDoc.createElement("Layer")
    layer.setAttribute('name', lName)
    layer.setAttribute('GUID', utils.get_guid())
    layer.setAttribute('FullName', lName)
    layer.setAttribute('External', '0')
    layer.setAttribute('Exportable', '1')
    layer.setAttribute('ExportLayerPak', '1')
    layer.setAttribute('DefaultLoaded', '0')
    layer.setAttribute('HavePhysics', '1')
    layer.setAttribute('Expanded', '0')
    layer.setAttribute('IsDefaultColor', '1')
    # Layer Objects
    layerObjects = layerDoc.createElement("LayerObjects")
    # Actual Objects
    for group in bpy.context.blend_data.groups:
        if len(group.objects) > 1:
            origin = 0, 0, 0
            rotation = 1, 0, 0, 0
        else:
            origin = group.objects[0].location
            rotation = group.objects[0].delta_rotation_quaternion

        if 'CryExportNode' in group.name:
            object_node = layerDoc.createElement("Object")
            object_node.setAttribute('name', group.name[14:])
            object_node.setAttribute('Type', 'Entity')
            object_node.setAttribute('Id', utils.get_guid())
            object_node.setAttribute('LayerGUID', layer.getAttribute('GUID'))
            object_node.setAttribute('Layer', lName)
            cbPrint(origin)
            positionString = "%s, %s, %s" % origin[:]
            object_node.setAttribute('Pos', positionString)
            rotationString = "%s, %s, %s, %s" % rotation[:]
            object_node.setAttribute('Rotate', rotationString)
            object_node.setAttribute('EntityClass', 'BasicEntity')
            object_node.setAttribute('FloorNumber', '-1')
            object_node.setAttribute('RenderNearest', '0')
            object_node.setAttribute('NoStaticDecals', '0')
            object_node.setAttribute('CreatedThroughPool', '0')
            object_node.setAttribute('MatLayersMask', '0')
            object_node.setAttribute('OutdoorOnly', '0')
            object_node.setAttribute('CastShadow', '1')
            object_node.setAttribute('MotionBlurMultiplier', '1')
            object_node.setAttribute('LodRatio', '100')
            object_node.setAttribute('ViewDistRatio', '100')
            object_node.setAttribute('HiddenInGame', '0')
            properties = layerDoc.createElement("Properties")
            properties.setAttribute('object_Model', '/Objects/%s.cgf'
                                    % group.name[14:])
            properties.setAttribute('bCanTriggerAreas', '0')
            properties.setAttribute('bExcludeCover', '0')
            properties.setAttribute('DmgFactorWhenCollidingAI', '1')
            properties.setAttribute('esFaction', '')
            properties.setAttribute('bHeavyObject', '0')
            properties.setAttribute('bInteractLargeObject', '0')
            properties.setAttribute('bMissionCritical', '0')
            properties.setAttribute('bPickable', '0')
            properties.setAttribute('soclasses_SmartObjectClass', '')
            properties.setAttribute('bUsable', '0')
            properties.setAttribute('UseMessage', '0')
            health = layerDoc.createElement("Health")
            health.setAttribute('bInvulnerable', '1')
            health.setAttribute('MaxHealth', '500')
            health.setAttribute('bOnlyEnemyFire', '1')
            interest = layerDoc.createElement("Interest")
            interest.setAttribute('soaction_Action', '')
            interest.setAttribute('bInteresting', '0')
            interest.setAttribute('InterestLevel', '1')
            interest.setAttribute('Pause', '15')
            interest.setAttribute('Radius', '20')
            interest.setAttribute('bShared', '0')
            vOffset = layerDoc.createElement('vOffset')
            vOffset.setAttribute('x', '0')
            vOffset.setAttribute('y', '0')
            vOffset.setAttribute('z', '0')
            interest.appendChild(vOffset)
            properties.appendChild(health)
            properties.appendChild(interest)
            object_node.appendChild(properties)
            layerObjects.appendChild(object_node)

    layer.appendChild(layerObjects)
    objLayer.appendChild(layer)
    layerDoc.appendChild(objLayer)
    return layerDoc.toprettyxml(indent="  ")


def fix_normalmap_in_mtls(rc_process, dae_file):
    SUCCESS = 0

    return_code = rc_process.wait()

    if return_code == SUCCESS:
        export_directory = os.path.dirname(dae_file)

        mtl_files = utils.get_mtl_files_in_directory(export_directory)

        for mtl_file_name in mtl_files:
            fix_normalmap_in_mtl(mtl_file_name)


def fix_normalmap_in_mtl(mtl_file_name):
    TMP_FILE_SUFFIX = ".tmp"
    BAD_TAG_NAME = "<Texture Map=\"NormalMap\" File=\""
    GOOD_TAG_NAME = "<Texture Map=\"Bumpmap\" File=\""

    tmp_mtl_file_name = mtl_file_name + TMP_FILE_SUFFIX
    mtl_old_file = open(mtl_file_name, "r")
    mtl_new_file = open(tmp_mtl_file_name, "w")

    for line in mtl_old_file:
        line = line.replace(BAD_TAG_NAME, GOOD_TAG_NAME)
        mtl_new_file.write(line)

    mtl_old_file.close()
    mtl_new_file.close()

    os.remove(mtl_file_name)
    os.rename(tmp_mtl_file_name, mtl_file_name)


def save(config):
    # prevent wasting time for exporting if RC was not found
    if not os.path.isfile(config.rc_path):
        raise exceptions.NoRcSelectedException

    exporter = CrytekDaeExporter(config)
    exporter.export()


def menu_function_export(self, context):
    self.layout.operator(CrytekDaeExporter.bl_idname, text="Export Crytek Dae")


def register():
    bpy.utils.register_class(CrytekDaeExporter)
    bpy.types.INFO_MT_file_export.append(menu_function_export)

    bpy.utils.register_class(TriangulateMeError)
    bpy.utils.register_class(Error)


def unregister():
    bpy.utils.unregister_class(CrytekDaeExporter)
    bpy.types.INFO_MT_file_export.remove(menu_function_export)
    bpy.utils.unregister_class(TriangulateMeError)
    bpy.utils.unregister_class(Error)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mesh.crytekdae('INVOKE_DEFAULT')
