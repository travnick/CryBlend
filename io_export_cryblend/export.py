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
#                Some code borrowed from fbx exporter Campbell Barton
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

from io_export_cryblend.rc import RCInstance
from io_export_cryblend.outPipe import cbPrint
from io_export_cryblend.utils import join

from bpy_extras.io_utils import ExportHelper
from datetime import datetime
from mathutils import Matrix, Vector
from time import clock
from xml.dom.minidom import Document, Element, parse, parseString
import bmesh
import copy
import os
import threading
import subprocess
import time
import xml.dom.minidom


AXES = {
    'X': 0,
    'Y': 1,
    'Z': 2,
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
        normalized_path = os.path.normpath(config.textures_dir)
        self.__textures_parent_directory = os.path.dirname(normalized_path)
        cbPrint("Normalized textures directory: {!r}".format(normalized_path),
                'debug')
        cbPrint("Textures parent directory: {!r}".format(
                                            self.__textures_parent_directory),
                'debug')

    def export(self):
        self.__prepare_for_export()

        root_element = self.__doc.createElement('collada')
        root_element.setAttribute("xmlns",
                               "http://www.collada.org/2005/11/COLLADASchema")
        root_element.setAttribute("version", "1.4.1")
        self.__doc.appendChild(root_element)
        self.__create_file_header(root_element)

        # Just here for future use:
        self.__export_library_cameras(root_element)
        self.__export_library_lights(root_element)
        ###

        self.__export_library_images(root_element)
        self.__export_library_effects(root_element)
        self.__export_library_materials(root_element)
        self.__export_library_geometries(root_element)

        utils.add_fakebones()
        self.__export_library_controllers(root_element)
        self.__export_library_animation_clips_and_animations(root_element)
        self.__export_library_visual_scenes(root_element)
        utils.remove_fakebones()

        self.__export_scene(root_element)

        converter = RCInstance(self.__config)
        converter.convert_dae(self.__doc)

        write_scripts(self.__config)

    def __prepare_for_export(self):
        utils.clean_file()

        if self.__config.apply_modifiers:
            utils.apply_modifiers()

        if self.__config.fix_weights:
            utils.fix_weights()

    def __create_file_header(self, parent_element):
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

    def __export_library_cameras(self, root_element):
        libcam = self.__doc.createElement("library_cameras")
        root_element.appendChild(libcam)

    def __export_library_lights(self, root_element):
        liblights = self.__doc.createElement("library_lights")
        root_element.appendChild(liblights)

    def __export_library_images(self, parent_element):
        library_images = self.__doc.createElement("library_images")
        parent_element.appendChild(library_images)

        images_to_convert = []

        for image in self.__get_image_textures_in_export_nodes():
            image_element = self.__export_library_image(images_to_convert,
                                                        image)
            library_images.appendChild(image_element)

        if self.__config.convert_source_image_to_dds:
            self.__convert_images_to_dds(images_to_convert)

    def __export_library_image(self, images_to_convert, image):
        if self.__config.convert_source_image_to_dds:
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

    def __get_image_textures_in_export_nodes(self):
        images = []
        textures = utils.get_type("textures")

        for texture in textures:
            try:
                if utils.is_valid_image(texture.image):
                    images.append(texture.image)

            except AttributeError:
                # don't care about non-image textures
                pass

        # return only unique images
        return list(set(images))

    def __convert_images_to_dds(self, images_to_convert):
        converter = RCInstance(self.__config)
        converter.convert_tif(images_to_convert)

    def __export_library_effects(self, parent_element):
        current_element = self.__doc.createElement("library_effects")
        parent_element.appendChild(current_element)
        for material in utils.get_type("materials"):
            self.__export_library_effects_material(material, current_element)

    def __export_library_effects_material(self, material, current_element):
        images = [[], [], []]
        texture_slots = utils.get_texture_slots_for_material(material)
        for texture_slot in texture_slots:
            image = texture_slot.texture.image
            if not image:
                raise exceptions.CryBlendException(
                            "One of texture slots has no image assigned.")

            surface, sampler = self.__create_surface_and_sampler(image.name)
            if texture_slot.use_map_color_diffuse:
                images[0] = [image.name, surface, sampler] 
            if texture_slot.use_map_color_spec:
                images[1] = [image.name, surface, sampler]
            if texture_slot.use_map_normal:
                images[2] = [image.name, surface, sampler]

        effect_node = self.__doc.createElement("effect")
        effect_node.setAttribute("id", "%s_fx" % material.name)
        profile_node = self.__doc.createElement("profile_COMMON")
        for image in images:
            if len(image) != 0:
                profile_node.appendChild(image[1])
                profile_node.appendChild(image[2])
        technique_common = self.__doc.createElement("technique")
        technique_common.setAttribute("sid", "common")

        phong = self.__create_material_node(material, images)
        technique_common.appendChild(phong)
        profile_node.appendChild(technique_common)
        
        extra = self.__create_double_sided_extra("GOOGLEEARTH")
        profile_node.appendChild(extra)
        effect_node.appendChild(profile_node)

        extra = self.__create_double_sided_extra("MAX3D")
        effect_node.appendChild(extra)
        current_element.appendChild(effect_node)

    def __create_surface_and_sampler(self, image_name):
        surface = self.__doc.createElement("newparam")
        surface.setAttribute("sid", "%s-surface" % image_name)
        surface_node = self.__doc.createElement("surface")
        surface_node.setAttribute("type", "2D")
        init_from_node = self.__doc.createElement("init_from")
        temp_node = self.__doc.createTextNode(image_name)
        init_from_node.appendChild(temp_node)
        surface_node.appendChild(init_from_node)
        surface.appendChild(surface_node)
        sampler = self.__doc.createElement("newparam")
        sampler.setAttribute("sid", "%s-sampler" % image_name)
        sampler_node = self.__doc.createElement("sampler2D")
        source_node = self.__doc.createElement("source")
        temp_node = self.__doc.createTextNode(
                                        "%s-surface" % (image_name))
        source_node.appendChild(temp_node)
        sampler_node.appendChild(source_node)
        sampler.appendChild(sampler_node)

        return surface, sampler

    def __create_material_node(self, material, images):
        phong = self.__doc.createElement("phong")

        emission = self.__create_color_node(material, "emission")
        ambient = self.__create_color_node(material, "ambient")
        if len(images[0]) != 0:
            diffuse = self.__create_texture_node(images[0][0], "diffuse")
        else:
            diffuse = self.__create_color_node(material, "diffuse")
        if len(images[1]) != 0:
            specular = self.__create_texture_node(images[1][0], "specular")
        else:
            specular = self.__create_color_node(material, "specular")

        shininess = self.__create_attribute_node(material, "shininess")
        index_refraction = self.__create_attribute_node(material, "index_refraction")

        phong.appendChild(emission)
        phong.appendChild(ambient)
        phong.appendChild(diffuse)
        phong.appendChild(specular)
        phong.appendChild(shininess)
        phong.appendChild(index_refraction)
        if len(images[2]) != 0:
            normal = self.__create_texture_node(images[2][0], "normal")
            phong.appendChild(normal)

        return phong

    def __create_color_node(self, material, type_):
        node = self.__doc.createElement(type_)
        color = self.__doc.createElement("color")
        color.setAttribute("sid", type_)
        col = utils.get_material_color(material, type_)
        color_text = self.__doc.createTextNode(col)
        color.appendChild(color_text)
        node.appendChild(color)

        return node

    def __create_texture_node(self, image_name, type_):
        node = self.__doc.createElement(type_)
        texture = self.__doc.createElement("texture")
        texture.setAttribute("texture", "%s-sampler" % image_name)
        node.appendChild(texture)

        return node

    def __create_attribute_node(self, material, type_):
        node = self.__doc.createElement(type_)
        float = self.__doc.createElement("float")
        float.setAttribute("sid", type_)
        val = utils.get_material_attribute(material, type_)
        value = self.__doc.createTextNode(val)
        float.appendChild(value)
        node.appendChild(float)

        return node

    def __create_double_sided_extra(self, profile):
        extra = self.__doc.createElement("extra")
        technique = self.__doc.createElement("technique")
        technique.setAttribute("profile", profile)
        double_sided = self.__doc.createElement("double_sided")
        double_sided_value = self.__doc.createTextNode("1")
        double_sided.appendChild(double_sided_value)
        technique.appendChild(double_sided)
        extra.appendChild(technique)

        return extra

    def __export_library_materials(self, parent_element):
        library_materials = self.__doc.createElement("library_materials")
        materials = utils.get_type("materials")

        for material in materials:
            material_element = self.__doc.createElement("material")
            material_element.setAttribute("id", "%s" % (material.name))
            instance_effect = self.__doc.createElement("instance_effect")
            instance_effect.setAttribute("url", "#%s_fx" % (material.name))
            material_element.appendChild(instance_effect)
            library_materials.appendChild(material_element)

        parent_element.appendChild(library_materials)

    def __export_library_geometries(self, parent_element):
        libgeo = self.__doc.createElement("library_geometries")
        parent_element.appendChild(libgeo)
        for object_ in utils.get_type("geometry"):
            bpy.context.scene.objects.active = object_
            if object_.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            object_.data.update(calc_tessface=1)
            mesh = object_.data
            object_.name = object_.name
            geometry_node = self.__doc.createElement("geometry")
            geometry_node.setAttribute("id", "%s" % (object_.name))
            mesh_node = self.__doc.createElement("mesh")

            start_time = clock()
            self.__write_positions(object_, mesh, mesh_node)
            cbPrint('Positions took %.4f sec.' % (clock() - start_time))

            start_time = clock()
            self.__write_normals(object_, mesh, mesh_node)
            cbPrint('Normals took %.4f sec.' % (clock() - start_time))

            start_time = clock()
            self.__write_uvs(object_, mesh, mesh_node)
            cbPrint('UVs took %.4f sec.' % (clock() - start_time))

            start_time = clock()
            self.__write_vertex_colors(object_, mesh, mesh_node)
            cbPrint('Vertex colors took %.4f sec.' % (clock() - start_time))

            start_time = clock()
            self.__write_vertices(object_, mesh, mesh_node)
            cbPrint('Vertices took %.4f sec.' % (clock() - start_time))

            start_time = clock()
            self.__write_polylist(object_, mesh, mesh_node)
            cbPrint('Polylist took %.4f sec.' % (clock() - start_time))

            extra = self.__create_double_sided_extra("MAYA")
            mesh_node.appendChild(extra)
            geometry_node.appendChild(mesh_node)
            libgeo.appendChild(geometry_node)

    def __write_positions(self, object_, mesh, root):
        float_positions = []
        for vertex in mesh.vertices:
            float_positions.extend(vertex.co)

        id_ = "{!s}-positions".format(object_.name)
        source = utils.write_source(id_, "float", float_positions, "XYZ")
        root.appendChild(source)

    def __write_normals(self, object_, mesh, root):
        float_normals = []
        float_normals_count = ""

        for face in mesh.tessfaces:
            if face.use_smooth:
                for vert in face.vertices:
                    vertex = mesh.vertices[vert]
                    float_normals.extend(vertex.normal)

            else:
                if self.__config.average_planar:
                    count = 1
                    nx = face.normal.x
                    ny = face.normal.y
                    nz = face.normal.z

                    for planar_face in mesh.tessfaces:
                        angle = face.normal.angle(planar_face.normal)
                        if (-.052 < angle and angle < .052):
                            nx += planar_face.normal.x
                            ny += planar_face.normal.y
                            nz += planar_face.normal.z
                            count += 1

                    float_normals.append(nx / count)
                    float_normals.append(ny / count)
                    float_normals.append(nz / count)
                else:
                    float_normals.extend(face.normal)

        id_ = "{!s}-normals".format(object_.name)
        source = utils.write_source(id_, "float", float_normals, "XYZ")
        root.appendChild(source)

    def __write_uvs(self, object_, mesh, root):
        uvdata = object_.data.tessface_uv_textures
        if uvdata is None:
            cbPrint("Your UV map is missing, adding...")
            bpy.ops.mesh.uv_texture_add()
        else:
            cbPrint("Found UV map.")

        float_uvs = []
        for uvindex, uvlayer in enumerate(uvdata):
            mapslot = uvindex
            mapname = uvlayer.name
            uvid = "{!s}-{!s}-{!s}".format(object_.name, mapname, mapslot)

            for uf in uvlayer.data:
                for uv in uf.uv:
                    float_uvs.extend(uv)

        id_ = "{!s}-UVMap-0".format(object_.name)
        source = utils.write_source(id_, "float", float_uvs, "ST")
        root.appendChild(source)

    def __write_vertex_colors(self, object_, mesh, root):
        float_colors = []
        alpha_found = False

        if object_.data.tessface_vertex_colors:
            color_layers = object_.data.tessface_vertex_colors
            for color_layer in color_layers:
                for fi, face in enumerate(color_layer.data):
                    colors = [face.color1[:], face.color2[:], face.color3[:]]
                    if len(mesh.tessfaces[fi].vertices) == 4:
                        colors.append(face.color4[:])

                    for color in colors:
                        if color_layer.name.lower() == "alpha":
                            alpha_found = True
                            alpha = (color[0] + color[1] + color[2])/3
                            float_colors.extend([1, 1, 1, alpha])
                        else:
                            float_colors.extend(color)

        if float_colors:
            id_ = "{!s}-colors".format(object_.name)
            params = ("RGBA" if alpha_found else "RGB")
            source = utils.write_source(id_, "float", float_colors, params)
            root.appendChild(source)

    def __write_vertices(self, object_, mesh, root):
        vertices = self.__doc.createElement("vertices")
        vertices.setAttribute("id", "%s-vertices" % (object_.name))
        input = utils.write_input(object_.name, None, "positions", "POSITION")
        vertices.appendChild(input)
        root.appendChild(vertices)

    def __write_polylist(self, object_, mesh, root):
        materials = mesh.materials[:]
        if materials:
            for matindex, material in enumerate(materials):
                vert_data = ""
                verts_per_poly = ""
                poly_count = normal = texcoord = 0

                for face in mesh.tessfaces:
                    if face.material_index == matindex:
                        verts_per_poly = join(verts_per_poly, len(face.vertices), " ")
                        poly_count += 1
                        for vert in face.vertices:
                            data = self.__write_vertex_data(mesh, face, vert, normal, texcoord)
                            vert_data = join(vert_data, data)
                            texcoord += 1
                    else:
                        texcoord += len(face.vertices)

                    if face.use_smooth:
                        normal += len(face.vertices)
                    else:
                        normal += 1

                polylist = self.__doc.createElement("polylist")
                polylist.setAttribute("material", material.name)
                polylist.setAttribute("count", str(poly_count))

                inputs = []
                inputs.append(utils.write_input(object_.name, 0, "vertices", "VERTEX"))
                inputs.append(utils.write_input(object_.name, 1, "normals", "NORMAL"))
                inputs.append(utils.write_input(object_.name, 2, "UVMap-0", "TEXCOORD"))
                if mesh.vertex_colors:
                    inputs.append(utils.write_input(object_.name, 3, "colors", "COLOR"))

                for input in inputs:
                    polylist.appendChild(input)

                vcount = self.__doc.createElement("vcount")
                vcount_text = self.__doc.createTextNode(verts_per_poly)
                vcount.appendChild(vcount_text)

                p = self.__doc.createElement("p")
                p_text = self.__doc.createTextNode(vert_data)
                p.appendChild(p_text)

                polylist.appendChild(vcount)
                polylist.appendChild(p)
                root.appendChild(polylist)

    def __write_vertex_data(self, mesh, face, vert, normal, texcoord):
        if face.use_smooth:
            normal = vert

        if mesh.vertex_colors:
            return "{:d} {:d} {:d} {:d} ".format(vert, normal, texcoord, texcoord)
        else:
            return "{:d} {:d} {:d} ".format(vert, normal, texcoord)

    def __export_library_controllers(self, parent_element):
        library_node = self.__doc.createElement("library_controllers")

        for object_ in utils.get_type("geometry"):
            if not "_boneGeometry" in object_.name:
                armature = utils.get_armature_for_object(object_)
                if armature is not None:
                    self.__process_bones(library_node,
                                         object_,
                                         armature)

        parent_element.appendChild(library_node)

    def __process_bones(self, parent_node, object_, armature):
        mesh = object_.data
        id_ = "{!s}_{!s}".format(armature.name, object_.name)

        controller_node = self.__doc.createElement("controller")
        parent_node.appendChild(controller_node)
        controller_node.setAttribute("id", id_)

        skin_node = self.__doc.createElement("skin")
        skin_node.setAttribute("source", "#%s" % object_.name)
        controller_node.appendChild(skin_node)

        bind_shape_matrix = self.__doc.createElement("bind_shape_matrix")
        utils.write_matrix(Matrix(), bind_shape_matrix)
        skin_node.appendChild(bind_shape_matrix)

        self.__process_bone_joints(object_, armature, skin_node)
        self.__process_bone_matrices(object_, armature, skin_node)
        self.__process_bone_weights(object_, armature, skin_node)

        joints = self.__doc.createElement("joints")
        input = utils.write_input(id_, None, "joints", "JOINT")
        joints.appendChild(input)
        input = utils.write_input(id_, None, "matrices", "INV_BIND_MATRIX")
        joints.appendChild(input)
        skin_node.appendChild(joints)

    def __process_bone_joints(self, object_, armature, skin_node):
        bones = utils.get_bones(armature)
        id_ = "{!s}_{!s}-joints".format(armature.name, object_.name)
        bone_names = [bone.name for bone in bones]
        source = utils.write_source(id_, "IDREF", bone_names, [])
        skin_node.appendChild(source)

    def __process_bone_matrices(self, object_, armature, skin_node):
        bones = utils.get_bones(armature)
        bone_matrices = []
        for bone in bones:
            fakebone = utils.find_fakebone(bone.name)
            if fakebone is None:
                return
            matrix_local = copy.deepcopy(fakebone.matrix_local)
            utils.negate_z_axis_of_matrix(matrix_local)
            bone_matrices.extend(utils.matrix_to_array(matrix_local))

        id_ = "{!s}_{!s}-matrices".format(armature.name, object_.name)
        source = utils.write_source(id_, "float4x4", bone_matrices, [])
        skin_node.appendChild(source)

    def __process_bone_weights(self, object_, armature, skin_node):
        bones = utils.get_bones(armature)
        group_weights = []
        vw = ""
        vertex_groups_lengths = ""
        vertex_count = 0

        for vertex in object_.data.vertices:
            for group in vertex.groups:
                group_weights.append(group.weight)
                for vertex_group in object_.vertex_groups:
                    if vertex_group.index == group.group:
                        for bone_id, bone in enumerate(bones):
                            if bone.name == vertex_group.name:
                                vw += "%s " % bone_id

                vw += "%s " % vertex_count
                vertex_count += 1

            vertex_groups_lengths += "%s " % len(vertex.groups)

        id_ = "{!s}_{!s}-weights".format(armature.name, object_.name)
        source = utils.write_source(id_, "float", group_weights, [])
        skin_node.appendChild(source)

        vertex_weights = self.__doc.createElement("vertex_weights")
        vertex_weights.setAttribute("count", str(len(object_.data.vertices)))

        id_ = "{!s}_{!s}".format(armature.name, object_.name)
        input = utils.write_input(id_, 0, "joints", "JOINT")
        vertex_weights.appendChild(input)
        input = utils.write_input(id_, 1, "weights", "WEIGHT")
        vertex_weights.appendChild(input)

        vcount = self.__doc.createElement("vcount")
        vcount_text = self.__doc.createTextNode(vertex_groups_lengths)
        vcount.appendChild(vcount_text)
        vertex_weights.appendChild(vcount)

        v = self.__doc.createElement("v")
        v_text = self.__doc.createTextNode(vw)
        v.appendChild(v_text)
        vertex_weights.appendChild(v)

        skin_node.appendChild(vertex_weights)

    def __export_library_animation_clips_and_animations(self, parent_element):
        libanmcl = self.__doc.createElement("library_animation_clips")
        libanm = self.__doc.createElement("library_animations")
        parent_element.appendChild(libanmcl)
        parent_element.appendChild(libanm)

        scene = bpy.context.scene
        for group in utils.get_export_nodes():
            node_type = utils.get_node_type(group.name)
            allowed = ["cga", "anm", "i_caf", "caf"]
            if node_type in allowed:
                animation_clip = self.__doc.createElement("animation_clip")
                node_name = utils.get_node_name(group.name)
                animation_clip.setAttribute("id",
                                            "{!s}-{!s}".format(node_name, node_name))
                animation_clip.setAttribute("start",
                                            "{:f}".format(utils.frame_to_time(scene.frame_start)))
                animation_clip.setAttribute("end",
                                            "{:f}".format(utils.frame_to_time(scene.frame_end)))
                is_animation = False
                for object_ in group.objects:
                    if (object_.type != 'ARMATURE' and object_.animation_data and
                            object_.animation_data.action):

                        is_animation = True
                        for axis in iter(AXES):
                            animation = self.__get_animation_location(object_, axis)
                            if animation is not None:
                                libanm.appendChild(animation)

                        for axis in iter(AXES):
                            animation = self.__get_animation_rotation(object_, axis)
                            if animation is not None:
                                libanm.appendChild(animation)

                        self.__export_instance_animation_parameters(object_,
                                                            animation_clip)

                if is_animation:
                    libanmcl.appendChild(animation_clip)

    def __export_instance_animation_parameters(self, object_, animation_clip):
        location_exists = rotation_exists = False
        for curve in object_.animation_data.action.fcurves:
            for axis in iter(AXES):
                if curve.array_index == AXES[axis]:
                    if curve.data_path == "location":
                        location_exists = True
                    if curve.data_path == "rotation_euler":
                        rotation_exists = True
                    if location_exists and rotation_exists:
                        break

        if location_exists:
            self.__export_instance_parameter(object_, animation_clip, "location")
        if rotation_exists:
            self.__export_instance_parameter(object_, animation_clip, "rotation_euler")

    def __export_instance_parameter(self, object_, animation_clip, parameter):
        for axis in iter(AXES):
            inst = self.__doc.createElement("instance_animation")
            inst.setAttribute("url",
                              "#{!s}_{!s}_{!s}".format(object_.name, parameter, axis))
            animation_clip.appendChild(inst)

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
        multiplier = utils.to_degrees
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
            if (curve.data_path == attribute_type and curve.array_index == AXES[axis]):
                keyframe_points = curve.keyframe_points
                sources = {
                    "input": [],
                    "output": [],
                    "interpolation": [],
                    "intangent": [],
                    "outangent": []
                }
                for keyframe_point in keyframe_points:
                    khlx = keyframe_point.handle_left[0]
                    khly = keyframe_point.handle_left[1]
                    khrx = keyframe_point.handle_right[0]
                    khry = keyframe_point.handle_right[1]
                    frame, value = keyframe_point.co

                    sources["input"].append(utils.frame_to_time(frame))
                    sources["output"].append(value * multiplier)
                    sources["interpolation"].append(keyframe_point.interpolation)
                    sources["intangent"].extend( [utils.frame_to_time(khlx), khly] )
                    sources["outangent"].extend( [utils.frame_to_time(khrx), khry] )

                animation_element = self.__doc.createElement("animation")
                animation_element.setAttribute("id", id_prefix)

                for type_, data in sources.items():
                    anim_node = self.__create_animation_node(type_, data, id_prefix)
                    animation_element.appendChild(anim_node)

                sampler = self.__create_sampler(id_prefix, source_prefix)
                channel = self.__doc.createElement("channel")
                channel.setAttribute("source", "{!s}-sampler".format(source_prefix))
                channel.setAttribute("target", target)

                animation_element.appendChild(sampler)
                animation_element.appendChild(channel)

                return animation_element

    def __create_animation_node(self, type_, data, id_prefix):
        id_ = "{!s}-{!s}".format(id_prefix, type_)
        type_map = {
            "input":            ["float", ["TIME"]],
            "output":           ["float", ["VALUE"]],
            "intangent":        ["float", "XY"],
            "outangent":        ["float", "XY"],
            "interpolation":    ["name",  ["INTERPOLATION"]]
        }

        source = utils.write_source(id_, type_map[type_][0], data, type_map[type_][1])

        return source

    def __create_sampler(self, id_prefix, source_prefix):
        sampler = self.__doc.createElement("sampler")
        sampler.setAttribute("id", "{!s}-sampler".format(id_prefix))

        input = self.__doc.createElement("input")
        input.setAttribute("semantic", "INPUT")
        input.setAttribute("source", "{!s}-input".format(source_prefix))
        output = self.__doc.createElement("input")
        output.setAttribute("semantic", "OUTPUT")
        output.setAttribute("source", "{!s}-output".format(source_prefix))
        interpolation = self.__doc.createElement("input")
        interpolation.setAttribute("semantic", "INTERPOLATION")
        interpolation.setAttribute("source", "{!s}-interpolation".format(source_prefix))
        intangent = self.__doc.createElement("input")
        intangent.setAttribute("semantic", "IN_TANGENT")
        intangent.setAttribute("source", "{!s}-intangent".format(source_prefix))
        outangent = self.__doc.createElement("input")
        outangent.setAttribute("semantic", "OUT_TANGENT")
        outangent.setAttribute("source", "{!s}-outangent".format(source_prefix))

        sampler.appendChild(input)
        sampler.appendChild(output)
        sampler.appendChild(interpolation)
        sampler.appendChild(intangent)
        sampler.appendChild(outangent)

        return sampler

    def __export_library_visual_scenes(self, parent_element):
        current_element = self.__doc.createElement("library_visual_scenes")
        visual_scene = self.__doc.createElement("visual_scene")
        visual_scene.setAttribute("id", "scene")
        visual_scene.setAttribute("name", "scene")
        current_element.appendChild(visual_scene)
        parent_element.appendChild(current_element)

        if utils.get_export_nodes():
            if utils.are_duplicate_nodes():
                message = "Duplicate Node Names"
                bpy.ops.screen.display_error('INVOKE_DEFAULT', message=message)

            for group in utils.get_export_nodes():
                self.__write_export_node(group, visual_scene)
        else:
            pass # TODO: Handle No Export Nodes Error

    def __write_export_node(self, group, visual_scene):
        nodename = "CryExportNode_{}".format(utils.get_node_name(group.name))
        node = self.__doc.createElement("node")
        node.setAttribute("id", nodename)
        node.setIdAttribute("id")

        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        self.__write_transforms(bpy.context.active_object, node)
        bpy.ops.object.delete(use_global=False)

        root_objects = []
        for object_ in group.objects:
            if object_.parent is None:
                root_objects.append(object_)
        node = self.__write_visual_scene_node(root_objects, node, node)

        extra = self.__create_cryengine_extra(group)
        node.appendChild(extra)
        visual_scene.appendChild(node)

    def __write_visual_scene_node(self, objects, nodeparent, root):
        for object_ in objects:
            if object_.type == "ARMATURE":
                self.__write_bone_list([utils.get_root_bone(object_)], object_, root, root)
                node = root
            elif not utils.is_fakebone(object_):
                node = self.__doc.createElement("node")
                node.setAttribute("id", object_.name)
                node.setIdAttribute("id")

                self.__write_transforms(object_, node)

                instance = self.__create_instance(object_)
                if instance is not None:
                    node.appendChild(instance)

                extra = self.__create_cryengine_extra(object_)
                if extra is not None:
                    node.appendChild(extra)

                nodeparent.appendChild(node)

            if object_.children:
                object_children = utils.get_object_children(object_)
                self.__write_visual_scene_node(object_children, node, root)

        return root

    def __write_bone_list(self, bones, object_, nodeparent, root):
        scene = bpy.context.scene
        bonenames = []

        for bone in bones:
            props = self.__create_ik_properties(bone, object_, root)
            nodename = join(bone.name, props)
            bonenames.append(nodename)

            node = self.__doc.createElement("node")
            node.setAttribute("id", nodename)
            node.setAttribute("name", nodename)
            node.setIdAttribute("id")

            fakebone = utils.find_fakebone(bone.name)
            if fakebone is not None:
                self.__write_transforms(fakebone, node)

            bone_geometry = utils.find_bone_geometry(bone.name)
            if bone_geometry is not None:
                instance = self.__create_instance(object_)
                node.appendChild(instance)

            nodeparent.appendChild(node)

            if object_.children:
                self.__write_bone_list(bone.children, object_, node, root)

    def __write_transforms(self, object_, node):
        trans = self.__create_translation_node(object_)
        rotx, roty, rotz = self.__create_rotation_node(object_)
        scale = self.__create_scale_node(object_)

        node.appendChild(trans)
        node.appendChild(rotx)
        node.appendChild(roty)
        node.appendChild(rotz)
        node.appendChild(scale)

    def __create_translation_node(self, object_):
        trans = self.__doc.createElement("translate")
        trans.setAttribute("sid", "translation")
        trans_text = self.__doc.createTextNode("{:f} {:f} {:f}".format(
                                                    * object_.location))
        trans.appendChild(trans_text)

        return trans

    def __create_rotation_node(self, object_):
        rotx = self.__write_rotation("X", "1 0 0 {:f}", object_.rotation_euler[0])
        roty = self.__write_rotation("Y", "0 1 0 {:f}", object_.rotation_euler[1])
        rotz = self.__write_rotation("Z", "0 0 1 {:f}", object_.rotation_euler[2])

        return rotx, roty, rotz

    def __write_rotation(self, axis, textFormat, rotation):
        rot = self.__doc.createElement("rotate")
        rot.setAttribute("sid", "rotation_{}".format(axis))
        rot_text = self.__doc.createTextNode(textFormat.format(
                                                rotation * utils.to_degrees))
        rot.appendChild(rot_text)

        return rot

    def __create_scale_node(self, object_):
        scale = self.__doc.createElement("scale")
        scale.setAttribute("sid", "scale")
        scale_text = self.__doc.createTextNode(
                    utils.floats_to_string(object_.scale, " ", "%s"))
        scale.appendChild(scale_text)

        return scale

    def __create_instance(self, object_):
        armature = utils.get_armature_for_object(object_)
        instance = None
        if armature is not None:
            instance = self.__doc.createElement("instance_controller")
            # This binds the mesh object to the armature in control of it
            instance.setAttribute("url", "#{!s}_{!s}".format(
                                        armature.name,
                                        object_.name))
        elif object_.name[:6] != "_joint" and object_.type == "MESH":
            instance = self.__doc.createElement("instance_geometry")
            instance.setAttribute("url", "#{!s}".format(object_.name))

        if instance is not None:
            bind_material = self.__create_bind_material(object_)
            instance.appendChild(bind_material)
            return instance

    def __create_bind_material(self, object_):
        bind_material = self.__doc.createElement("bind_material")
        technique_common = self.__doc.createElement("technique_common")

        for material in object_.material_slots:
            instance_material = self.__doc.createElement(
                                "instance_material")
            instance_material.setAttribute("symbol", material.name)
            instance_material.setAttribute("target", "#{!s}".format(
                                material.name))

            bind_vertex_input = self.__doc.createElement(
                                "bind_vertex_input")
            bind_vertex_input.setAttribute("semantic", "UVMap")
            bind_vertex_input.setAttribute("input_semantic", "TEXCOORD")
            bind_vertex_input.setAttribute("input_set", "0")

            instance_material.appendChild(bind_vertex_input)
            technique_common.appendChild(instance_material)

        bind_material.appendChild(technique_common)

        return bind_material
        
    def __create_cryengine_extra(self, node):
        extra = self.__doc.createElement("extra")
        technique = self.__doc.createElement("technique")
        technique.setAttribute("profile", "CryEngine")
        # Tag properties onto the end of the item.
        properties = self.__doc.createElement("properties")
        if utils.is_export_node(node.name):
            node_type = utils.get_node_type(node.name)
            allowed = {"cgf", "cga", "chr", "skin", "anm", "i_caf", "caf"}
            if node_type in allowed:
                prop = self.__doc.createTextNode("fileType={}".format(node_type))
                properties.appendChild(prop)
            if self.__config.donot_merge:
                prop = self.__doc.createTextNode("DoNotMerge")
                properties.appendChild(prop)
        else:
            if not node.rna_type.id_data.items():
                return
        for prop in node.rna_type.id_data.items():
            if prop:
                user_defined_property = self.__doc.createTextNode("{!s}".format(prop[1]))
                properties.appendChild(user_defined_property)
        technique.appendChild(properties)

        if (node.name[:6] == "_joint"):
            helper = self.__create_helper_joint(node)
            technique.appendChild(helper)

        extra.appendChild(technique)

        return extra

    def __create_helper_joint(self, object_):
        x1, y1, z1, x2, y2, z2 = utils.get_bounding_box(object_)

        min = self.__doc.createElement("bound_box_min")
        min_text = self.__doc.createTextNode("{:f} {:f} {:f}".format(x1, y1, z1))
        min.appendChild(min_text)

        max = self.__doc.createElement("bound_box_max")
        max_text = self.__doc.createTextNode("{:f} {:f} {:f}".format(x2, y2, z2))
        max.appendChild(max_text)

        joint = self.__doc.createElement("helper")
        joint.setAttribute("type", "dummy")
        joint.appendChild(min)
        joint.appendChild(max)

        return joint

    def __create_ik_properties(self, bone, object_, export_node):
        props = ""
        if self.__config.include_ik and bone.name.endswith("_Phys"):
            nodename = root.getAttribute('id')[14:]
            props_name = bone.name.replace("_", "*")

            armature_object = bpy.data.objects[object_.name[:-5]]
            pose_bone = armature_object.pose.bones[bone.name[:-5]]

            props = join(
                        '%{!s}%'.format(nodename),
                        '--PRprops_name={!s}_'.format(props_name),

                        'xmax={!s}_'.format(pose_bone.ik_max_x),
                        'xmin={!s}_'.format(pose_bone.ik_min_x),
                        'xdamping={!s}_'.format(pose_bone.ik_stiffness_x),
                        'xspringangle={!s}_'.format(0.0),
                        'xspringtension={!s}_'.format(1.0),

                        'ymax={!s}_'.format(pose_bone.ik_max_y),
                        'ymin={!s}_'.format(pose_bone.ik_min_y),
                        'ydamping={!s}_'.format(pose_bone.ik_stiffness_y),
                        'yspringangle={!s}_'.format(0.0),
                        'yspringtension={!s}_'.format(1.0),

                        'zmax={!s}_'.format(pose_bone.ik_max_z),
                        'zmin={!s}_'.format(pose_bone.ik_min_z),
                        'zdamping={!s}_'.format(pose_bone.ik_stiffness_z),
                        'zspringangle={!s}_'.format(0.0),
                        'zspringtension={!s}_'.format(1.0)
                    )

        return props

    def __export_scene(self, parent_element):
        scene = self.__doc.createElement("scene")
        instance_visual_scene = self.__doc.createElement("instance_visual_scene")
        instance_visual_scene.setAttribute("url", "#scene")
        scene.appendChild(instance_visual_scene)
        parent_element.appendChild(scene)


def write_scripts(config):
    filepath = bpy.path.ensure_ext(config.filepath, ".dae")
    if not config.make_chrparams and not config.make_cdf:
        return

    dae_path = utils.get_absolute_path_for_rc(filepath)
    output_path =  os.path.dirname(dae_path)
    chr_names = []
    for group in utils.get_export_nodes():
        if utils.get_node_type(group.name) == "chr":
            chr_names.append(utils.get_node_name(group.name))

    for chr_name in chr_names:
        if config.make_chrparams:
            filepath = "{}/{}.chrparams".format(output_path, chr_name)
            contents = utils.generate_file_contents("chrparams")
            utils.generate_xml(filepath, contents)
        if config.make_cdf:
            filepath = "{}/{}.cdf".format(output_path, chr_name)
            contents = utils.generate_file_contents("cdf")
            utils.generate_xml(filepath, contents)


def save(config):
    # prevent wasting time for exporting if RC was not found
    if not os.path.isfile(config.rc_path):
        raise exceptions.NoRcSelectedException

    exporter = CrytekDaeExporter(config)
    exporter.export()


def register():
    bpy.utils.register_class(CrytekDaeExporter)
    bpy.utils.register_class(TriangulateMeError)
    bpy.utils.register_class(Error)


def unregister():
    bpy.utils.unregister_class(CrytekDaeExporter)
    bpy.utils.unregister_class(TriangulateMeError)
    bpy.utils.unregister_class(Error)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mesh.crytekdae('INVOKE_DEFAULT')
