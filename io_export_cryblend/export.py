#------------------------------------------------------------------------------
# Name:        export.py
# Purpose:     Main exporter to CryEngine
#
# Author:      Angelo J. Miner,
#              Daniel White, David Marcelis, Duo Oratar, Mikołaj Milej,
#              Oscar Martin Garcia, Özkan Afacan,
#              Some code borrowed from fbx exporter Campbell Barton
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
    from io_export_cryblend import utils, add, exceptions

from io_export_cryblend.rc import RCInstance
from io_export_cryblend.outpipe import cbPrint
from io_export_cryblend.utils import join

from bpy_extras.io_utils import ExportHelper
from collections import OrderedDict
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


class CrytekDaeExporter:

    def __init__(self, config):
        self._config = config
        self._doc = Document()
        self._materials = self._get_materials()

    def export(self):
        self._prepare_for_export()

        root_element = self._doc.createElement('collada')
        root_element.setAttribute(
            "xmlns", "http://www.collada.org/2005/11/COLLADASchema")
        root_element.setAttribute("version", "1.4.1")
        self._doc.appendChild(root_element)
        self._create_file_header(root_element)

        # Just here for future use:
        self._export_library_cameras(root_element)
        self._export_library_lights(root_element)
        ###

        self._export_library_images(root_element)
        self._export_library_effects(root_element)
        self._export_library_materials(root_element)
        self._export_library_geometries(root_element)

        utils.add_fakebones()
        try:
            self._export_library_controllers(root_element)
            self._export_library_animation_clips_and_animations(root_element)
            self._export_library_visual_scenes(root_element)
        except RuntimeError:
            pass
        finally:
            utils.remove_fakebones()

        self._export_scene(root_element)

        converter = RCInstance(self._config)
        converter.convert_dae(self._doc)

        write_scripts(self._config)

    def _get_materials(self):
        materials = OrderedDict()
        material_counter = {}

        for group in utils.get_mesh_export_nodes(
                self._config.export_selected_nodes):
            material_counter[group.name] = 50
            for object in group.objects:
                for slot in object.material_slots:
                    if slot.material is None:
                        continue

                    if slot.material not in materials:
                        node_name = utils.get_node_name(group)

                        node, index, name, physics = utils.get_material_parts(
                            node_name, slot.material.name)

                        # check if material has no position defined
                        if index == 0:
                            material_counter[group.name] += 1
                            index = material_counter[group.name]

                        materials[slot.material] = "{}__{:02d}__{}__{}".format(
                            node, index, name, physics)

        return materials

    def _get_materials_for_object(self, object_):
        materials = OrderedDict()
        for material, materialname in self._materials.items():
            for object_material in object_.data.materials:
                if material.name == object_material.name:
                    materials[material] = materialname

        return materials

    def _prepare_for_export(self):
        utils.clean_file()

        if self._config.apply_modifiers:
            utils.apply_modifiers()

        if self._config.fix_weights:
            utils.fix_weights()

    def _create_file_header(self, parent_element):
        asset = self._doc.createElement('asset')
        parent_element.appendChild(asset)
        contributor = self._doc.createElement('contributor')
        asset.appendChild(contributor)
        author = self._doc.createElement('author')
        contributor.appendChild(author)
        author_name = self._doc.createTextNode('Blender User')
        author.appendChild(author_name)
        author_tool = self._doc.createElement('authoring_tool')
        author_name_text = self._doc.createTextNode(
            'CryBlend v{}'.format(self._config.cryblend_version))
        author_tool.appendChild(author_name_text)
        contributor.appendChild(author_tool)
        created = self._doc.createElement('created')
        created_value = self._doc.createTextNode(
            datetime.now().isoformat(' '))
        created.appendChild(created_value)
        asset.appendChild(created)
        modified = self._doc.createElement('modified')
        asset.appendChild(modified)
        unit = self._doc.createElement('unit')
        unit.setAttribute('name', 'meter')
        unit.setAttribute('meter', '1')
        asset.appendChild(unit)
        up_axis = self._doc.createElement('up_axis')
        z_up = self._doc.createTextNode('Z_UP')
        up_axis.appendChild(z_up)
        asset.appendChild(up_axis)

    def _export_library_cameras(self, root_element):
        library_cameras = self._doc.createElement('library_cameras')
        root_element.appendChild(library_cameras)

    def _export_library_lights(self, root_element):
        library_lights = self._doc.createElement('library_lights')
        root_element.appendChild(library_lights)

