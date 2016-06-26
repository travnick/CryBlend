#------------------------------------------------------------------------------
# Name:        utils.py
# Purpose:     Utility functions for use throughout the add-on
#
# Author:      Angelo J. Miner,
#              Daniel White, David Marcelis, Duo Oratar, Mikołaj Milej,
#              Oscar Martin Garcia, Özkan Afacan
#
# Created:     23/02/2012
# Copyright:   (c) Angelo J. Miner 2012
# Licence:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>


if "bpy" in locals():
    import imp
    imp.reload(exceptions)
else:
    import bpy
    from io_export_cryblend import exceptions


from io_export_cryblend.outpipe import cbPrint
from mathutils import Matrix, Vector
from xml.dom.minidom import Document, parseString
import bpy
import fnmatch
import math
import os
import random
import re
import subprocess
import sys
import xml.dom.minidom
import time


# Globals:
to_degrees = 180.0 / math.pi


#------------------------------------------------------------------------------
# Conversions:
#------------------------------------------------------------------------------

def color_to_string(color, a):
    if type(color) in (float, int):
        return "{:f} {:f} {:f} {:f}".format(color, color, color, a)
    elif type(color).__name__ == "Color":
        return "{:f} {:f} {:f} {:f}".format(color.r, color.g, color.b, a)


def frame_to_time(frame):
    fps_base = bpy.context.scene.render.fps_base
    fps = bpy.context.scene.render.fps
    return fps_base * frame / fps


def matrix_to_string(matrix):
    return str(matrix_to_array(matrix))


def floats_to_string(floats, separator=" ", precision="%.6f"):
    return separator.join(precision % x for x in floats)


def strings_to_string(strings, separator=" "):
    return separator.join(string for string in strings)


def matrix_to_array(matrix):
    array = []
    for row in matrix:
        array.extend(row)

    return array


def write_matrix(matrix, node):
    doc = Document()
    for row in matrix:
        row_string = floats_to_string(row)
        node.appendChild(doc.createTextNode(row_string))


def join(*items):
    strings = []
    for item in items:
        strings.append(str(item))
    return "".join(strings)


#------------------------------------------------------------------------------
# Matrix Manipulations:
#------------------------------------------------------------------------------

def negate_z_axis_of_matrix(matrix_local):
    for i in range(0, 3):
        matrix_local[i][3] = -matrix_local[i][3]


#------------------------------------------------------------------------------
# Path Manipulations:
#------------------------------------------------------------------------------

def get_absolute_path(file_path):
    [is_relative, file_path] = strip_blender_path_prefix(file_path)

    if is_relative:
        blend_file_path = os.path.dirname(bpy.data.filepath)
        file_path = '{}/{}'.format(blend_file_path, file_path)

    return os.path.abspath(file_path)


def get_absolute_path_for_rc(file_path):
    # 'z:' is for wine (linux, mac) path
    # there should be better way to determine it
    WINE_DEFAULT_DRIVE_LETTER = 'z:'

    file_path = get_absolute_path(file_path)

    if sys.platform != 'win32':
        file_path = '{}{}'.format(WINE_DEFAULT_DRIVE_LETTER, file_path)

    return file_path


def get_relative_path(filepath, start=None):
    blend_file_directory = os.path.dirname(bpy.data.filepath)
    [is_relative_to_blend_file, filepath] = strip_blender_path_prefix(filepath)

    if not start:
        if is_relative_to_blend_file:
            return filepath

        # path is not relative, so create path relative to blend file.
        start = blend_file_directory

        if not start:
            raise exceptions.BlendNotSavedException

    else:
        # make absolute path to be able make relative to 'start'
        if is_relative_to_blend_file:
            filepath = os.path.normpath(os.path.join(blend_file_directory,
                                                     filepath))

    return make_relative_path(filepath, start)


def strip_blender_path_prefix(path):
    is_relative = False
    BLENDER_RELATIVE_PATH_PREFIX = '//'
    prefix_length = len(BLENDER_RELATIVE_PATH_PREFIX)

    if path.startswith(BLENDER_RELATIVE_PATH_PREFIX):
        path = path[prefix_length:]
        is_relative = True

    return (is_relative, path)


