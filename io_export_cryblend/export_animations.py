#------------------------------------------------------------------------------
# Name:        export_animations.py
# Purpose:     Animation exporter to CryEngine
#
# Author:      Özkan Afacan,
#              Angelo J. Miner, Daniel White, David Marcelis, Duo Oratar,
#              Mikołaj Milej, Oscar Martin Garcia
#
# Created:     13/06/2016
# Copyright:   (c) Özkan Afacan 2016
# License:     GPLv2+
#------------------------------------------------------------------------------


if "bpy" in locals():
    import imp
    imp.reload(utils)
    imp.reload(exceptions)
else:
    import bpy
    from io_export_cryblend import export, utils, add, exceptions

from io_export_cryblend.rc import RCInstance
from io_export_cryblend.outpipe import cbPrint

from xml.dom.minidom import Document, Element, parse, parseString
import xml.dom.minidom
import os


AXES = {
    'X': 0,
    'Y': 1,
    'Z': 2,
}


class CrytekDaeAnimationExporter(export.CrytekDaeExporter):

    def __init__(self, config):
        self._config = config
        self._doc = Document()

    def export(self):
        self._prepare_for_export()

        root_element = self._doc.createElement('collada')
        root_element.setAttribute(
            "xmlns", "http://www.collada.org/2005/11/COLLADASchema")
        root_element.setAttribute("version", "1.4.1")
        self._doc.appendChild(root_element)
        self._create_file_header(root_element)

        libanmcl = self._doc.createElement("library_animation_clips")
        libanm = self._doc.createElement("library_animations")
        root_element.appendChild(libanmcl)
        root_element.appendChild(libanm)

        lib_visual_scene = self._doc.createElement("library_visual_scenes")
        visual_scene = self._doc.createElement("visual_scene")
        visual_scene.setAttribute("id", "scene")
        visual_scene.setAttribute("name", "scene")
        lib_visual_scene.appendChild(visual_scene)
        root_element.appendChild(lib_visual_scene)

        initial_frame_active = bpy.context.scene.frame_current
        initial_frame_start = bpy.context.scene.frame_start
        initial_frame_end = bpy.context.scene.frame_end

        ALLOWED_NODE_TYPES = ("i_caf", "anm")
        for group in utils.get_animation_export_nodes():

            node_type = utils.get_node_type(group)
            node_name = utils.get_node_name(group)

            if node_type in ALLOWED_NODE_TYPES:
                object_ = None

                if node_type == 'i_caf':
                    object_ = utils.get_armature_from_node(group)
                elif node_type == 'anm':
                    object_ = group.objects[0]

                frame_start, frame_end = utils.get_animation_node_range(
                    object_, node_name)
                bpy.context.scene.frame_start = frame_start
                bpy.context.scene.frame_end = frame_end

                print('')
                cbPrint(group.name)
                cbPrint("Animation is being preparing to process.")
                cbPrint("Animation frame range are [{} - {}]".format(
                    frame_start, frame_end))

                if node_type == 'i_caf':
                    utils.add_fakebones(group)
                try:
                    self._export_library_animation_clips_and_animations(
                        libanmcl, libanm, group)
                    self._export_library_visual_scenes(visual_scene, group)
                except RuntimeError:
                    pass
                finally:
                    if node_type == 'i_caf':
                        utils.remove_fakebones()

                    cbPrint("Animation has been processed.")

        bpy.context.scene.frame_current = initial_frame_active
        bpy.context.scene.frame_start = initial_frame_start
        bpy.context.scene.frame_end = initial_frame_end
        print('')

        self._export_scene(root_element)

        converter = RCInstance(self._config)
        converter.convert_dae(self._doc)

    def _prepare_for_export(self):
        utils.clean_file()


