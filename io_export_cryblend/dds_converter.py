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
        cbPrint("ZZZZZZZZZZZZZZZ", "test")
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

            rc_process = utils.run_rc(self.__rc_exe,
                                      tiff_image_for_rc,
                                      rc_params)

            rc_process.wait()
            cbPrint("RC return code %s" % rc_process.returncode)

        if save_tiff:
            self.__save_tiffs()

        self.__remove_tmp_files()

    def __get_rc_params(self, refresh_rc, destination_path):
        rc_params = ["/verbose", "/threads=cores", "/userdialog=1"]
        if refresh_rc:
            rc_params.append("/refresh")

        image_directory = utils.get_texture_path()

        rc_params.append("/targetroot={!s}".format(image_directory))

        return rc_params

    def __get_temp_tiff_image_path(self, image):
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

def move_texture_to_project(images):
    for image in images:
        dds_old_path = utils.get_path_with_new_extension(image.filepath, "dds")
        dds_tail = os.path.split(dds_old_path)[1]
        dds_name = dds_tail[:-4]
        dds_new_path = bpy.path.ensure_ext("%s/%s/%s/%s/%s" % (utils.get_cry_root_path(), "Objects", utils.get_project_path(), "Textures", dds_name), ".dds")
        shutil.copy(dds_old_path, dds_new_path)
        os.remove(dds_old_path)
        cbPrint("ZZZZZZZZZZZZZZZ", "test")
        cbPrint(dds_old_path, "test")
        cbPrint(dds_new_path, "test")

# this is needed if you want to access more than the first def
if __name__ == "__main__":
    register()