def make_relative_path(filepath, start):
    try:
        relative_path = os.path.relpath(filepath, start)
        return relative_path

    except ValueError:
        raise exceptions.TextureAndBlendDiskMismatchException(start, filepath)


def get_path_with_new_extension(path, extension):
    return '{}.{}'.format(os.path.splitext(path)[0], extension)


def strip_extension_from_path(path):
    return os.path.splitext(path)[0]


def get_extension_from_path(path):
    return os.path.splitext(path)[1]


def normalize_path(path):
    path = path.replace("\\", "/")

    multiple_paths = re.compile("/{2,}")
    path = multiple_paths.sub("/", path)

    if path[0] == "/":
        path = path[1:]

    if path[-1] == "/":
        path = path[:-1]

    return path


def build_path(*components):
    path = "/".join(components)
    path = path.replace("/.", ".")  # accounts for extension
    return normalize_path(path)


def get_filename(path):
    path_normalized = normalize_path(path)
    components = path_normalized.split("/")
    name = os.path.splitext(components[-1])[0]
    return name


def trim_path_to(path, trim_to):
    path_normalized = normalize_path(path)
    components = path_normalized.split("/")
    for index, component in enumerate(components):
        if component == trim_to:
            cbPrint("FOUND AN INSTANCE")
            break
    cbPrint(index)
    components_trimmed = components[index:]
    cbPrint(components_trimmed)
    path_trimmed = build_path(*components_trimmed)
    cbPrint(path_trimmed)
    return path_trimmed


#------------------------------------------------------------------------------
# File Clean-Up:
#------------------------------------------------------------------------------

def clean_file():
    for texture in get_type("textures"):
        try:
            texture.image.name = replace_invalid_rc_characters(
                texture.image.name)
        except AttributeError:
            pass
    for material in get_type("materials"):
        material.name = replace_invalid_rc_characters(material.name)
    for node in get_type("objects"):
        node.name = replace_invalid_rc_characters(node.name)
        try:
            node.data.name = replace_invalid_rc_characters(node.data.name)
        except AttributeError:
            pass
        if node.type == "ARMATURE":
            for bone in node.data.bones:
                bone.name = replace_invalid_rc_characters(bone.name)
    for node in get_export_nodes():
        node_name = get_node_name(node)
        nodetype = get_node_type(node)
        node_name = replace_invalid_rc_characters(node_name)
        node.name = "{}.{}".format(node_name, nodetype)


def replace_invalid_rc_characters(string):
    # Remove leading and trailing spaces.
    string.strip()

    # Replace remaining white spaces with double underscores.
    string = "__".join(string.split())

    character_map = {
        "a": "àáâå",
        "c": "ç",
        "e": "èéêë",
        "i": "ìíîïı",
        "l": "ł",
        "n": "ñ",
        "o": "òóô",
        "u": "ùúû",
        "y": "ÿ",
        "ss": "ß",
        "ae": "äæ",
        "oe": "ö",
        "ue": "ü"
    }  # Expand with more individual replacement rules.

    # Individual replacement.
    for good, bad in character_map.items():
        for char in bad:
            string = string.replace(char, good)
            string = string.replace(char.upper(), good.upper())

    # Remove all remaining non alphanumeric characters except underscores,
    # dots, and dollar signs.
    string = re.sub("[^.^_^$0-9A-Za-z]", "", string)

    return string


def fix_weights():
    for object_ in get_type("skins"):
        override = get_3d_context(object_)
        try:
            bpy.ops.object.vertex_group_normalize_all(
                override, lock_active=False)
        except:
            raise exceptions.CryBlendException(
                "Please fix weightless vertices first.")
    cbPrint("Weights Corrected.")


def apply_modifiers():
    for object_ in bpy.data.objects:
        for mod in object_.modifiers:
            if mod.type != "ARMATURE":
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except RuntimeError:
                    pass


#------------------------------------------------------------------------------
# Collections:
#------------------------------------------------------------------------------

def get_export_nodes(just_selected=False):
    export_nodes = []

    if just_selected:
        return __get_selected_nodes()

    for group in bpy.data.groups:
        if is_export_node(group) and len(group.objects) > 0:
            export_nodes.append(group)

    return export_nodes


