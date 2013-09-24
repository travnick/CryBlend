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
import tempfile


class DdsConverterRunner:
    def __init__(self, rc_exe):
        self.__rc_exe = rc_exe

    def start_conversion(self, images_to_convert, refresh_rc):
        converter = _DdsConverter(self.__rc_exe)

        conversion_thread = threading.Thread(
            target=converter, args=(images_to_convert, refresh_rc)
        )
        conversion_thread.start()

        return conversion_thread


class _DdsConverter:
    def __init__(self, rc_exe):
        self.__rc_exe = rc_exe
        self.__tmp_images = []

    def __call__(self, images_to_convert, refresh_rc):
        SUCCESS = 0

        rc_params = ["/verbose", "/threads=cores", "/userdialog=1"]
        if refresh_rc:
            rc_params.append("/refresh")

        for image in images_to_convert:
            tiff_image = self.__get_tiff_image(image)

            self.__tmp_images.append(tiff_image)

            tiff_image_for_rc = utils.get_absolute_path_for_rc(tiff_image)

            rc_process = utils.run_rc(self.__rc_exe,
                                      tiff_image_for_rc,
                                      rc_params)

            return_code = rc_process.wait()

        self.__remove_tmp_files()

    def __get_tiff_image(self, image):
        tiff_file_path = utils.get_path_with_new_extension(image.filepath,
                                                           "tif")

        self.__save_as_tiff(image, tiff_file_path)

        return utils.get_absolute_path(tiff_file_path)

    def __save_as_tiff(self, image, tiff_file_path):
        if image.file_format is not 'TIFF':
            originalPath = image.filepath

            try:
                image.filepath_raw = tiff_file_path
                image.file_format = 'TIFF'
                image.save()
            finally:
                image.filepath = originalPath

    def __remove_tmp_files(self):
        for image in self.__tmp_images:
            cbPrint("Removing tmp image: " + image)
            os.remove(image)

        self.__tmp_images.clear()