# -----------------------------------------------------------------------------
# Library Animations and Clips: --> Animations, F-Curves
# -----------------------------------------------------------------------------

    def _export_library_animation_clips_and_animations(
            self, libanmcl, libanm, group):

        scene = bpy.context.scene
        anim_id = utils.get_animation_id(group)

        animation_clip = self._doc.createElement("animation_clip")
        animation_clip.setAttribute("id", anim_id)
        animation_clip.setAttribute("start", "{:f}".format(
            utils.frame_to_time(scene.frame_start)))
        animation_clip.setAttribute("end", "{:f}".format(
            utils.frame_to_time(scene.frame_end)))
        is_animation = False

        for object_ in group.objects:
            if (object_.type != 'ARMATURE' and object_.animation_data and
                    object_.animation_data.action):

                is_animation = True

                props_name = self._create_properties_name(object_, group)
                bone_name = "{!s}{!s}".format(object_.name, props_name)

                for axis in iter(AXES):
                    animation = self._get_animation_location(
                        object_, bone_name, axis, anim_id)
                    if animation is not None:
                        libanm.appendChild(animation)

                for axis in iter(AXES):
                    animation = self._get_animation_rotation(
                        object_, bone_name, axis, anim_id)
                    if animation is not None:
                        libanm.appendChild(animation)

                self._export_instance_animation_parameters(
                    object_, animation_clip, anim_id)

        if is_animation:
            libanmcl.appendChild(animation_clip)

    def _export_instance_animation_parameters(
            self, object_, animation_clip, anim_id):
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
            self._export_instance_parameter(
                object_, animation_clip, "location", anim_id)
        if rotation_exists:
            self._export_instance_parameter(
                object_, animation_clip, "rotation_euler", anim_id)

    def _export_instance_parameter(
            self,
            object_,
            animation_clip,
            parameter,
            anim_id):
        for axis in iter(AXES):
            inst = self._doc.createElement("instance_animation")
            inst.setAttribute(
                "url", "#{!s}-{!s}_{!s}_{!s}".format(
                    anim_id, object_.name, parameter, axis))
            animation_clip.appendChild(inst)

    def _get_animation_location(self, object_, bone_name, axis, anim_id):
        attribute_type = "location"
        multiplier = 1
        target = "{!s}{!s}{!s}".format(bone_name, "/translation.", axis)

        animation_element = self._get_animation_attribute(object_,
                                                          axis,
                                                          attribute_type,
                                                          multiplier,
                                                          target,
                                                          anim_id)
        return animation_element

    def _get_animation_rotation(self, object_, bone_name, axis, anim_id):
        attribute_type = "rotation_euler"
        multiplier = utils.to_degrees
        target = "{!s}{!s}{!s}{!s}".format(bone_name,
                                           "/rotation_",
                                           axis,
                                           ".ANGLE")

        animation_element = self._get_animation_attribute(object_,
                                                          axis,
                                                          attribute_type,
                                                          multiplier,
                                                          target,
                                                          anim_id)
        return animation_element

    def _get_animation_attribute(self,
                                 object_,
                                 axis,
                                 attribute_type,
                                 multiplier,
                                 target,
                                 anim_id):
        id_prefix = "{!s}-{!s}_{!s}_{!s}".format(anim_id, object_.name,
                                                 attribute_type, axis)
        source_prefix = "#{!s}".format(id_prefix)

        for curve in object_.animation_data.action.fcurves:
            if (curve.data_path ==
                    attribute_type and curve.array_index == AXES[axis]):
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
                    sources["interpolation"].append(
                        keyframe_point.interpolation)
                    sources["intangent"].extend(
                        [utils.frame_to_time(khlx), khly])
                    sources["outangent"].extend(
                        [utils.frame_to_time(khrx), khry])

                animation_element = self._doc.createElement("animation")
                animation_element.setAttribute("id", id_prefix)

                for type_, data in sources.items():
                    anim_node = self._create_animation_node(
                        type_, data, id_prefix)
                    animation_element.appendChild(anim_node)

                sampler = self._create_sampler(id_prefix, source_prefix)
                channel = self._doc.createElement("channel")
                channel.setAttribute(
                    "source", "{!s}-sampler".format(source_prefix))
                channel.setAttribute("target", target)

                animation_element.appendChild(sampler)
                animation_element.appendChild(channel)

                return animation_element

    def _create_animation_node(self, type_, data, id_prefix):
        id_ = "{!s}-{!s}".format(id_prefix, type_)
        type_map = {
            "input": ["float", ["TIME"]],
            "output": ["float", ["VALUE"]],
            "intangent": ["float", "XY"],
            "outangent": ["float", "XY"],
            "interpolation": ["name", ["INTERPOLATION"]]
        }

        source = utils.write_source(
            id_, type_map[type_][0], data, type_map[type_][1])

        return source

    def _create_sampler(self, id_prefix, source_prefix):
        sampler = self._doc.createElement("sampler")
        sampler.setAttribute("id", "{!s}-sampler".format(id_prefix))

        input = self._doc.createElement("input")
        input.setAttribute("semantic", "INPUT")
        input.setAttribute("source", "{!s}-input".format(source_prefix))
        output = self._doc.createElement("input")
        output.setAttribute("semantic", "OUTPUT")
        output.setAttribute("source", "{!s}-output".format(source_prefix))
        interpolation = self._doc.createElement("input")
        interpolation.setAttribute("semantic", "INTERPOLATION")
        interpolation.setAttribute(
            "source", "{!s}-interpolation".format(source_prefix))
        intangent = self._doc.createElement("input")
        intangent.setAttribute("semantic", "IN_TANGENT")
        intangent.setAttribute(
            "source", "{!s}-intangent".format(source_prefix))
        outangent = self._doc.createElement("input")
        outangent.setAttribute("semantic", "OUT_TANGENT")
        outangent.setAttribute(
            "source", "{!s}-outangent".format(source_prefix))

        sampler.appendChild(input)
        sampler.appendChild(output)
        sampler.appendChild(interpolation)
        sampler.appendChild(intangent)
        sampler.appendChild(outangent)

        return sampler