def get_mesh_export_nodes(just_selected=False):
    export_nodes = []

    ALLOWED_NODE_TYPES = ('cgf', 'cga', 'chr', 'skin')
    for node in get_export_nodes(just_selected):
        if get_node_type(node) in ALLOWED_NODE_TYPES:
            export_nodes.append(node)

    return export_nodes


def get_chr_names(just_selected=False):
    chr_names = []

    for node in get_export_nodes(just_selected):
        if get_node_type(node) == 'chr':
            chr_nodes.append(get_node_name(node))

    return chr_names


def get_animation_export_nodes(just_selected=False):
    export_nodes = []

    if just_selected:
        return __get_selected_nodes()

    ALLOWED_NODE_TYPES = ('anm', 'i_caf')
    for group in bpy.data.groups:
        if is_export_node(group) and len(group.objects) > 0:
            if get_node_type(group) in ALLOWED_NODE_TYPES:
                export_nodes.append(group)

    return export_nodes


def __get_selected_nodes():
    export_nodes = []

    for object in bpy.context.selected_objects:
        for group in object.users_group:
            if is_export_node(group) and group not in export_nodes:
                export_nodes.append(group)

    return export_nodes


def get_type(type_):
    dispatch = {
        "objects": __get_objects,
        "geometry": __get_geometry,
        "controllers": __get_controllers,
        "skins": __get_skins,
        "fakebones": __get_fakebones,
        "bone_geometry": __get_bone_geometry,
        "materials": __get_materials,
        "texture_slots": __get_texture_slots,
        "textures": __get_textures,
        "texture_nodes": __get_texture_nodes_for_cycles
    }
    return list(set(dispatch[type_]()))


def __get_objects():
    items = []
    for group in get_export_nodes():
        items.extend(group.objects)

    return items


def __get_geometry():
    items = []
    for object_ in get_type("objects"):
        if object_.type == "MESH" and not is_fakebone(object_):
            items.append(object_)

    return items


def __get_controllers():
    items = []
    for object_ in get_type("objects"):
        if not (is_bone_geometry(object_) or
                is_fakebone(object_)):
            if object_.parent is not None:
                if object_.parent.type == "ARMATURE":
                    items.append(object_.parent)

    return items


def __get_skins():
    items = []
    for object_ in get_type("objects"):
        if object_.type == "MESH":
            if not (is_bone_geometry(object_) or
                    is_fakebone(object_)):
                if object_.parent is not None:
                    if object_.parent.type == "ARMATURE":
                        items.append(object_)

    return items


def __get_fakebones():
    items = []
    for object_ in bpy.data.objects:
        if is_fakebone(object_):
            items.append(object_)

    return items


def __get_bone_geometry():
    items = []
    for object_ in get_type("objects"):
        if is_bone_geometry(object_):
            items.append(object_)

    return items


def __get_texture_nodes_for_cycles():
    cycles_nodes = []

    for material in get_type("materials"):
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if is_valid_cycles_texture_node(node):
                    cycles_nodes.append(node)

    return cycles_nodes


def __get_materials():
    items = []
    allowed = {"MESH"}
    for object_ in get_type("objects"):
        if object_.type in allowed:
            for material_slot in object_.material_slots:
                items.append(material_slot.material)

    return items


def __get_texture_slots():
    items = []
    for material in get_type("materials"):
        items.extend(get_texture_slots_for_material(material))

    return items


def __get_textures():
    items = []
    for texture_slot in get_type("texture_slots"):
        items.append(texture_slot.texture)

    return items


#------------------------------------------------------------------------------
# Textures:
#------------------------------------------------------------------------------

def get_texture_nodes_for_material(material):
    cycles_nodes = []

    if material.use_nodes:
        for node in material.node_tree.nodes:
            if is_valid_cycles_texture_node(node):
                cycles_nodes.append(node)

    return cycles_nodes


def get_texture_slots_for_material(material):
    texture_slots = []
    for texture_slot in material.texture_slots:
        if texture_slot and texture_slot.texture.type == 'IMAGE':
            texture_slots.append(texture_slot)

    validate_texture_slots(texture_slots)

    return texture_slots