#------------------------------------------------------------------
# Library Images:
#------------------------------------------------------------------

    def _export_library_images(self, parent_element):
        library_images = self._doc.createElement('library_images')
        parent_element.appendChild(library_images)

        if bpy.context.scene.render.engine == 'CYCLES':
            images = self._get_nodes_images_in_export_nodes()
        else:
            images = self._get_image_textures_in_export_nodes()

        for image in images:
            image_element = self._export_library_image(image)
            library_images.appendChild(image_element)

        if self._config.do_textures:
            self._convert_images_to_dds(images)

    def _export_library_image(self, image):
        image_path = utils.get_image_path_for_game(image,
                                                   self._config.game_dir)

        image_element = self._doc.createElement('image')
        image_element.setAttribute('id', image.name)
        image_element.setAttribute('name', image.name)
        init_from = self._doc.createElement('init_from')
        path_node = self._doc.createTextNode(image_path)
        init_from.appendChild(path_node)
        image_element.appendChild(init_from)

        return image_element

    def _get_nodes_images_in_export_nodes(self):
        images = []

        nodes = utils.get_type("texture_nodes")

        for node in nodes:
            try:
                if utils.is_valid_image(node.image):
                    images.append(node.image)

            except AttributeError:
                # don't care about non-image textures
                pass

        # return only unique images
        return list(set(images))

    def _get_image_textures_in_export_nodes(self):
        images = []
        textures = utils.get_type('textures')

        for texture in textures:
            try:
                if utils.is_valid_image(texture.image):
                    images.append(texture.image)

            except AttributeError:
                # don't care about non-image textures
                pass

        # return only unique images
        return list(set(images))

    def _convert_images_to_dds(self, images):
        converter = RCInstance(self._config)
        converter.convert_tif(images)

#--------------------------------------------------------------
# Library Effects:
#--------------------------------------------------------------

    def _export_library_effects(self, parent_element):
        current_element = self._doc.createElement('library_effects')
        parent_element.appendChild(current_element)
        for material, materialname in self._materials.items():
            self._export_library_effects_material(
                material, materialname, current_element)

    def _export_library_effects_material(
            self, material, materialname, current_element):
        images = [[], [], []]

        is_cycles_render = bpy.context.scene.render.engine == 'CYCLES'

        if is_cycles_render:
            self._get_cycles_render_images(material, images)
        else:
            self._get_blender_render_images(material, images)

        effect_node = self._doc.createElement("effect")
        effect_node.setAttribute("id", "{}_fx".format(materialname))
        profile_node = self._doc.createElement("profile_COMMON")
        for image in images:
            if len(image) != 0:
                profile_node.appendChild(image[1])
                profile_node.appendChild(image[2])
        technique_common = self._doc.createElement("technique")
        technique_common.setAttribute("sid", "common")

        phong = self._create_material_node(material, images)
        technique_common.appendChild(phong)
        profile_node.appendChild(technique_common)

        extra = self._create_double_sided_extra("GOOGLEEARTH")
        profile_node.appendChild(extra)
        effect_node.appendChild(profile_node)

        extra = self._create_double_sided_extra("MAX3D")
        effect_node.appendChild(extra)
        current_element.appendChild(effect_node)

    def _get_cycles_render_images(self, material, images):
        cycles_nodes = utils.get_texture_nodes_for_material(material)
        for cycles_node in cycles_nodes:
            image = cycles_node.image
            if not image:
                raise exceptions.CryBlendException(
                    "One of texture slots has no image assigned.")

            surface, sampler = self._create_surface_and_sampler(image.name)
            if cycles_node.name == "Image Texture":
                images[0] = [image.name, surface, sampler]
            if cycles_node.name == "Specular":
                images[1] = [image.name, surface, sampler]
            if cycles_node.name == "Normal":
                images[2] = [image.name, surface, sampler]

    def _get_blender_render_images(self, material, images):
        texture_slots = utils.get_texture_slots_for_material(material)
        for texture_slot in texture_slots:
            image = texture_slot.texture.image
            if not image:
                raise exceptions.CryBlendException(
                    "One of texture slots has no image assigned.")

            surface, sampler = self._create_surface_and_sampler(image.name)
            if texture_slot.use_map_color_diffuse:
                images[0] = [image.name, surface, sampler]
            if texture_slot.use_map_color_spec:
                images[1] = [image.name, surface, sampler]
            if texture_slot.use_map_normal:
                images[2] = [image.name, surface, sampler]

    def _create_surface_and_sampler(self, image_name):
        surface = self._doc.createElement("newparam")
        surface.setAttribute("sid", "{}-surface".format(image_name))
        surface_node = self._doc.createElement("surface")
        surface_node.setAttribute("type", "2D")
        init_from_node = self._doc.createElement("init_from")
        temp_node = self._doc.createTextNode(image_name)
        init_from_node.appendChild(temp_node)
        surface_node.appendChild(init_from_node)
        surface.appendChild(surface_node)
        sampler = self._doc.createElement("newparam")
        sampler.setAttribute("sid", "{}-sampler".format(image_name))
        sampler_node = self._doc.createElement("sampler2D")
        source_node = self._doc.createElement("source")
        temp_node = self._doc.createTextNode(
            "{}-surface".format(image_name))
        source_node.appendChild(temp_node)
        sampler_node.appendChild(source_node)
        sampler.appendChild(sampler_node)

        return surface, sampler

    def _create_material_node(self, material, images):
        phong = self._doc.createElement("phong")

        emission = self._create_color_node(material, "emission")
        ambient = self._create_color_node(material, "ambient")
        if len(images[0]) != 0:
            diffuse = self._create_texture_node(images[0][0], "diffuse")
        else:
            diffuse = self._create_color_node(material, "diffuse")
        if len(images[1]) != 0:
            specular = self._create_texture_node(images[1][0], "specular")
        else:
            specular = self._create_color_node(material, "specular")

        shininess = self._create_attribute_node(material, "shininess")
        index_refraction = self._create_attribute_node(
            material, "index_refraction")

        phong.appendChild(emission)
        phong.appendChild(ambient)
        phong.appendChild(diffuse)
        phong.appendChild(specular)
        phong.appendChild(shininess)
        phong.appendChild(index_refraction)
        if len(images[2]) != 0:
            normal = self._create_texture_node(images[2][0], "normal")
            phong.appendChild(normal)

        return phong

    def _create_color_node(self, material, type_):
        node = self._doc.createElement(type_)
        color = self._doc.createElement("color")
        color.setAttribute("sid", type_)
        col = utils.get_material_color(material, type_)
        color_text = self._doc.createTextNode(col)
        color.appendChild(color_text)
        node.appendChild(color)

        return node

    def _create_texture_node(self, image_name, type_):
        node = self._doc.createElement(type_)
        texture = self._doc.createElement("texture")
        texture.setAttribute("texture", "{}-sampler".format(image_name))
        node.appendChild(texture)

        return node

    def _create_attribute_node(self, material, type_):
        node = self._doc.createElement(type_)
        float = self._doc.createElement("float")
        float.setAttribute("sid", type_)
        val = utils.get_material_attribute(material, type_)
        value = self._doc.createTextNode(val)
        float.appendChild(value)
        node.appendChild(float)

        return node

    def _create_double_sided_extra(self, profile):
        extra = self._doc.createElement("extra")
        technique = self._doc.createElement("technique")
        technique.setAttribute("profile", profile)
        double_sided = self._doc.createElement("double_sided")
        double_sided_value = self._doc.createTextNode("1")
        double_sided.appendChild(double_sided_value)
        technique.appendChild(double_sided)
        extra.appendChild(technique)

        return extra