# ---------------------------------------------------------------------
# Library Visual Scene: --> Skeleton and _Phys bones, Bone
#       Transformations, and Instance URL (_boneGeometry) and extras.
# ---------------------------------------------------------------------

    def _export_library_visual_scenes(self, visual_scene, group):

        if utils.get_animation_export_nodes():
            if utils.are_duplicate_nodes():
                message = "Duplicate Node Names"
                bpy.ops.screen.display_error('INVOKE_DEFAULT', message=message)

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

        node = self._write_visual_scene_node(group.objects, node, group)

        extra = self._create_cryengine_extra(group)
        node.appendChild(extra)
        visual_scene.appendChild(node)

    def _write_visual_scene_node(self, objects, parent_node, group):
        node_type = utils.get_node_type(group)
        for object_ in objects:
            if node_type == 'i_caf' and object_.type == 'ARMATURE':
                self._write_bone_list([utils.get_root_bone(
                    object_)], object_, parent_node, group)

            elif node_type == 'anm' and object_.type == 'MESH':
                prop_name = "{}{}".format(
                    object_.name, self._create_properties_name(
                        object_, group))
                node = self._doc.createElement("node")
                node.setAttribute("id", prop_name)
                node.setAttribute("name", prop_name)
                node.setIdAttribute("id")

                self._write_transforms(object_, node)

                extra = self._create_cryengine_extra(object_)
                if extra is not None:
                    node.appendChild(extra)

                parent_node.appendChild(node)

        return parent_node


# -------------------------------------------------------------------


def save(config):
    # prevent wasting time for exporting if RC was not found
    if not config.disable_rc and not os.path.isfile(config.rc_path):
        raise exceptions.NoRcSelectedException

    exporter = CrytekDaeAnimationExporter(config)
    exporter.export()


def register():
    bpy.utils.register_class(CrytekDaeAnimationExporter)

    bpy.utils.register_class(TriangulateMeError)
    bpy.utils.register_class(Error)


def unregister():
    bpy.utils.unregister_class(CrytekDaeAnimationExporter)
    bpy.utils.unregister_class(TriangulateMeError)
    bpy.utils.unregister_class(Error)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mesh.crytekdae('INVOKE_DEFAULT')