def validate_texture_slots(texture_slots):
    texture_types = count_texture_types(texture_slots)
    raise_exception_if_textures_have_same_type(texture_types)


def count_texture_types(texture_slots):
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


def raise_exception_if_textures_have_same_type(texture_types):
    ERROR_TEMPLATE = "There is more than one texture of type {!r}."
    error_messages = []

    for type_name, type_count in texture_types.items():
        if type_count > 1:
            error_messages.append(ERROR_TEMPLATE.format(type_name.lower()))

    if error_messages:
        raise exceptions.CryBlendException(
            "\n".join(error_messages) +
            "\n" +
            "Please correct that and try again.")


def is_valid_image(image):
    return image.has_data and image.filepath


def is_valid_cycles_texture_node(node):
    ALLOWED_NODE_NAMES = ('Image Texture', 'Specular', 'Normal')
    if node.type == 'TEX_IMAGE' and node.name in ALLOWED_NODE_NAMES:
        if node.image:
            return True

    return False


def get_image_path_for_game(image, game_dir):
    if not game_dir or not os.path.isdir(game_dir):
        raise exceptions.NoGameDirectorySelected

    image_path = os.path.normpath(bpy.path.abspath(image.filepath))
    image_path = get_path_with_new_extension(image_path, "dds")
    image_path = os.path.relpath(image_path, game_dir)

    return image_path


#------------------------------------------------------------------------------
# Materials:
#------------------------------------------------------------------------------

def get_material_color(material, type_):
    color = 0.0
    alpha = 1.0

    if type_ == "emission":
        color = material.emit
    elif type_ == "ambient":
        color = material.ambient
    elif type_ == "diffuse":
        color = material.diffuse_color
        alpha = material.alpha
    elif type_ == "specular":
        color = material.specular_color

    col = color_to_string(color, alpha)
    return col


def get_material_attribute(material, type_):
    if type_ == "shininess":
        float = material.specular_hardness
    elif type_ == "index_refraction":
        float = material.alpha

    return str(float)


def get_material_parts(node, material):
    VALID_PHYSICS = ("physDefault", "physProxyNoDraw", "physNoCollide",
                     "physObstruct", "physNone")

    parts = material.split("__")
    count = len(parts)

    group = node
    index = 0
    name = material
    physics = "physDefault"

    if count == 1:
        # name
        index = 0
    elif count == 2:
        # XXX__name or name__phys
        if parts[1] not in VALID_PHYSICS:
            # XXX__name
            index = int(parts[0])
            name = parts[1]
        else:
            # name__phys
            name = parts[0]
            physics = parts[1]
    elif count == 3:
        # XXX__name__phys
        index = int(parts[0])
        name = parts[1]
        physics = parts[2]
    elif count == 4:
        # group__XXX__name__phys
        group = parts[0]
        index = int(parts[1])
        name = parts[2]
        physics = parts[3]

    name = replace_invalid_rc_characters(name)
    if physics not in VALID_PHYSICS:
        physics = "physDefault"

    return group, index, name, physics


def extract_cryblend_properties(materialname):
    """Returns the CryBlend properties of a materialname as dict or
    None if name is invalid.
    """
    if is_cryblend_material(materialname):
        groups = re.findall(
            "(.+)__([0-9]+)__(.*)__(phys[A-Za-z0-9]+)",
            materialname)
        properties = {}
        properties["ExportNode"] = groups[0][0]
        properties["Number"] = int(groups[0][1])
        properties["Name"] = groups[0][2]
        properties["Physics"] = groups[0][3]
        return properties
    return None


def is_cryblend_material(materialname):
    if re.search(".+__[0-9]+__.*__phys[A-Za-z0-9]+", materialname):
        return True
    else:
        return False


#------------------------------------------------------------------------------
# Export Nodes:
#------------------------------------------------------------------------------

def is_export_node(node):
    extensions = [".cgf", ".cga", ".chr", ".skin", ".anm", ".i_caf"]
    for extension in extensions:
        if node.name.endswith(extension):
            return True

    return False


def are_duplicate_nodes():
    node_names = []
    for group in get_export_nodes():
        node_names.append(get_node_name(group))
    unique_node_names = set(node_names)
    if len(unique_node_names) < len(node_names):
        return True


