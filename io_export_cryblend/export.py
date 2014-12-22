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

from io_export_cryblend.dds_converter import DdsConverterRunner
from io_export_cryblend.outPipe import cbPrint
from io_export_cryblend.utils import join

from bpy_extras.io_utils import ExportHelper
from datetime import datetime
from mathutils import Matrix, Vector
from time import clock
from xml.dom.minidom import Document
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
        # Ensure the correct extension for chosen path
        filepath = bpy.path.ensure_ext(self.__config.filepath, ".dae")

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

        write_to_file(self.__config,
                      self.__doc, filepath,
                      self.__config.rc_path)

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
        textures = utils.get_textures_in_export_nodes()

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
        converter = DdsConverterRunner(
                                self.__config.rc_for_textures_conversion_path)
        converter.start_conversion(images_to_convert,
                                   self.__config.refresh_rc,
                                   self.__config.save_tiff_during_conversion)

    def __export_library_effects(self, parent_element):
        current_element = self.__doc.createElement("library_effects")
        parent_element.appendChild(current_element)

        for material in utils.get_materials_in_export_nodes():
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

    def __create_color_node(self, material, type):
        node = self.__doc.createElement(type)
        color = self.__doc.createElement("color")
        color.setAttribute("sid", type)
        col = utils.get_material_color(material, type)
        color_text = self.__doc.createTextNode(col)
        color.appendChild(color_text)
        node.appendChild(color)

        return node

    def __create_texture_node(self, image_name, type):
        node = self.__doc.createElement(type)
        texture = self.__doc.createElement("texture")
        texture.setAttribute("texture", "%s-sampler" % image_name)
        node.appendChild(texture)

        return node

    def __create_attribute_node(self, material, type):
        node = self.__doc.createElement(type)
        float = self.__doc.createElement("float")
        float.setAttribute("sid", type)
        val = utils.get_material_attribute(material, type)
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
        materials = utils.get_materials_in_export_nodes()

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

        for object_ in utils.get_objects_in_export_nodes():
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
        for vertex in mesh.vertices[:]:
            float_positions.extend(vertex.co)

        id = "{!s}-positions".format(object_.name)
        source = utils.write_source(id,
                                    "float",
                                    float_positions,
                                    "XYZ",
                                    self.__doc)
        root.appendChild(source)

    def __write_normals(self, object_, mesh, root):
        float_normals = []
        float_normals_count = ""

        for face in mesh.tessfaces:
            if face.use_smooth:
                for vert in face.vertices:
                    vertex = mesh.vertices[vert]
                    normal = utils.veckey3d21(vertex.normal)
                    float_normals.extend(normal)

            else:
                if self.__config.avg_pface:
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
                    normal = utils.veckey3d21(face.normal)
                    float_normals.extend(normal)

        id = "{!s}-normals".format(object_.name)
        source = utils.write_source(id,
                                    "float",
                                    float_normals,
                                    "XYZ",
                                    self.__doc)
        root.appendChild(source)

    def __write_uvs(self, object_, mesh, root):
        uvdata = object_.data.tessface_uv_textures
        if uvdata is not None:
            cbPrint("Found UV map.")
        else:
            bpy.ops.mesh.uv_texture_add()
            cbPrint("Your UV map is missing, adding.")

        float_uvs = []
        for uvindex, uvlayer in enumerate(uvdata):
            mapslot = uvindex
            mapname = uvlayer.name
            uvid = "{!s}-{!s}-{!s}".format(object_.name, mapname, mapslot)

            for uf in uvlayer.data:
                for uv in uf.uv:
                    float_uvs.extend(uv)

        id = "{!s}-UVMap-0".format(object_.name)
        source = utils.write_source(id,
                                    "float",
                                    float_uvs,
                                    "ST",
                                    self.__doc)
        root.appendChild(source)

    def __write_vertex_colors(self, object_, mesh, root):
        # from fbx exporter
        # list for vert alpha if found
        alpha_found = 0
        alpha_list = []
        float_colors = []

        if object_.data.tessface_vertex_colors:
            collayers = object_.data.tessface_vertex_colors
            # TODO merge these two for loops
            for collayer in collayers:
                i = -1
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
                        for color in colors:
                            tmp = [fi, color[0]]

                        alpha_list.append(tmp)

                    for vca in alpha_list:
                        cbPrint(str(vca))

            for collayer in collayers:
                i = -1
                colname = str(collayer.name)
                for fi, cf in enumerate(collayer.data):
                    colors = [cf.color1[:], cf.color2[:], cf.color3[:]]
                    if len(mesh.tessfaces[fi].vertices) == 4:
                        colors.append(cf.color4[:])

                    for color in colors:
                        if i == -1:
                            if alpha_found == 1:
                                tmp = alpha_list[fi]
                                float_colors.extend(color)
                                float_colors.append(tmp[1])
                                cbPrint(color[0])
                            else:
                                float_colors.extend(color)
                            i = 0
                        else:
                            if i == 7:
                                i = 0
                            if alpha_found == 1:
                                tmp = alpha_list[fi]
                                float_colors.extend(color)
                                float_colors.append(tmp[1])
                                cbPrint(color[0])
                            else:
                                float_colors.extend(color)
                        i += 1

        if float_colors:
            id = "{!s}-colors".format(object_.name)
            if alpha_found:
                source = utils.write_source(id,
                                            "float",
                                            float_colors,
                                            "RGBA",
                                            self.__doc)
            else:
                source = utils.write_source(id,
                                            "float",
                                            float_colors,
                                            "RGB",
                                            self.__doc)
            root.appendChild(source)

    def __write_vertices(self, object_, mesh, root):
        vertices = self.__doc.createElement("vertices")
        vertices.setAttribute("id", "%s-vertices" % (object_.name))
        input = utils.write_input(object_.name, None,
                                    "positions", "POSITION")
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
                inputs.append(utils.write_input(object_.name, 0,
                                            "vertices", "VERTEX"))
                inputs.append(utils.write_input(object_.name, 1,
                                            "normals", "NORMAL"))
                inputs.append(utils.write_input(object_.name, 2,
                                            "UVMap-0", "TEXCOORD"))
                if mesh.vertex_colors:
                    inputs.append(utils.write_input(object_.name, 3,
                                                    "colors", "COLOR"))

                for input in inputs:
                    polylist.appendChild(input)

                vcount = self.__doc.createElement("vcount")
                vcount_text_node = self.__doc.createTextNode(verts_per_poly)
                vcount.appendChild(vcount_text_node)

                p = self.__doc.createElement("p")
                p_text_node = self.__doc.createTextNode(vert_data)
                p.appendChild(p_text_node)

                polylist.appendChild(vcount)
                polylist.appendChild(p)
                root.appendChild(polylist)

    def __write_vertex_data(self, mesh, face, vert, normal, texcoord):
        if face.use_smooth:
            normal = vert

        if mesh.vertex_colors:
            return "{:d} {:d} {:d} {:d} ".format(vert, normal, texcoord, texcoord)
        else :
            return "{:d} {:d} {:d} ".format(vert, normal, texcoord)

    def __export_library_controllers(self, parent_element):
        library_node = self.__doc.createElement("library_controllers")

        for selected_object in utils.get_objects_in_export_nodes():
            if not "_boneGeometry" in selected_object.name:
                armatures = utils.get_armature_modifiers(selected_object)

                if armatures:
                    self.__process_bones(library_node,
                                         selected_object,
                                         armatures)

        parent_element.appendChild(library_node)

    def __process_bones(self, parent_node, object_, armatures):
        mesh = object_.data
        armature = armatures[0].object
        id = "{!s}-{!s}".format(armature.name, object_.name)

        controller_node = self.__doc.createElement("controller")
        parent_node.appendChild(controller_node)

        controller_node.setAttribute("id", id)
        skin_node = self.__doc.createElement("skin")
        skin_node.setAttribute("source", "#%s" % object_.name)
        controller_node.appendChild(skin_node)

        bind_shape_matrix = self.__doc.createElement("bind_shape_matrix")
        utils.write_matrix(Matrix(), bind_shape_matrix)
        skin_node.appendChild(bind_shape_matrix)

        armature_bones = utils.get_bones(armature)

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

        joints = self.__doc.createElement("joints")

        input = utils.write_input(id, None, "joints", "JOINT")
        joints.appendChild(input)
        input = utils.write_input(id, None, "matrices", "INV_BIND_MATRIX")
        joints.appendChild(input)
        skin_node.appendChild(joints)

        vertex_weights = self.__doc.createElement("vertex_weights")
        vertex_weights.setAttribute("count", str(len(mesh.vertices)))

        input = utils.write_input(id, 0, "joints", "JOINT")
        vertex_weights.appendChild(input)
        input = utils.write_input(id, 1, "weights", "WEIGHT")
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

    def __process_bones_joints(self,
                               object_name,
                               skin_node,
                               armature_name,
                               armature_bones):
        id = "{!s}-{!s}-joints".format(armature_name, object_name)
        bone_names = [bone.name for bone in armature_bones]
        source = utils.write_source(id,
                                    "IDREF",
                                    bone_names,
                                    ["IDREF"],
                                    self.__doc)
        skin_node.appendChild(source)

    def __process_bones_matrices(self,
                                 object_name,
                                 skin_node,
                                 armature_name,
                                 armature_bones):
        
        source_matrices_node = self.__doc.createElement("source")
        source_matrices_node.setAttribute("id", "%s-%s-matrices"
                                          % (armature_name, object_name))

        skin_node.appendChild(source_matrices_node)

        float_array_node = self.__doc.createElement("float_array")
        float_array_node.setAttribute("id", "%s-%s-matrices-array"
                                      % (armature_name, object_name))
        float_array_node.setAttribute("count", "%s"
                                      % (len(armature_bones) * 16))
        self.__export_float_array(armature_bones, float_array_node)
        source_matrices_node.appendChild(float_array_node)

        technique_node = self.__doc.createElement("technique_common")
        accessor_node = self.__doc.createElement("accessor")
        accessor_node.setAttribute("source", "#%s-%s-matrices-array"
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
        source_node.setAttribute("id", "%s-%s-weights"
                                         % (armature_name, object_.name))

        skin_node.appendChild(source_node)

        float_array = self.__doc.createElement("float_array")
        float_array.setAttribute("id", "%s-%s-weights-array"
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
        accessor_node.setAttribute("source", "#%s-%s-weights-array"
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

    def __export_float_array(self, armature_bones, float_array):
        for bone in armature_bones:
            fakebone = utils.find_fakebone(bone.name)
            if fakebone is None:
                return

            matrix_local = copy.deepcopy(fakebone.matrix_local)
            utils.negate_z_axis_of_matrix(matrix_local)

            utils.write_matrix(matrix_local, float_array)

    def __export_library_animation_clips_and_animations(self, parent_element):
        libanmcl = self.__doc.createElement("library_animation_clips")
        libanm = self.__doc.createElement("library_animations")
        parent_element.appendChild(libanmcl)
        parent_element.appendChild(libanm)

        scene = bpy.context.scene
        for group in bpy.data.groups:
            if utils.is_export_node(group.name):
                type = utils.get_node_type(group.name)
                if type == "cga" or type == "chr":
                    node_name = group.name[14:]
                    animation_clip = self.__doc.createElement("animation_clip")
                    animation_clip.setAttribute("id",
                                                "%s-%s" % (scene.name, node_name))
                    animation_clip.setAttribute("start",
                                                "%s" % (utils.convert_time(scene.frame_start)))
                    animation_clip.setAttribute("end",
                                                "%s" % (utils.convert_time(scene.frame_end)))
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

    def __export__animation_clip(self, object_, ename, act_name,
                                 start_frame, end_frame):
        animation_clip = self.__doc.createElement("animation_clip")
        animation_clip.setAttribute("id", "{!s}-{!s}".format(act_name, ename[14:]))
        # RC does not seem to like doubles and truncates them to integers
        animation_clip.setAttribute("start",
                                    "{:f}".format(utils.convert_time(start_frame)))
        animation_clip.setAttribute("end",
                                    "{:f}".format(utils.convert_time(end_frame)))
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
            if (curve.data_path == attribute_type and curve.array_index == AXES[axis]):
                keyframe_points = curve.keyframe_points
                sources = {
                    "input": "",
                    "output": "",
                    "interpolation": "",
                    "intangent": "",
                    "outangent": ""
                }
                for keyframe_point in keyframe_points:
                    khlx = keyframe_point.handle_left[0]
                    khly = keyframe_point.handle_left[1]
                    khrx = keyframe_point.handle_right[0]
                    khry = keyframe_point.handle_right[1]
                    frame, value = keyframe_point.co

                    sources["input"] = join(sources["input"], "{:f} ".format(utils.convert_time(frame)))
                    sources["output"] = join(sources["output"], "{:f} ".format(value * multiplier))
                    sources["interpolation"] = join(sources["interpolation"], "{:f} ".format(keyframe_point.interpolation))
                    sources["intangent"] = join(sources["intangent"], "{:f}{:f} ".format(utils.convert_time(khlx), khly))
                    sources["outangent"] = join(sources["outangent"], "{:f}{:f} ".format(utils.convert_time(khrx), khry))

                animation_element = self.__doc.createElement("animation")
                animation_element.setAttribute("id", id_prefix)

                for type, data in sources.items():
                    animation_node = self.__create_animation_node(type, data, len(keyframe_points), id_prefix, source_prefix)
                    animation_element.appendChild(animation_node)

                sampler = self.__create_sampler(id_prefix, source_prefix)
                channel = self.__doc.createElement("channel")
                channel.setAttribute("source", "{!s}-sampler".format(source_prefix))
                channel.setAttribute("target", target)

                animation_element.appendChild(sampler)
                animation_element.appendChild(channel)

                return animation_element

    def __create_animation_node(self,
                                type,
                                item,
                                num_keyframes,
                                id_prefix,
                                source_prefix):
        if type == "intang" or type == "outang":
            axes = 2
        else:
            axes = 1
        source = self.__doc.createElement("source")
        source.setAttribute("id", "{!s}-{!s}".format(id_prefix, type))
        float_array = self.__doc.createElement("float_array")
        float_array.setAttribute("id", "{!s}-{!s}-array".format(id_prefix, type))
        float_array.setAttribute("count", "{!r}".format(num_keyframes * axes))
        source_text_node = self.__doc.createTextNode("{0}".format(item))
        float_array.appendChild(source_text_node)
        technique_common = self.__doc.createElement("technique_common")
        accessor = self.__doc.createElement("accessor")
        accessor.setAttribute("source", "{!s}-{!s}-array".format(source_prefix, type))
        accessor.setAttribute("count", "{!r}".format(num_keyframes))
        accessor.setAttribute("stride", "1")
        if axes == 2:
            param_x = self.__doc.createElement("param")
            param_x.setAttribute("name", "X")
            param_x.setAttribute("type", "float")
            param_y = self.__doc.createElement("param")
            param_y.setAttribute("name", "Y")
            param_y.setAttribute("type", "float")
            accessor.appendChild(param_x)
            accessor.appendChild(param_y)
        else:
            param = self.__doc.createElement("param")
            param.setAttribute("name", "TIME")
            param.setAttribute("type", "float")
            accessor.appendChild(param)
        technique_common.appendChild(accessor)
        source.appendChild(float_array)
        source.appendChild(technique_common)

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
        outangent.setAttribute("source", "{!s}-outtangent".format(source_prefix))

        sampler.appendChild(input)
        sampler.appendChild(output)
        sampler.appendChild(interpolation)
        sampler.appendChild(intangent)
        sampler.appendChild(outangent)

        return sampler

    def __export_library_visual_scenes(self, parent_element):
        current_element = self.__doc.createElement("library_visual_scenes")
        visual_scene = self.__doc.createElement("visual_scene")
        current_element.appendChild(visual_scene)
        parent_element.appendChild(current_element)

        # doesn't matter what name we have here as long as it is
        # the same for <scene>
        visual_scene.setAttribute("id", "scene")
        visual_scene.setAttribute("name", "scene")
        for group in bpy.context.blend_data.groups:
            if group:
                if (utils.is_export_node(group.name)):
                    self.__write_visual_scene(group, visual_scene)

    def __write_visual_scene(self, group, visual_scene):
        ename = str(group.id_data.name)
        node = self.__doc.createElement("node")
        node.setAttribute("id", utils.get_node_name(ename))
        node.setIdAttribute("id")
        visual_scene.appendChild(node)
        node = self.__write_visual_scene_node(group.objects, node)
        # export node settings
        extra = self.__doc.createElement("extra")
        technique = self.__doc.createElement("technique")
        technique.setAttribute("profile", "CryEngine")
        node_type = utils.get_node_type(ename)
        props = self.__doc.createElement("properties")
        if node_type == "cgf":
            type = self.__doc.createTextNode("fileType=cgf")
            props.appendChild(type)
        elif node_type == "cga":
            type = self.__doc.createTextNode("fileType=cga")
            props.appendChild(type)
        elif node_type == "chr":
            type = self.__doc.createTextNode("fileType=chrcaf")
            props.appendChild(type)
        elif node_type == "skin":
            type = self.__doc.createTextNode("fileType=skin")
            props.appendChild(type)
        else:
            cbPrint("Unable to recognize node type.")
        if self.__config.donot_merge:
            do_not_merge = self.__doc.createTextNode("DoNotMerge")
            props.appendChild(do_not_merge)
        technique.appendChild(props)
        extra.appendChild(technique)
        node.appendChild(extra)

    def __write_visual_scene_node(self, objects, root):
        for object_ in objects:
            node = self.__doc.createElement("node")
            node.setAttribute("id", object_.name)
            node.setIdAttribute("id")

            self.__write_transforms(object_, node)

            instance = self.__create_instance(object_)
            if instance is not None:
                node.appendChild(instance)

            extra = self.__create_cryengine_extra(object_)
            node.appendChild(extra)

            self.__write_next_visual_scene_node(object_, node, root)

        return root

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
        trans.setAttribute("sid", "trans")
        try:
            translation_text_node = self.__doc.createTextNode("{:f} {:f} {:f}".format(
                                            * object_.location))
        except:
            translation_text_node = self.__doc.createTextNode("{:f} {:f} {:f}".format(
                                            * object_.head))
        trans.appendChild(translation_text_node)

        return trans

    def __create_rotation_node(self, object_):
        rotx = self.__doc.createElement("rotate")
        rotx.setAttribute("sid", "rotation_X")
        try:
            rotx_text_node = self.__doc.createTextNode("1 0 0 {:f}".format(
                                        object_.rotation_euler[0]
                                            * utils.toDegrees))
        except:
            rotx_text_node = self.__doc.createTextNode("1 0 0 0")

        roty = self.__doc.createElement("rotate")
        roty.setAttribute("sid", "rotation_Y")
        try:
            roty_text_node = self.__doc.createTextNode("0 1 0 {:f}".format(
                                        object_.rotation_euler[1]
                                            * utils.toDegrees))
        except:
            roty_text_node = self.__doc.createTextNode("0 1 0 0")

        rotz = self.__doc.createElement("rotate")
        rotz.setAttribute("sid", "rotation_Z")
        try:
            rotz_text_node = self.__doc.createTextNode("0 0 1 {:f}".format(
                                        object_.rotation_euler[2]
                                            * utils.toDegrees))
        except:
            rotz_text_node = self.__doc.createTextNode("0 0 1 0")

        rotx.appendChild(rotx_text_node)
        roty.appendChild(roty_text_node)
        rotz.appendChild(rotz_text_node)

        return rotx, roty, rotz

    def __create_scale_node(self, object_):
        scale = self.__doc.createElement("scale")
        scale.setAttribute("sid", "scale")
        try:
            scale_text_node = self.__doc.createTextNode(
                        utils.floats_to_string(object_.scale, " ", "%s"))
        except:
            scale_text_node = self.__doc.createTextNode(
                        utils.floats_to_string((1, 1, 1), " ", "%s")) 
        scale.appendChild(scale_text_node)

        return scale

    def __create_instance(self, object_):
        armature_list = utils.get_armature_modifiers(object_)
        instance = None
        if armature_list:
            instance = self.__doc.createElement("instance_controller")
            # This binds the mesh object to the armature in control of it
            instance.setAttribute("url", "#{!s}-{!s}".format(
                            armature_list[0].object.name,
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
        
    def __create_cryengine_extra(self, object_):
        extra = self.__doc.createElement("extra")
        technique = self.__doc.createElement("technique")
        technique.setAttribute("profile", "CryEngine")
        # Tag properties onto the end of the item.
        properties = self.__doc.createElement("properties")
        for prop in object_.rna_type.id_data.items():
            if prop:
                user_defined_property = self.__doc.createTextNode("{!s}".format(prop[1]))
                properties.appendChild(user_defined_property)
        technique.appendChild(properties)

        if (object_.name[:6] == "_joint"):
            helper = self.__create_helper_joint(object_)
            technique.appendChild(helper)

        extra.appendChild(technique)

        return extra

    def __create_helper_joint(self, object_):
        x1, y1, z1, x2, y2, z2 = utils.get_bounding_box(object_)

        min = self.__doc.createElement("bound_box_min")
        min_text_node = self.__doc.createTextNode("{:f} {:f} {:f}".format(x1, y1, z1))
        min.appendChild(min_text_node)

        max = self.__doc.createElement("bound_box_max")
        max_text_node = self.__doc.createTextNode("{:f} {:f} {:f}".format(x2, y2, z2))
        max.appendChild(max_text_node)

        bounding_box = self.__doc.createElement("helper")
        bounding_box.setAttribute("type", "dummy")
        bounding_box.appendChild(min)
        bounding_box.appendChild(max)

        return bounding_box

    def __write_next_visual_scene_node(self, object_, node, root):
        if object_.type == 'ARMATURE':
            cbPrint("Armature appended.")
            bonelist = utils.get_bones(object_)
            self.__write_bone_list(bonelist, object_, root)

        if utils.is_fakebone(object_):
            return
        if object_.parent:
            if object_.parent.type != 'ARMATURE':
                nodeparent = self.__doc.getElementById(object_.parent.name)
                cbPrint(nodeparent)
                if nodeparent:
                    cbPrint("Appending object_ to parent.")
                    cbPrint(node)
                    already_exists = self.__doc.getElementById(object_.name)
                    if already_exists:
                        cbPrint("Object already appended to parent.")
                    else:
                        nodeparent.appendChild(node)
                object_children = utils.get_object_children(object_)
                self.__write_visual_scene_node(object_children, root)

            elif not object_.children:
                root.appendChild(node)
        else:
            if object_.children:
                if object_.type != "ARMATURE":
                    root.appendChild(node)
                    object_children = utils.get_object_children(object_)
                    self.__write_visual_scene_node(object_children, root)

            else:
                root.appendChild(node)

    def __write_bone_list(self, bones, object_, root):
        scene = bpy.context.scene
        boneExtendedNames = []
        for bone in bones:
            if bone.parent:
                cbPrint("Bone {!s} has parent {!s}".format(bone.name,
                                                            bone.parent.name))

            node = self.__doc.createElement("node")

            props = self.__create_ik_properties(bone, object_)

            name = join(bone.name, props)
            node.setAttribute("id", name)
            node.setAttribute("name", name)
            boneExtendedNames.append(name)
            node.setIdAttribute("id")

            fakebone = utils.find_fakebone(bone.name)
            if fakebone is not None:
                self.__write_transforms(fakebone, node)

            # Find the boneGeometry object
            for object_ in scene.objects:
                if object_.name == "{!s}{!s}".format(bone.name, "_boneGeometry"):
                    instance = self.__create_instance(object_)
                    node.appendChild(instance)

            if bone.parent:
                for name in boneExtendedNames:
                    if name == bone.parent.name:
                        nodeparent = self.__doc.getElementById(name)
                        if (nodeparent is not None):
                            nodeparent.appendChild(node)
                        cbPrint(bone.parent.name)
            else:
                root.appendChild(node)

    def __create_ik_properties(self, bone, object_):
        props = ""

        if (self.__config.include_ik and "_Phys" == bone.name[-5:]):
            exportNodeName = root.getAttribute('id')[14:]
            starredBoneName = bone.name.replace("_", "*")
            props = join(props, '%{!s}%'.format(exportNodeName))
            props = join(props, '--PRprops_name={!s}_'.format(starredBoneName))

            pose_bone = (bpy.data.objects[object_.name[:-5]]
                ).pose.bones[bone.name[:-5]]

            props = join(props, 'xmax={!s}_'.format(pose_bone.ik_max_x))
            props = join(props, 'xmin={!s}_'.format(pose_bone.ik_min_x))
            props = join(props, 'xdamping={!s}_'.format(
                                            pose_bone.ik_stiffness_x))
            props = join(props, 'xspringangle={!s}_'.format(0.0))
            props = join(props, 'xspringtension={!s}_'.format(1.0))

            props = join(props, 'ymax={!s}_'.format(pose_bone.ik_max_y))
            props = join(props, 'ymin={!s}_'.format(pose_bone.ik_min_y))
            props = join(props, 'ydamping={!s}_'.format(
                                            pose_bone.ik_stiffness_y))
            props = join(props, 'yspringangle={!s}_'.format(0.0))
            props = join(props, 'yspringtension={!s}_'.format(1.0))

            props = join(props, 'zmax={!s}_'.format(pose_bone.ik_max_z))
            props = join(props, 'zmin={!s}_'.format(pose_bone.ik_min_z))
            props = join(props, 'zdamping={!s}_'.format(
                                            pose_bone.ik_stiffness_z))
            props = join(props, 'zspringangle={!s}_'.format(0.0))
            props = join(props, 'zspringtension={!s}_'.format(1.0))

        return props

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
    rc_params = ["/verbose", "/threads=processors"]
    rc_params.append("/refresh")

    if config.run_rc or config.do_materials:
        if config.do_materials:
            rc_params.append("/createmtl=1")

        rc_process = utils.run_rc(exe, dae_file_for_rc, rc_params)

        if rc_process is not None:
            rc_process.wait()
            components = dae_file_for_rc.split("\\")
            name = components[len(components)-1]
            cbPrint(name)
            output_path = dae_file_for_rc[:-len(name)]
            for group in bpy.data.groups:
                if utils.is_export_node(group.name):
                    node_type = utils.get_node_type(group.name)
                    out_file = "{0}{1}".format(output_path,
                                                group.name[14:])
                    args = [exe, "/refresh", out_file]
                    rc_second_pass = subprocess.Popen(args)

        if config.do_materials:
            mtl_fix_thread = threading.Thread(
                target=fix_normalmap_in_mtls,
                args=(rc_process, file_name)
            )
            mtl_fix_thread.start()

    if config.make_layer:
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
