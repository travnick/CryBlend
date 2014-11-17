#------------------------------------------------------------------------------
# Name:        utils.py
# Purpose:     Utility functions for use throughout the add-on
#
# Author:      Angelo J. Miner
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


from io_export_cryblend.outPipe import cbPrint
import bpy
import fnmatch
import math
import os
import random
import subprocess
import sys
import xml.dom.minidom


# globals
toDegrees = 180.0 / math.pi


def color_to_string(r, g, b, a):
    return "%s %s %s %s" % (r, g, b, a)


def convert_time(frx):
    fps_base = bpy.context.scene.render.fps_base
    fps = bpy.context.scene.render.fps
    return (fps_base * frx) / fps


# the following func is from
# http://ronrothman.com/
#    public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace/
# modified to use the current ver of shipped python
def fix_write_xml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
        writer.write(indent + "<" + self.tagName)
        attrs = self._get_attributes()
        for a_name in sorted(attrs.keys()):
            writer.write(" %s=\"" % a_name)
            xml.dom.minidom._write_data(writer, attrs[a_name].value)
            writer.write("\"")
        if self.childNodes:
            if (len(self.childNodes) == 1
                and self.childNodes[0].nodeType
                    == xml.dom.minidom.Node.TEXT_NODE):
                writer.write(">")
                self.childNodes[0].writexml(writer, "", "", "")
                writer.write("</%s>%s" % (self.tagName, newl))
                return
            writer.write(">%s" % (newl))
            for node in self.childNodes:
                node.writexml(writer, indent + addindent, addindent, newl)
            writer.write("%s</%s>%s" % (indent, self.tagName, newl))
        else:
            writer.write("/>%s" % (newl))


def get_guid():
    GUID = "{%s-%s-%s-%s-%s}" % (random_hex_sector(8),
                                 random_hex_sector(4),
                                 random_hex_sector(4),
                                 random_hex_sector(4),
                                 random_hex_sector(12))
    return GUID


def random_hex_sector(length):
    fixed_length_hex_format = "%0" + str(length) + "x"
    return fixed_length_hex_format % random.randrange(16 ** length)


# borrowed from obj exporter
# modified by angelo j miner
def veckey3d(v):
    return (round(v.x / 32767.0),
            round(v.y / 32767.0),
            round(v.z / 32767.0))


def veckey3d2(v):
    return (v.x,
            v.y,
            v.z)


def veckey3d21(v):
    return (round(v.x, 6),
            round(v.y, 6),
            round(v.z, 6))


def veckey3d3(vn, fn):
    facenorm = fn
    return (round((facenorm.x * vn.x) / 2),
            round((facenorm.y * vn.y) / 2),
            round((facenorm.z * vn.z) / 2))


def matrix_to_string(matrix):
    rows = []
    for row in matrix:
        rows.append(" ".join("%s" % column for column in row))

    return " ".join(rows)


def floats_to_string(floats, separator=" ", precision="%.6f"):
    return separator.join(precision % x for x in floats)


def get_absolute_path(file_path):
    [is_relative, file_path] = strip_blender_path_prefix(file_path)

    if is_relative:
        blend_file_path = os.path.dirname(bpy.data.filepath)
        file_path = "%s/%s" % (blend_file_path, file_path)

    return os.path.abspath(file_path)


def get_absolute_path_for_rc(file_path):
    # 'z:' is for wine (linux, mac) path
    # there should be better way to determine it
    WINE_DEFAULT_DRIVE_LETTER = "z:"

    file_path = get_absolute_path(file_path)

    if not sys.platform == 'win32':
        file_path = "%s%s" % (WINE_DEFAULT_DRIVE_LETTER, file_path)

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
    BLENDER_RELATIVE_PATH_PREFIX = "//"
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


def get_mtl_files_in_directory(directory):
    MTL_MATCH_STRING = "*.{!s}".format("mtl")

    mtl_files = []
    for file in os.listdir(directory):
        if fnmatch.fnmatch(file, MTL_MATCH_STRING):
            filepath = "{!s}/{!s}".format(directory, file)
            mtl_files.append(filepath)

    return mtl_files


def run_rc(rc_path, files_to_process, params=None):
    cbPrint(rc_path)
    process_params = [rc_path]

    if isinstance(files_to_process, list):
        process_params.extend(files_to_process)
    else:
        process_params.append(files_to_process)

    process_params.extend(params)

    cbPrint(params)
    cbPrint(files_to_process)

    try:
        run_object = subprocess.Popen(process_params)
    except:
        raise exceptions.NoRcSelectedException

    return run_object


def get_path_with_new_extension(image_path, extension):
    return "%s.%s" % (os.path.splitext(image_path)[0], extension)


def get_extension_from_path(image_path):
    return "%s" % (os.path.splitext(image_path)[1])


def add_fakebones():
    '''Add helpers to track bone transforms.'''
    for om in bpy.data.meshes:
        if om.users == 0:
            bpy.data.meshes.remove(om)

    for group in bpy.data.groups:
        if group.name.startswith("CryExportNode_"):
            for object_ in group.objects:
                if object_.type == "ARMATURE":
                    arm = object_
                    break

    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
    for pbone in arm.pose.bones:
        bmatrix = pbone.bone.head_local

        for object_ in bpy.context.selectable_objects:
            object_.select = False
        bpy.ops.mesh.primitive_cube_add(radius=.1, location=bmatrix)
        bpy.context.active_object.name = pbone.name

        for fb in bpy.context.scene.objects:
            if fb.name == pbone.name:
                fb["fakebone"] = "fakebone"
        bpy.context.scene.objects.active = arm
        arm.data.bones.active = pbone.bone
        bpy.ops.object.parent_set(type='BONE')

    keyframe_fakebones()


def remove_fakebones():
    '''Select to remove all fakebones from the scene.'''
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


def keyframe_fakebones():
    scene = bpy.context.scene
    location_list = []
    rotation_list = []
    keyframe_list = []
    armature = None
    for object_ in scene.objects:
        if (object_.type == "ARMATURE"):
            armature = object_
            break

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


def get_object_children(Parent):
    return [Object for Object in Parent.children
            if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}]


def negate_z_axis_of_matrix(matrix_local):
    for i in range(0, 3):
        matrix_local[i][3] = -matrix_local[i][3]


# this is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