def get_node_name(node):
    node_type = get_node_type(node)
    return node.name[:-(len(node_type) + 1)]


def get_node_type(node):
    node_components = node.name.split(".")
    return node_components[-1]


def get_armature_node(object_):
    ALLOWED_NODE_TYPES = ("cga", "anm", "chr", "skin", "i_caf")
    for group in object_.users_group:
        if get_node_type(group) in ALLOWED_NODE_TYPES:
            return group


def is_visual_scene_node_writed(object_, group):
    if is_bone_geometry(object_):
        return False
    if object_.parent is not None and object_.type != 'MESH':
        return False

    return True


#------------------------------------------------------------------------------
# Fakebones:
#------------------------------------------------------------------------------

def get_fakebone(bone_name):
    return next((fakebone for fakebone in get_type("fakebones")
                 if fakebone.name == bone_name), None)


def is_fakebone(object_):
    if object_.get("fakebone") is not None:
        return True
    else:
        return False


def add_fakebones(group=None):
    '''Add helpers to track bone transforms.'''
    scene = bpy.context.scene
    remove_unused_meshes()

    if group:
        for object_ in group.objects:
            if object_.type == 'ARMATURE':
                armature = object_
    else:
        armature = get_armature()

    if armature is None:
        return

    skeleton = armature.data

    skeleton.pose_position = 'REST'
    time.sleep(0.5)

    scene.frame_set(scene.frame_start)
    for pose_bone in armature.pose.bones:
        bmatrix = pose_bone.bone.head_local
        bpy.ops.mesh.primitive_cube_add(radius=.01, location=bmatrix)
        fakebone = bpy.context.active_object
        fakebone.name = pose_bone.name
        fakebone["fakebone"] = "fakebone"
        scene.objects.active = armature
        armature.data.bones.active = pose_bone.bone
        bpy.ops.object.parent_set(type='BONE_RELATIVE')

        if group:
            group.objects.link(fakebone)

    if group:
        if get_node_type(group) == 'i_caf':
            process_animation(armature, skeleton)


def remove_fakebones():
    '''Select to remove all fakebones from the scene.'''
    if len(get_type("fakebones")) == 0:
        return
    old_mode = bpy.context.mode
    if old_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    deselect_all()
    for fakebone in get_type("fakebones"):
        fakebone.select = True
        bpy.ops.object.delete(use_global=False)
    if old_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode=old_mode)


#------------------------------------------------------------------------------
# Animation and Keyframing:
#------------------------------------------------------------------------------

def process_animation(armature, skeleton):
    '''Process animation to export.'''
    skeleton.pose_position = 'POSE'
    time.sleep(0.5)

    location_list, rotation_list = get_keyframes(armature)
    set_keyframes(armature, location_list, rotation_list)


def get_keyframes(armature):
    '''Get each bone location and rotation for each frame.'''
    location_list = []
    rotation_list = []

    for frame in range(
            bpy.context.scene.frame_start,
            bpy.context.scene.frame_end + 1):
        bpy.context.scene.frame_set(frame)

        locations = {}
        rotations = {}

        for bone in armature.pose.bones:
            fakeBone = bpy.data.objects[bone.name]

            if bone.parent and bone.parent.parent:
                parentMatrix = bpy.data.objects[
                    bone.parent.name].matrix_world

                animatrix = parentMatrix.inverted() * fakeBone.matrix_world
                lm, rm, sm = animatrix.decompose()
                locations[bone.name] = lm
                rotations[bone.name] = rm.to_euler()

            else:
                lm, rm, sm = fakeBone.matrix_world.decompose()
                locations[bone.name] = lm
                rotations[bone.name] = rm.to_euler()

        location_list.append(locations.copy())
        rotation_list.append(rotations.copy())

        del locations
        del rotations

    cbPrint("Keyframes have been appended to lists.")

    return location_list, rotation_list


def set_keyframes(armature, location_list, rotation_list):
    '''Insert each keyframe from lists.'''

    bpy.context.scene.frame_set(bpy.context.scene.frame_start)

    for frame in range(
            bpy.context.scene.frame_start,
            bpy.context.scene.frame_end + 1):
        set_keyframe(armature, frame, location_list, rotation_list)

    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
    cbPrint("Keyframes have been inserted to armature fakebones.")


