#------------------------------------------------------------------------------
# Name:        DdsConverter
# Purpose:     Converter to DDS
#
# Author:      Mikołaj Milej
#
# Created:     22/09/2013
# Copyright:   (c) Mikołaj Milej 2013
# Licence:     GPLv2+
#------------------------------------------------------------------------------


from io_export_cryblend import utils
from io_export_cryblend.outPipe import cbPrint
import os
import threading


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
        self.__tmp_images = []

    def __call__(self, images_to_convert, refresh_rc, save_tiff):
        SUCCESS = 0

        rc_params = ["/verbose", "/threads=cores", "/userdialog=1"]
        if refresh_rc:
            rc_params.append("/refresh")

        for image in images_to_convert:
            tiff_image_path = self.__get_temp_tiff_image_path(image)

            tiff_image_for_rc = utils.get_absolute_path_for_rc(tiff_image_path)

            rc_process = utils.run_rc(self.__rc_exe,
                                      tiff_image_for_rc,
                                      rc_params)

            return_code = rc_process.wait()

        if not save_tiff:
            self.__remove_tmp_files()

        self.__tmp_images.clear()

    def __get_temp_tiff_image_path(self, image):
        tiff_image_path = utils.get_path_with_new_extension(image.filepath,
                                                            "tif")

        tiff_saved = self.__save_as_tiff_if_not_already_tiff(image,
                                                             tiff_image_path)

        tiff_image_path = utils.get_absolute_path(tiff_image_path)

        if tiff_saved:
            self.__tmp_images.append(tiff_image_path)

        return tiff_image_path

    def __save_as_tiff_if_not_already_tiff(self, image, tiff_file_path):
        if image.filepath != tiff_file_path:
            originalPath = image.filepath

            try:
                image.filepath_raw = tiff_file_path
                image.file_format = 'TIFF'
                image.save()
            finally:
                image.filepath = originalPath

            return True

        else:
            return False

    def __remove_tmp_files(self):
        for image in self.__tmp_images:
            cbPrint("Removing tmp image: " + image)
            os.remove(image)