#------------------------------------------------------------------
# Library Materials:
#------------------------------------------------------------------

    def _export_library_materials(self, parent_element):
        library_materials = self._doc.createElement('library_materials')

        for material, materialname in self._materials.items():
            material_element = self._doc.createElement('material')
            material_element.setAttribute('id', materialname)
            instance_effect = self._doc.createElement('instance_effect')
            instance_effect.setAttribute('url', '#{}_fx'.format(materialname))
            material_element.appendChild(instance_effect)
            library_materials.appendChild(material_element)

        parent_element.appendChild(library_materials)

#------------------------------------------------------------------
# Library Geometries:
#------------------------------------------------------------------

    def _export_library_geometries(self, parent_element):
        libgeo = self._doc.createElement("library_geometries")
        parent_element.appendChild(libgeo)
        for object_ in utils.get_type("geometry"):
            utils.set_active(object_)
            if object_.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            object_.data.update(calc_tessface=1)
            mesh = object_.data
            object_.name = object_.name
            geometry_node = self._doc.createElement("geometry")
            geometry_node.setAttribute("id", object_.name)
            mesh_node = self._doc.createElement("mesh")

            print('')
            cbPrint('"{}" object is processing...'.format(object_.name))

            start_time = clock()
            self._write_positions(object_, mesh, mesh_node)
            cbPrint('Positions took {:.4f} sec.'.format(clock() - start_time))

            start_time = clock()
            self._write_normals(object_, mesh, mesh_node)
            cbPrint('Normals took {:.4f} sec.'.format(clock() - start_time))

            start_time = clock()
            self._write_uvs(object_, mesh, mesh_node)
            cbPrint('UVs took {:.4f} sec.'.format(clock() - start_time))

            start_time = clock()
            self._write_vertex_colors(object_, mesh, mesh_node)
            cbPrint(
                'Vertex colors took {:.4f} sec.'.format(
                    clock() - start_time))

            start_time = clock()
            self._write_vertices(object_, mesh, mesh_node)
            cbPrint('Vertices took {:.4f} sec.'.format(clock() - start_time))

            start_time = clock()
            self._write_polylist(object_, mesh, mesh_node)
            cbPrint('Polylist took {:.4f} sec.'.format(clock() - start_time))

            extra = self._create_double_sided_extra("MAYA")
            mesh_node.appendChild(extra)
            geometry_node.appendChild(mesh_node)
            libgeo.appendChild(geometry_node)

    def _write_positions(self, object_, mesh, root):
        float_positions = []
        for vertex in mesh.vertices:
            float_positions.extend(vertex.co)

        id_ = "{!s}-positions".format(object_.name)
        source = utils.write_source(id_, "float", float_positions, "XYZ")
        root.appendChild(source)

    def _write_normals(self, object_, mesh, root):
        float_normals = []
        float_normals_count = ""

        for face in mesh.tessfaces:
            if face.use_smooth:
                for vert in face.vertices:
                    vertex = mesh.vertices[vert]
                    float_normals.extend(vertex.normal)
            else:
                if self._config.average_planar:
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

    def _write_uvs(self, object_, mesh, root):
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

    def _write_vertex_colors(self, object_, mesh, root):
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
                            alpha = (color[0] + color[1] + color[2]) / 3
                            float_colors.extend([1, 1, 1, alpha])
                        else:
                            float_colors.extend(color)

        if float_colors:
            id_ = "{!s}-colors".format(object_.name)
            params = ("RGBA" if alpha_found else "RGB")
            source = utils.write_source(id_, "float", float_colors, params)
            root.appendChild(source)

    def _write_vertices(self, object_, mesh, root):
        vertices = self._doc.createElement("vertices")
        vertices.setAttribute("id", "{}-vertices".format(object_.name))
        input = utils.write_input(object_.name, None, "positions", "POSITION")
        vertices.appendChild(input)
        root.appendChild(vertices)

    def _write_polylist(self, object_, mesh, root):
        matindex = 0
        for material, materialname in self._get_materials_for_object(
                object_).items():
            vert_data = ''
            verts_per_poly = ''
            poly_count = normal = texcoord = 0

            for face in mesh.tessfaces:
                if face.material_index == matindex:
                    verts_per_poly = join(
                        verts_per_poly, len(
                            face.vertices), ' ')
                    poly_count += 1
                    for vert in face.vertices:
                        data = self._write_vertex_data(
                            mesh, face, vert, normal, texcoord)
                        vert_data = join(vert_data, data)
                        texcoord += 1
                else:
                    texcoord += len(face.vertices)

                if face.use_smooth:
                    normal += len(face.vertices)
                else:
                    normal += 1

            if poly_count == 0:
                matindex += 1
                continue

            polylist = self._doc.createElement('polylist')
            polylist.setAttribute('material', materialname)
            polylist.setAttribute('count', str(poly_count))

            inputs = []
            inputs.append(
                utils.write_input(
                    object_.name,
                    0,
                    'vertices',
                    'VERTEX'))
            inputs.append(
                utils.write_input(
                    object_.name,
                    1,
                    'normals',
                    'NORMAL'))
            inputs.append(
                utils.write_input(
                    object_.name,
                    2,
                    'UVMap-0',
                    'TEXCOORD'))
            if mesh.vertex_colors:
                inputs.append(
                    utils.write_input(
                        object_.name,
                        3,
                        'colors',
                        'COLOR'))

            for input in inputs:
                polylist.appendChild(input)

            vcount = self._doc.createElement('vcount')
            vcount_text = self._doc.createTextNode(verts_per_poly)
            vcount.appendChild(vcount_text)

            p = self._doc.createElement('p')
            p_text = self._doc.createTextNode(vert_data)
            p.appendChild(p_text)

            polylist.appendChild(vcount)
            polylist.appendChild(p)
            root.appendChild(polylist)
            matindex += 1

    def _write_vertex_data(self, mesh, face, vert, normal, texcoord):
        if face.use_smooth:
            normal = vert

        if mesh.vertex_colors:
            return "{:d} {:d} {:d} {:d} ".format(
                vert, normal, texcoord, texcoord)
        else:
            return "{:d} {:d} {:d} ".format(vert, normal, texcoord)