def set_keyframe(armature, frame, location_list, rotation_list):
    '''Inset keyframe for current frame from lists.'''
    bpy.context.scene.frame_set(frame)

    for bone in armature.pose.bones:
        index = frame - bpy.context.scene.frame_start

        fakeBone = bpy.data.objects[bone.name]

        fakeBone.location = location_list[index][bone.name]
        fakeBone.rotation_euler = rotation_list[index][bone.name]

        fakeBone.keyframe_insert(data_path="location")
        fakeBone.keyframe_insert(data_path="rotation_euler")


def apply_animation_scale(armature):
    '''Apply Animation Scale.'''
    scene = bpy.context.scene
    remove_unused_meshes()

    if armature is None or armature.type != "ARMATURE":
        return

    skeleton = armature.data
    empties = []

    deselect_all()
    scene.frame_set(scene.frame_start)
    for pose_bone in armature.pose.bones:
        bmatrix = pose_bone.bone.head_local
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.1)
        empty = bpy.context.active_object
        empty.name = pose_bone.name

        bpy.ops.object.constraint_add(type='CHILD_OF')
        bpy.data.objects[empty.name].constraints[
            'Child Of'].use_scale_x = False
        bpy.data.objects[empty.name].constraints[
            'Child Of'].use_scale_y = False
        bpy.data.objects[empty.name].constraints[
            'Child Of'].use_scale_z = False

        bpy.data.objects[empty.name].constraints['Child Of'].target = armature
        bpy.data.objects[empty.name].constraints[
            'Child Of'].subtarget = pose_bone.name

        cbPrint("Baking animation on " + empty.name + "...")
        bpy.ops.nla.bake(
            frame_start=scene.frame_start,
            frame_end=scene.frame_end,
            step=1,
            only_selected=True,
            visual_keying=True,
            clear_constraints=True,
            clear_parents=False,
            bake_types={'OBJECT'})

        empties.append(empty)

    for empty in empties:
        empty.select = True

    cbPrint("Baked Animation successfully on empties.")
    deselect_all()

    set_active(armature)
    armature.select = True
    bpy.ops.anim.keyframe_clear_v3d()

    bpy.ops.object.transform_apply(rotation=True, scale=True)

    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.user_transforms_clear()

    for pose_bone in armature.pose.bones:
        pose_bone.constraints.new(type='COPY_LOCATION')
        pose_bone.constraints.new(type='COPY_ROTATION')

        for empty in empties:
            if empty.name == pose_bone.name:
                pose_bone.constraints['Copy Location'].target = empty
                pose_bone.constraints['Copy Rotation'].target = empty
                break

        pose_bone.bone.select = True

    cbPrint("Baking Animation on skeleton...")
    bpy.ops.nla.bake(
        frame_start=scene.frame_start,
        frame_end=scene.frame_end,
        step=1,
        only_selected=True,
        visual_keying=True,
        clear_constraints=True,
        clear_parents=False,
        bake_types={'POSE'})

    bpy.ops.object.mode_set(mode='OBJECT')

    deselect_all()

    cbPrint("Clearing empty data...")
    for empty in empties:
        empty.select = True

    bpy.ops.object.delete()

    cbPrint("Apply Animation was completed.")


def get_animation_id(group):
    node_type = get_node_type(group)
    node_name = get_node_name(group)

    return "{!s}-{!s}".format(node_name, node_name)

    # Now anm files produces with name as node_name_node_name.anm
    # after the process is done anm files are renmaed by rc.py to
    # cga_name_node_name.anm
    # In the future we may export directly correct name
    # with using below codes. But there is a prerequisite for that:
    # Dae have to be one main visual_node, others have to be in that main node
    # To achieve that we must change a bit visual_exporting process for anm.
    # Deficiency at that way process export nodes show as one at console.
    if node_type == 'i_caf':
        return "{!s}-{!s}".format(node_name, node_name)
    else:
        cga_node = find_cga_node_from_anm_node(group)
        if cga_node:
            cga_name = get_node_name(cga_node)
            return "{!s}-{!s}".format(node_name, cga_name)
        else:
            cga_name = group.objects[0].name
            return "{!s}-{!s}".format(node_name, cga_name)


