#------------------------------------------------------------------------------
# Name:        rc.py
# Purpose:     Resource compiler transactions
#
# Author:      Daniel White,
#              Angelo J. Miner, David Marcelis, Duo Oratar, Mikołaj Milej,
#              Oscar Martin Garcia, Özkan Afacan
#
# Created:     2/12/2016
# Copyright:   (c) Daniel White 2016
# Licence:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>


if "bpy" in locals():
    import imp
    imp.reload(utils)
else:
    import bpy
    from io_export_cryblend import utils

from io_export_cryblend.outpipe import cbPrint
import fnmatch
import os
import shutil
import subprocess
import threading
import tempfile


class RCInstance:

    def __init__(self, config):
        self.__config = config

    def convert_tif(self, source):
        converter = _TIFConverter(self.__config, source)
        conversion_thread = threading.Thread(target=converter)
        conversion_thread.start()

    def convert_dae(self, source):
        converter = _DAEConverter(self.__config, source)
        conversion_thread = threading.Thread(target=converter)
        conversion_thread.start()


class _DAEConverter:

    def __init__(self, config, source):
        self.__config = config
        self.__doc = source

    def __call__(self):
        filepath = bpy.path.ensure_ext(self.__config.filepath, ".dae")
        utils.generate_xml(filepath, self.__doc, overwrite=True)

        dae_path = utils.get_absolute_path_for_rc(filepath)

        if not self.__config.disable_rc:
            rc_params = ["/verbose", "/threads=processors", "/refresh"]
            if self.__config.do_materials:
                rc_params.append("/createmtl=1")

            rc_process = run_rc(self.__config.rc_path, dae_path, rc_params)

            if rc_process is not None:
                rc_process.wait()
                self.__recompile(dae_path)
                self.__rename_anm_files(dae_path)

            if self.__config.do_materials:
                mtl_fix_thread = threading.Thread(
                    target=self.__fix_normalmap_in_mtls,
                    args=(rc_process, filepath)
                )
                mtl_fix_thread.start()

        if self.__config.make_layer:
            lyr_contents = self.__make_layer()
            lyr_path = os.path.splitext(filepath)[0] + ".lyr"
            utils.generate_file(lyr_path, lyr_contents)

        if not self.__config.save_dae:
            rcdone_path = "{}.rcdone".format(dae_path)
            utils.remove_file(dae_path)
            utils.remove_file(rcdone_path)

    def __recompile(self, dae_path):
        name = os.path.basename(dae_path)
        output_path = os.path.dirname(dae_path)
        ALLOWED_NODE_TYPES = ("chr", "skin")
        for group in utils.get_export_nodes():
            node_type = utils.get_node_type(group)
            if node_type in ALLOWED_NODE_TYPES:
                out_file = os.path.join(output_path, group.name)
                args = [
                    self.__config.rc_path,
                    "/refresh",
                    "/vertexindexformat=u16",
                    out_file]
                rc_second_pass = subprocess.Popen(args)
            elif node_type == 'i_caf':
                try:
                    os.remove(os.path.join(output_path, ".animsettings"))
                    os.remove(os.path.join(output_path, ".caf"))
                    os.remove(os.path.join(output_path, ".$animsettings"))
                except:
                    pass

    def __rename_anm_files(self, dae_path):
        output_path = os.path.dirname(dae_path)

        for group in utils.get_export_nodes():
            if utils.get_node_type(group) == 'anm':
                node_name = utils.get_node_name(group)
                src_name = "{}_{}".format(node_name, group.name)
                src_name = os.path.join(output_path, src_name)

                if os.path.exists(src_name):
                    dest_name = utils.get_geometry_animation_file_name(group)
                    dest_name = os.path.join(output_path, dest_name)

                    if os.path.exists(dest_name):
                        os.remove(dest_name)

                    os.rename(src_name, dest_name)

    def __fix_normalmap_in_mtls(self, rc_process, dae_file):
        SUCCESS = 0

        return_code = rc_process.wait()

        if return_code == SUCCESS:
            export_directory = os.path.dirname(dae_file)

            mtl_files = self.__get_mtl_files_in_directory(export_directory)

            for mtl_file_name in mtl_files:
                self.__fix_normalmap_in_mtl(mtl_file_name)

    def __get_mtl_files_in_directory(self, directory):
        MTL_MATCH_STRING = "*.{!s}".format("mtl")

        mtl_files = []
        for file in os.listdir(directory):
            if fnmatch.fnmatch(file, MTL_MATCH_STRING):
                filepath = "{!s}/{!s}".format(directory, file)
                mtl_files.append(filepath)

        return mtl_files

    def __fix_normalmap_in_mtl(self, mtl_file_name):
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

    def __make_layer(self):
        layer_doc = Document()
        object_layer = layer_doc.createElement("ObjectLayer")
        layer_name = "ExportedLayer"
        layer = createAttributes(
            'Layer',
            {'name': layer_name,
             'GUID': utils.get_guid(),
             'FullName': layer_name,
             'External': '0',
             'Exportable': '1',
             'ExportLayerPak': '1',
             'DefaultLoaded': '0',
             'HavePhysics': '1',
             'Expanded': '0',
             'IsDefaultColor': '1'
             }
        )

        layer_objects = layer_doc.createElement("LayerObjects")
        for group in utils.get_export_nodes():
            if len(group.objects) > 1:
                origin = 0, 0, 0
                rotation = 1, 0, 0, 0
            else:
                origin = group.objects[0].location
                rotation = group.objects[0].delta_rotation_quaternion

            object = createAttributes(
                'Object',
                {'name': group.name[14:],
                 'Type': 'Entity',
                 'Id': utils.get_guid(),
                 'LayerGUID': layer.getAttribute('GUID'),
                 'Layer': layer_name,
                 'Pos': "{}, {}, {}".format(origin[:]),
                 'Rotate': "{}, {}, {}, {}".format(rotation[:]),
                 'EntityClass': 'BasicEntity',
                 'FloorNumber': '-1',
                 'RenderNearest': '0',
                 'NoStaticDecals': '0',
                 'CreatedThroughPool': '0',
                 'MatLayersMask': '0',
                 'OutdoorOnly': '0',
                 'CastShadow': '1',
                 'MotionBlurMultiplier': '1',
                 'LodRatio': '100',
                 'ViewDistRatio': '100',
                 'HiddenInGame': '0',
                 }
            )
            properties = createAttributes(
                'Properties',
                {'object_Model': '/Objects/{}.cgf'.format(group.name[14:]),
                 'bCanTriggerAreas': '0',
                 'bExcludeCover': '0',
                 'DmgFactorWhenCollidingAI': '1',
                 'esFaction': '',
                 'bHeavyObject': '0',
                 'bInteractLargeObject': '0',
                 'bMissionCritical': '0',
                 'bPickable': '0',
                 'soclasses_SmartObjectClass': '',
                 'bUsable': '0',
                 'UseMessage': '0',
                 }
            )
            health = createAttributes(
                'Health',
                {'bInvulnerable': '1',
                 'MaxHealth': '500',
                 'bOnlyEnemyFire': '1',
                 }
            )
            interest = createAttributes(
                'Interest',
                {'soaction_Action': '',
                 'bInteresting': '0',
                 'InterestLevel': '1',
                 'Pause': '15',
                 'Radius': '20',
                 'bShared': '0',
                 }
            )
            vOffset = createAttributes(
                'vOffset',
                {'x': '0',
                 'y': '0',
                 'z': '0',
                 }
            )

            interest.appendChild(vOffset)
            properties.appendChild(health)
            properties.appendChild(interest)
            object.appendChild(properties)
            layer_objects.appendChild(object)

        layer.appendChild(layer_objects)
        object_layer.appendChild(layer)
        layer_doc.appendChild(object_layer)

        return layer_doc.toprettyxml(indent="    ")

        def __createAttributes(self, node_name, attributes):
            doc = Document()
            node = doc.createElement(node_name)
            for name, value in attributes.items():
                node.setAttribute(name, value)

            return node