# -------------------------------------------------------------------------
# Library Controllers: --> Skeleton Armature and List of Bone Names
#                      --> Skin Geometry, Weights, Transform Matrices
# -------------------------------------------------------------------------

    def _export_library_controllers(self, parent_element):
        library_node = self._doc.createElement("library_controllers")

        for object_ in utils.get_type("geometry"):
            if not utils.is_bone_geometry(object_):
                armature = utils.get_armature_for_object(object_)
                if armature is not None:
                    self._process_bones(library_node,
                                        object_,
                                        armature)

        parent_element.appendChild(library_node)

    def _process_bones(self, parent_node, object_, armature):
        mesh = object_.data
        id_ = "{!s}_{!s}".format(armature.name, object_.name)

        controller_node = self._doc.createElement("controller")
        parent_node.appendChild(controller_node)
        controller_node.setAttribute("id", id_)

        skin_node = self._doc.createElement("skin")
        skin_node.setAttribute("source", "#{}".format(object_.name))
        controller_node.appendChild(skin_node)

        bind_shape_matrix = self._doc.createElement("bind_shape_matrix")
        utils.write_matrix(Matrix(), bind_shape_matrix)
        skin_node.appendChild(bind_shape_matrix)

        self._process_bone_joints(object_, armature, skin_node)
        self._process_bone_matrices(object_, armature, skin_node)
        self._process_bone_weights(object_, armature, skin_node)

        joints = self._doc.createElement("joints")
        input = utils.write_input(id_, None, "joints", "JOINT")
        joints.appendChild(input)
        input = utils.write_input(id_, None, "matrices", "INV_BIND_MATRIX")
        joints.appendChild(input)
        skin_node.appendChild(joints)

    def _process_bone_joints(self, object_, armature, skin_node):

        bones = utils.get_bones(armature)
        id_ = "{!s}_{!s}-joints".format(armature.name, object_.name)
        group = utils.get_armature_node(object_)
        bone_names = []
        for bone in bones:
            props_name = self._create_properties_name(bone, group)
            bone_name = "{!s}{!s}".format(bone.name, props_name)
            bone_names.append(bone_name)
        source = utils.write_source(id_, "IDREF", bone_names, [])
        skin_node.appendChild(source)

    def _process_bone_matrices(self, object_, armature, skin_node):

        bones = utils.get_bones(armature)
        bone_matrices = []
        for bone in bones:
            fakebone = utils.get_fakebone(bone.name)
            if fakebone is None:
                return
            matrix_local = copy.deepcopy(fakebone.matrix_local)
            utils.negate_z_axis_of_matrix(matrix_local)
            bone_matrices.extend(utils.matrix_to_array(matrix_local))

        id_ = "{!s}_{!s}-matrices".format(armature.name, object_.name)
        source = utils.write_source(id_, "float4x4", bone_matrices, [])
        skin_node.appendChild(source)

    def _process_bone_weights(self, object_, armature, skin_node):

        bones = utils.get_bones(armature)
        group_weights = []
        vw = ""
        vertex_groups_lengths = ""
        vertex_count = 0
        bone_list = {}

        for bone_id, bone in enumerate(bones):
            bone_list[bone.name] = bone_id

        for vertex in object_.data.vertices:
            vertex_group_count = 0
            for group in vertex.groups:
                group_name = object_.vertex_groups[group.group].name
                if (group.weight == 0 or
                        group_name not in bone_list):
                    continue
                if vertex_group_count == 8:
                    cbPrint("Too many bone references in {}:{} vertex group"
                            .format(object_.name, group_name))
                    continue
                group_weights.append(group.weight)
                vw = "{}{} {} ".format(vw, bone_list[group_name], vertex_count)
                vertex_count += 1
                vertex_group_count += 1

            vertex_groups_lengths = "{}{} ".format(vertex_groups_lengths,
                                                   vertex_group_count)

        id_ = "{!s}_{!s}-weights".format(armature.name, object_.name)
        source = utils.write_source(id_, "float", group_weights, [])
        skin_node.appendChild(source)

        vertex_weights = self._doc.createElement("vertex_weights")
        vertex_weights.setAttribute("count", str(len(object_.data.vertices)))

        id_ = "{!s}_{!s}".format(armature.name, object_.name)
        input = utils.write_input(id_, 0, "joints", "JOINT")
        vertex_weights.appendChild(input)
        input = utils.write_input(id_, 1, "weights", "WEIGHT")
        vertex_weights.appendChild(input)

        vcount = self._doc.createElement("vcount")
        vcount_text = self._doc.createTextNode(vertex_groups_lengths)
        vcount.appendChild(vcount_text)
        vertex_weights.appendChild(vcount)

        v = self._doc.createElement("v")
        v_text = self._doc.createTextNode(vw)
        v.appendChild(v_text)
        vertex_weights.appendChild(v)

        skin_node.appendChild(vertex_weights)