def get_geometry_animation_file_name(group):
    node_type = get_node_type(group)
    node_name = get_node_name(group)

    cga_node = find_cga_node_from_anm_node(group)
    if cga_node:
        cga_name = get_node_name(cga_node)
        return "{!s}_{!s}.anm".format(cga_name, node_name)
    else:
        cga_name = group.objects[0].name
        return "{!s}_{!s}.anm".format(cga_name, node_name)


def find_cga_node_from_anm_node(anm_group):
    for object_ in anm_group.objects:
        for group in object_.users_group:
            if get_node_type(group) == 'cga':
                return group
    return None


#------------------------------------------------------------------------------
# Bone Geometry:
#------------------------------------------------------------------------------

def get_bone_geometry(bone_name):
    if bone_name.endswith("_Phys"):
        bone_name = bone_name[:-5]

    return bpy.data.objects.get("{}_boneGeometry".format(bone_name), None)


def is_bone_geometry(object_):
    if object_.type == "MESH" and object_.name.endswith("_boneGeometry"):
        return True
    else:
        return False


def is_physical(object_):
    if object_.name.endswith("_Phys"):
        return True
    else:
        return False


def physicalize(object_):
    object_.name = "{}_Phys".format(object_.name)


#------------------------------------------------------------------------------
# Skeleton:
#------------------------------------------------------------------------------

def get_root_bone(armature):
    for bone in get_bones(armature):
        if bone.parent is None:
            return bone


def count_root_bones(armature):
    count = 0
    for bone in get_bones(armature):
        if bone.parent is None:
            count += 1

    return count


def get_armature_for_object(object_):
    if object_.parent is not None:
        if object_.parent.type == "ARMATURE":
            return object_.parent


def get_armature():
    for object_ in get_type("controllers"):
        return object_


def get_bones(armature):
    return [bone for bone in armature.data.bones]


def get_animation_node_range(object_, node_name):
    try:
        start_frame = object_["{}_Start".format(node_name)]
        end_frame = object_["{}_End".format(node_name)]

        if isinstance(start_frame, str) and isinstance(end_frame, str):
            tm = bpy.context.scene.timeline_markers
            if tm.find(start_frame) != -1 and tm.find(end_frame) != -1:
                return tm[start_frame].frame, tm[end_frame].frame
            else:
                raise exceptions.MarkerNotFound
        else:
            return start_frame, end_frame
    except:
        return bpy.context.scene.frame_start, bpy.context.scene.frame_end


def get_armature_from_node(group):
    armature_count = 0
    armature = None
    for object_ in group.objects:
        if object_.type == "ARMATURE":
            armature_count += 1
            armature = object_

    if armature_count == 1:
        return armature

    error_message = None
    if armature_count == 0:
        raise exceptions.CryBlendException("i_caf node has no armature!")
        error_message = "i_caf node has no armature!"
    elif armature_count > 1:
        raise exceptions.CryBlendException(
            "{} i_caf node have more than one armature!".format(node_name))

    return None


#------------------------------------------------------------------------------
# General:
#------------------------------------------------------------------------------

def select_all():
    for object_ in bpy.data.objects:
        object_.select = True


def deselect_all():
    for object_ in bpy.data.objects:
        object_.select = False


def set_active(object_):
    bpy.context.scene.objects.active = object_


def get_object_children(parent):
    return [child for child in parent.children
            if child.type in {'ARMATURE', 'EMPTY', 'MESH'}]


def parent(children, parent):
    for object_ in children:
        object_.parent = parent

    return


def remove_unused_meshes():
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def get_bounding_box(object_):
    box = object_.bound_box
    vmin = Vector([box[0][0], box[0][1], box[0][2]])
    vmax = Vector([box[6][0], box[6][1], box[6][2]])

    return vmin[0], vmin[1], vmin[2], vmax[0], vmax[1], vmax[2]


#------------------------------------------------------------------------------
# Overriding Context:
#------------------------------------------------------------------------------

