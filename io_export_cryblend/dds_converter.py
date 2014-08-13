#------------------------------------------------------------------------------
# Name:        dds_converter.py
# Purpose:     Image conversion to DDS
#
# Author:      Mikołaj Milej
#
# Created:     22/09/2013
# Copyright:   (c) Mikołaj Milej 2013
# Licence:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>


if "bpy" in locals():
    import imp
    imp.reload(utils)
else:
    import bpy
    from io_export_cryblend import utils

from io_export_cryblend.outPipe import cbPrint
import os
import shutil
import threading
import tempfile


class DdsConverterRunner:
    def __init__(self, rc_exe):
        self.__rc_exe = rc_exe

    def start_conversion(self, images_to_convert, refresh_rc, save_tiff):
        converter = _DdsConverter(self.__rc_exe)

        conversion_thread = threading.Thread(
            target=converter, args=(images_to_convert, refresh_rc, save_tiff)
        )
        conversion_thread.start()

        return conversion_thread


class _DdsConverter:
    def __init__(self, rc_exe):
        self.__rc_exe = rc_exe
        self.__tmp_images = {}
        self.__tmp_dir = tempfile.mkdtemp("CryBlend")

    def __call__(self, images_to_convert, refresh_rc, save_tiff):

        for image in images_to_convert:
            rc_params = self.__get_rc_params(refresh_rc, image.filepath)
            tiff_image_path = self.__get_temp_tiff_image_path(image)

            tiff_image_for_rc = utils.get_absolute_path_for_rc(tiff_image_path)

            try:
                create_normal_texture()
            except:
                cbPrint("Failed to invert green channel")

            rc_process = utils.run_rc(self.__rc_exe,
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

        if save_tiff:
            self.__save_tiffs()

        self.__remove_tmp_files()

    def create_normal_texture():
        if ("_ddn" in image.name):
            # make a copy to prevent editing the original image
            temp_normal_image = image.copy()
            self.__invert_green_channel(temp_normal_image)
            # save to file and delete the temporary image
            new_normal_image_path = "%s_cb_normal.%s" % (os.path.splitext(temp_normal_image.filepath_raw)[0], os.path.splitext(temp_normal_image.filepath_raw)[1])
            temp_normal_image.save_render(filepath=new_normal_image_path)
            bpy.data.images.remove(temp_normal_image)

    def __get_rc_params(self, refresh_rc, destination_path):
        rc_params = ["/verbose", "/threads=cores", "/userdialog=1"]
        if refresh_rc:
            rc_params.append("/refresh")

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
            cbPrint("Image {!r} is already a tif, not converting".format(image.name), 'debug')
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