# -----------------------------------------------------------------------------
# Library Animation and Clips: --> Animations, F-Curves
# -----------------------------------------------------------------------------

    def _export_library_animation_clips_and_animations(self, parent_element):
        libanmcl = self._doc.createElement("library_animation_clips")
        libanm = self._doc.createElement("library_animations")
        parent_element.appendChild(libanmcl)
        parent_element.appendChild(libanm)


# ---------------------------------------------------------------------
# Library Visual Scene: --> Skeleton and _Phys bones, Bone
#       Transformations, and Instance URL (_boneGeometry) and extras.
# ---------------------------------------------------------------------

    def _export_library_visual_scenes(self, parent_element):
        current_element = self._doc.createElement("library_visual_scenes")
        visual_scene = self._doc.createElement("visual_scene")
        visual_scene.setAttribute("id", "scene")
        visual_scene.setAttribute("name", "scene")
        current_element.appendChild(visual_scene)
        parent_element.appendChild(current_element)

        if utils.get_mesh_export_nodes(self._config.export_selected_nodes):
            if utils.are_duplicate_nodes():
                message = "Duplicate Node Names"
                bpy.ops.screen.display_error('INVOKE_DEFAULT', message=message)

            for group in utils.get_mesh_export_nodes(
                    self._config.export_selected_nodes):
                self._write_export_node(group, visual_scene)
        else:
            pass  # TODO: Handle No Export Nodes Error

    def _write_export_node(self, group, visual_scene):
        if not self._config.export_for_lumberyard:
            node_name = "CryExportNode_{}".format(utils.get_node_name(group))
            node = self._doc.createElement("node")
            node.setAttribute("id", node_name)
            node.setIdAttribute("id")
        else:
            node_name = "{}".format(utils.get_node_name(group))
            node = self._doc.createElement("node")
            node.setAttribute("id", node_name)
            node.setAttribute("LumberyardExportNode", "1")
            node.setIdAttribute("id")

        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        self._write_transforms(bpy.context.active_object, node)
        bpy.ops.object.delete(use_global=False)

        root_objects = []
        for object_ in group.objects:
            if utils.is_visual_scene_node_writed(object_, group):
                root_objects.append(object_)

        node = self._write_visual_scene_node(root_objects, node, group)

        extra = self._create_cryengine_extra(group)
        node.appendChild(extra)
        visual_scene.appendChild(node)

    def _write_visual_scene_node(self, objects, parent_node, group):
        for object_ in objects:
            if object_.type == "MESH" and not utils.is_fakebone(object_):
                prop_name = join(object_.name,
                                 self._create_properties_name(object_, group))
                node = self._doc.createElement("node")
                node.setAttribute("id", prop_name)
                node.setAttribute("name", prop_name)
                node.setIdAttribute("id")

                self._write_transforms(object_, node)

                ALLOWED_NODE_TYPES = ('cgf', 'cga', 'chr', 'skin')
                if utils.get_node_type(group) in ALLOWED_NODE_TYPES:
                    instance = self._create_instance(object_)
                    if instance is not None:
                        node.appendChild(instance)

                extra = self._create_cryengine_extra(object_)
                if extra is not None:
                    node.appendChild(extra)

                parent_node.appendChild(node)

                if object_.parent is not None and object_.parent.type == "ARMATURE":
                    self._write_bone_list([utils.get_root_bone(
                        object_.parent)], object_, parent_node, group)

            elif object_.type == "ARMATURE" and utils.is_physical(object_):
                self._write_bone_list([utils.get_root_bone(
                    object_)], object_, parent_node, group)

        return parent_node

    def _write_bone_list(self, bones, object_, parent_node, group):
        scene = bpy.context.scene
        bone_names = []

        for bone in bones:
            props_name = self._create_properties_name(bone, group)
            props_ik = self._create_ik_properties(bone, object_)
            bone_name = join(bone.name, props_name, props_ik)
            bone_names.append(bone_name)

            node = self._doc.createElement("node")
            node.setAttribute("id", bone_name)
            node.setAttribute("name", bone_name)
            node.setIdAttribute("id")

            fakebone = utils.get_fakebone(bone.name)
            if fakebone is not None:
                self._write_transforms(fakebone, node)

                bone_geometry = utils.get_bone_geometry(bone.name)
                if bone_geometry is not None:
                    instance = self._create_instance_for_bone(
                        bone, bone_geometry)
                    node.appendChild(instance)

                    extra = self._create_physic_proxy_for_bone(
                        object_.parent, bone)
                    if extra is not None:
                        node.appendChild(extra)

            elif utils.is_physical(bone):
                bone_geometry = utils.get_bone_geometry(bone.name)
                if bone_geometry is not None:
                    self._write_transforms(bone_geometry, node)

            parent_node.appendChild(node)

            if bone.children:
                self._write_bone_list(bone.children, object_, node, group)

    def _create_instance_for_bone(self, bone, bone_geometry):
        instance = None

        instance = self._doc.createElement("instance_geometry")
        instance.setAttribute("url", "#{}_boneGeometry".format(bone.name))
        bm = self._doc.createElement("bind_material")
        tc = self._doc.createElement("technique_common")

        for mat in bone_geometry.material_slots:
            im = self._doc.createElement("instance_material")
            im.setAttribute("symbol", mat.name)
            im.setAttribute("target", "#{}".format(mat.name))
            bvi = self._doc.createElement("bind_vertex_input")
            bvi.setAttribute("semantic", "UVMap")
            bvi.setAttribute("input_semantic", "TEXCOORD")
            bvi.setAttribute("input_set", "0")
            im.appendChild(bvi)
            tc.appendChild(im)

        bm.appendChild(tc)
        instance.appendChild(bm)

        return instance

    def _create_physic_proxy_for_bone(self, object_, bone):
        extra = None
        try:
            bonePhys = object_.pose.bones[bone.name]['phys_proxy']
            cbPrint(bone.name + " physic proxy is " + bonePhys)

            extra = self._doc.createElement("extra")
            techcry = self._doc.createElement("technique")
            techcry.setAttribute("profile", "CryEngine")
            prop2 = self._doc.createElement("properties")

            cryprops = self._doc.createTextNode(bonePhys)
            prop2.appendChild(cryprops)
            techcry.appendChild(prop2)
            extra.appendChild(techcry)
        except:
            pass

        return extra

    def _write_transforms(self, object_, node):
        trans = self._create_translation_node(object_)
        rotx, roty, rotz = self._create_rotation_node(object_)
        scale = self._create_scale_node(object_)

        node.appendChild(trans)
        node.appendChild(rotx)
        node.appendChild(roty)
        node.appendChild(rotz)
        node.appendChild(scale)

    def _create_translation_node(self, object_):
        trans = self._doc.createElement("translate")
        trans.setAttribute("sid", "translation")
        trans_text = self._doc.createTextNode("{:f} {:f} {:f}".format(
            * object_.location))
        trans.appendChild(trans_text)

        return trans

    def _create_rotation_node(self, object_):
        rotx = self._write_rotation(
            "X", "1 0 0 {:f}", object_.rotation_euler[0])
        roty = self._write_rotation(
            "Y", "0 1 0 {:f}", object_.rotation_euler[1])
        rotz = self._write_rotation(
            "Z", "0 0 1 {:f}", object_.rotation_euler[2])

        return rotx, roty, rotz

    def _write_rotation(self, axis, textFormat, rotation):
        rot = self._doc.createElement("rotate")
        rot.setAttribute("sid", "rotation_{}".format(axis))
        rot_text = self._doc.createTextNode(textFormat.format(
            rotation * utils.to_degrees))
        rot.appendChild(rot_text)

        return rot

    def _create_scale_node(self, object_):
        scale = self._doc.createElement("scale")
        scale.setAttribute("sid", "scale")
        scale_text = self._doc.createTextNode(
            utils.floats_to_string(object_.scale, " ", "%s"))
        scale.appendChild(scale_text)

        return scale

    def _create_instance(self, object_):
        armature = utils.get_armature_for_object(object_)
        instance = None
        if armature is not None:
            instance = self._doc.createElement("instance_controller")
            # This binds the mesh object to the armature in control of it
            instance.setAttribute("url", "#{!s}_{!s}".format(
                armature.name,
                object_.name))
        elif object_.name[:6] != "_joint" and object_.type == "MESH":
            instance = self._doc.createElement("instance_geometry")
            instance.setAttribute("url", "#{!s}".format(object_.name))

        if instance is not None:
            bind_material = self._create_bind_material(object_)
            instance.appendChild(bind_material)
            return instance

    def _create_bind_material(self, object_):
        bind_material = self._doc.createElement('bind_material')
        technique_common = self._doc.createElement('technique_common')

        for material, materialname in self._get_materials_for_object(
                object_).items():
            instance_material = self._doc.createElement(
                'instance_material')
            instance_material.setAttribute('symbol', materialname)
            instance_material.setAttribute('target', '#{!s}'.format(
                materialname))

            bind_vertex_input = self._doc.createElement(
                'bind_vertex_input')
            bind_vertex_input.setAttribute('semantic', 'UVMap')
            bind_vertex_input.setAttribute('input_semantic', 'TEXCOORD')
            bind_vertex_input.setAttribute('input_set', '0')

            instance_material.appendChild(bind_vertex_input)
            technique_common.appendChild(instance_material)

        bind_material.appendChild(technique_common)

        return bind_material

    def _create_cryengine_extra(self, node):
        extra = self._doc.createElement("extra")
        technique = self._doc.createElement("technique")
        technique.setAttribute("profile", "CryEngine")
        properties = self._doc.createElement("properties")

        ALLOWED_NODE_TYPES = ("cgf", "cga", "chr", "skin", "anm", "i_caf")

        if utils.is_export_node(node):
            node_type = utils.get_node_type(node)
            if node_type in ALLOWED_NODE_TYPES:
                prop = self._doc.createTextNode(
                    "fileType={}".format(node_type))
                properties.appendChild(prop)
            if self._config.do_not_merge:
                prop = self._doc.createTextNode("DoNotMerge")
                properties.appendChild(prop)
        else:
            if not node.rna_type.id_data.items():
                return
        for prop in node.rna_type.id_data.items():
            self._create_user_defined_property(prop, properties)

        technique.appendChild(properties)

        if (node.name[:6] == "_joint"):
            helper = self._create_helper_joint(node)
            technique.appendChild(helper)

        extra.appendChild(technique)

        return extra

    def _create_user_defined_property(self, prop, node):
        if prop:
            prop_name = prop[0]
            if add.is_user_defined_property(prop_name):
                udp = None

                if isinstance(prop[1], str):
                    udp = self._doc.createTextNode("{!s}".format(prop[1]))
                else:
                    udp = self._doc.createTextNode("{!s}=".format(prop[0])
                                                   + "{!s}".format(prop[1]))

                node.appendChild(udp)

    def _create_helper_joint(self, object_):
        x1, y1, z1, x2, y2, z2 = utils.get_bounding_box(object_)

        min = self._doc.createElement("bound_box_min")
        min_text = self._doc.createTextNode(
            "{:f} {:f} {:f}".format(x1, y1, z1))
        min.appendChild(min_text)

        max = self._doc.createElement("bound_box_max")
        max_text = self._doc.createTextNode(
            "{:f} {:f} {:f}".format(x2, y2, z2))
        max.appendChild(max_text)

        joint = self._doc.createElement("helper")
        joint.setAttribute("type", "dummy")
        joint.appendChild(min)
        joint.appendChild(max)

        return joint

    def _create_properties_name(self, bone, group):
        bone_name = bone.name.replace("__", "*")
        node_name = utils.get_node_name(group)
        props_name = '%{!s}%--PRprops_name={!s}'.format(node_name, bone_name)

        return props_name

    def _create_ik_properties(self, bone, object_):
        props = ""
        if utils.is_physical(bone):

            armature_object = bpy.data.objects[object_.name[:-5]]
            pose_bone = armature_object.pose.bones[bone.name[:-5]]

            xIK, yIK, zIK = add.get_bone_ik_max_min(pose_bone)

            damping, spring, spring_tension = add.get_bone_ik_properties(
                pose_bone)

            props = join(
                xIK,
                '_xdamping={}'.format(damping[0]),
                '_xspringangle={}'.format(spring[0]),
                '_xspringtension={}'.format(spring_tension[0]),

                yIK,
                '_ydamping={}'.format(damping[1]),
                '_yspringangle={}'.format(spring[1]),
                '_yspringtension={}'.format(spring_tension[1]),

                zIK,
                '_zdamping={}'.format(damping[2]),
                '_zspringangle={}'.format(spring[2]),
                '_zspringtension={}'.format(spring_tension[2])
            )

        return props

    def _export_scene(self, parent_element):
        scene = self._doc.createElement("scene")
        instance_visual_scene = self._doc.createElement(
            "instance_visual_scene")
        instance_visual_scene.setAttribute("url", "#scene")
        scene.appendChild(instance_visual_scene)
        parent_element.appendChild(scene)


def write_scripts(config):
    filepath = bpy.path.ensure_ext(config.filepath, ".dae")
    if not config.make_chrparams and not config.make_cdf:
        return

    dae_path = utils.get_absolute_path_for_rc(filepath)
    output_path = os.path.dirname(dae_path)

    for chr_name in utils.get_chr_names(self._config.export_selected_nodes):
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
    if not config.disable_rc and not os.path.isfile(config.rc_path):
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