def get_3d_context(object_):
    window = bpy.context.window
    screen = window.screen
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area3d = area
            break
    for region in area3d.regions:
        if region.type == "WINDOW":
            region3d = region
            break
    override = {
        "window": window,
        "screen": screen,
        "area": area3d,
        "region": region3d,
        "object": object_
    }

    return override


#------------------------------------------------------------------------------
# Layer File:
#------------------------------------------------------------------------------

def get_guid():
    GUID = "{{}-{}-{}-{}-{}}".format(random_hex_sector(8),
                                     random_hex_sector(4),
                                     random_hex_sector(4),
                                     random_hex_sector(4),
                                     random_hex_sector(12))
    return GUID


def random_hex_sector(length):
    fixed_length_hex_format = "%0{}x".format(length)
    return fixed_length_hex_format % random.randrange(16 ** length)


#------------------------------------------------------------------------------
# Scripting:
#------------------------------------------------------------------------------

def generate_file_contents(type_):
    if type_ == "chrparams":
        return """<Params>\
<AnimationList>\
<Animation name="???" path="???.caf"/>\
</AnimationList>\
</Params>"""

    elif type_ == "cdf":
        return """<CharacterDefinition>\
<Model File="???.chr" Material="???"/>\
<AttachmentList>\
<Attachment Type="CA_BONE" AName="???" Rotation="1,0,0,0" Position="0,0,0" BoneName="???" Flags="0"/>\
<Attachment Type="CA_SKIN" AName="???" Binding="???.skin" Flags="0"/>\
</AttachmentList>\
<ShapeDeformation COL0="0" COL1="0" COL2="0" COL3="0" COL4="0" COL5="0" COL6="0" COL7="0"/>\
</CharacterDefinition>"""


def generate_file(filepath, contents, overwrite=False):
    if not os.path.exists(filepath) or overwrite:
        file = open(filepath, 'w')
        file.write(contents)
        file.close()


def generate_xml(filepath, contents, overwrite=False):
    if not os.path.exists(filepath) or overwrite:
        if isinstance(contents, str):
            script = parseString(contents)
        else:
            script = contents
        contents = script.toprettyxml(indent="    ")
        generate_file(filepath, contents, overwrite)


def remove_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)


#------------------------------------------------------------------------------
# Collada:
#------------------------------------------------------------------------------

def write_source(id_, type_, array, params):
    doc = Document()
    length = len(array)
    if type_ == "float4x4":
        stride = 16
    elif len(params) == 0:
        stride = 1
    else:
        stride = len(params)
    count = int(length / stride)

    source = doc.createElement("source")
    source.setAttribute("id", id_)

    if type_ == "float4x4":
        source_data = doc.createElement("float_array")
    else:
        source_data = doc.createElement("{!s}_array".format(type_))
    source_data.setAttribute("id", "{!s}-array".format(id_))
    source_data.setAttribute("count", str(length))
    try:
        source_data.appendChild(doc.createTextNode(floats_to_string(array)))
    except TypeError:
        source_data.appendChild(doc.createTextNode(strings_to_string(array)))
    technique_common = doc.createElement("technique_common")
    accessor = doc.createElement("accessor")
    accessor.setAttribute("source", "#{!s}-array".format(id_))
    accessor.setAttribute("count", str(count))
    accessor.setAttribute("stride", str(stride))
    for param in params:
        param_node = doc.createElement("param")
        param_node.setAttribute("name", param)
        param_node.setAttribute("type", type_)
        accessor.appendChild(param_node)
    if len(params) == 0:
        param_node = doc.createElement("param")
        param_node.setAttribute("type", type_)
        accessor.appendChild(param_node)
    technique_common.appendChild(accessor)

    source.appendChild(source_data)
    source.appendChild(technique_common)

    return source


def write_input(name, offset, type_, semantic):
    doc = Document()
    id_ = "{!s}-{!s}".format(name, type_)
    input = doc.createElement("input")

    if offset is not None:
        input.setAttribute("offset", str(offset))
    input.setAttribute("semantic", semantic)
    if semantic == "TEXCOORD":
        input.setAttribute("set", "0")
    input.setAttribute("source", "#{!s}".format(id_))

    return input


# this is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