class _TIFConverter:

    def __init__(self, config, source):
        self.__config = config
        self.__images_to_convert = source
        self.__tmp_images = {}
        self.__tmp_dir = tempfile.mkdtemp("CryBlend")

    def __call__(self):
        for image in self.__images_to_convert:
            rc_params = self.__get_rc_params(image.filepath)
            tiff_image_path = self.__get_temp_tiff_image_path(image)

            tiff_image_for_rc = utils.get_absolute_path_for_rc(tiff_image_path)
            cbPrint(tiff_image_for_rc)

            try:
                self.__create_normal_texture()
            except:
                cbPrint("Failed to invert green channel")

            rc_process = run_rc(self.__config.texture_rc_path,
                                tiff_image_for_rc,
                                rc_params)

            # re-save the original image after running the RC to
            # prevent the original one from getting lost
            try:
                if ("_ddn" in image.name):
                    image.save()
            except:
                cbPrint("Failed to invert green channel")

            rc_process.wait()

        if self.__config.texture_rc_path:
            self.__save_tiffs()

        self.__remove_tmp_files()

    def __create_normal_texture(self):
        if ("_ddn" in image.name):
            # make a copy to prevent editing the original image
            temp_normal_image = image.copy()
            self.__invert_green_channel(temp_normal_image)
            # save to file and delete the temporary image
            new_normal_image_path = "{}_cb_normal.{}".format(os.path.splitext(
                temp_normal_image.filepath_raw)[0],
                os.path.splitext(
                temp_normal_image.filepath_raw)[1])
            temp_normal_image.save_render(filepath=new_normal_image_path)
            bpy.data.images.remove(temp_normal_image)

    def __get_rc_params(self, destination_path):
        rc_params = ["/verbose", "/threads=cores", "/userdialog=1", "/refresh"]

        image_directory = os.path.dirname(utils.get_absolute_path_for_rc(
            destination_path))

        rc_params.append("/targetroot={!s}".format(image_directory))

        return rc_params

    def __invert_green_channel(self, image):
        override = {'edit_image': bpy.data.images[image.name]}
        bpy.ops.image.invert(override, invert_g=True)
        image.update()

    def __get_temp_tiff_image_path(self, image):
        # check if the image already is a .tif
        image_extension = utils.get_extension_from_path(image.filepath)
        cbPrint(image_extension)

        if ".tif" == image_extension:
            cbPrint(
                "Image {!r} is already a tif, not converting".format(
                    image.name), 'debug')
            return image.filepath

        tiff_image_path = utils.get_path_with_new_extension(image.filepath,
                                                            "tif")
        tiff_image_absolute_path = utils.get_absolute_path(tiff_image_path)
        tiff_file_name = os.path.basename(tiff_image_path)

        tmp_file_path = os.path.join(self.__tmp_dir, tiff_file_name)

        if tiff_image_path != image.filepath:
            self.__save_as_tiff(image, tmp_file_path)
            self.__tmp_images[tmp_file_path] = (tiff_image_absolute_path)

        return tmp_file_path

    def __save_as_tiff(self, image, tiff_file_path):
        originalPath = image.filepath

        try:
            image.filepath_raw = tiff_file_path
            image.file_format = 'TIFF'
            image.save()

        finally:
            image.filepath = originalPath

    def __save_tiffs(self):
        for tmp_image, dest_image in self.__tmp_images.items():
            cbPrint("Moving tmp image: {!r} to {!r}".format(tmp_image,
                                                            dest_image),
                    'debug')
            shutil.move(tmp_image, dest_image)

    def __remove_tmp_files(self):
        for tmp_image in self.__tmp_images:
            try:
                cbPrint("Removing tmp image: {!r}".format(tmp_image), 'debug')
                os.remove(tmp_image)
            except FileNotFoundError:
                pass

        os.removedirs(self.__tmp_dir)
        self.__tmp_images.clear()


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
