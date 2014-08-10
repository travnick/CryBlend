#------------------------------------------------------------------------------
# Name:        configuration.py
# Purpose:     Storing CryBlend configuration settings
#
# Author:      Mikołaj Milej
#
# Created:     02/10/2013
# Copyright:   (c) Mikołaj Milej 2013
# Licence:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>


import bpy
from io_export_cryblend.outPipe import cbPrint
import os
import pickle


class __Configuration:
    __CONFIG_PATH = bpy.utils.user_resource("CONFIG",
                                            path="scripts",
                                            create=True)
    __CONFIG_FILENAME = "cryblend.cfg"
    __CONFIG_FILEPATH = os.path.join(__CONFIG_PATH, __CONFIG_FILENAME)
    __DEFAULT_CONFIGURATION = {"RC_LOCATION": r"",
                              "RC_FOR_TEXTURES_CONVERSION": r"",
                              "merge_anm": r"",
                              "donot_merge": r"",
                              "avg_pface": r"",
                              "run_rc": r"",
                              "do_materials": r"",
                              "convert_source_image_to_dds": r"",
                              "save_tiff_during_conversion": r"",
                              "refresh_rc": r"",
                              "include_ik": r"",
                              "correct_weight": r"",
                              "make_layer": r"",
                              "run_in_profiler": r""}

    def __init__(self):
        self.__CONFIG = self.__load({})

# rc_path:
    @property
    def rc_path(self):
        return self.__CONFIG["RC_LOCATION"]

    @rc_path.setter
    def rc_path(self, value):
        self.__CONFIG["RC_LOCATION"] = value

# rc_for_texture_conversion_path:
    @property
    def rc_for_texture_conversion_path(self):
        if (not self.__CONFIG["RC_FOR_TEXTURES_CONVERSION"]):
            return self.rc_path

        return self.__CONFIG["RC_FOR_TEXTURES_CONVERSION"]

    @rc_for_texture_conversion_path.setter
    def rc_for_texture_conversion_path(self, value):
        self.__CONFIG["RC_FOR_TEXTURES_CONVERSION"] = value

# merge_anm:
    @property
    def merge_anm(self):
        return self.__CONFIG["merge_anm"]

    @merge_anm.setter
    def merge_anm(self, value):
        self.__CONFIG["merge_anm"] = value

# donot_merge:
    @property
    def donot_merge(self):
        return self.__CONFIG["donot_merge"]

    @donot_merge.setter
    def donot_merge(self, value):
        self.__CONFIG["donot_merge"] = value

# avg_pface:
    @property
    def avg_pface(self):
        return self.__CONFIG["avg_pface"]

    @avg_pface.setter
    def avg_pface(self, value):
        self.__CONFIG["avg_pface"] = value

# run_rc:
    @property
    def run_rc(self):
        return self.__CONFIG["run_rc"]

    @run_rc.setter
    def run_rc(self, value):
        self.__CONFIG["run_rc"] = value

# do_materials:
    @property
    def do_materials(self):
        return self.__CONFIG["do_materials"]

    @do_materials.setter
    def do_materials(self, value):
        self.__CONFIG["do_materials"] = value

# convert_source_image_to_dds:
    @property
    def convert_source_image_to_dds(self):
        return self.__CONFIG["convert_source_image_to_dds"]

    @convert_source_image_to_dds.setter
    def convert_source_image_to_dds(self, value):
        self.__CONFIG["convert_source_image_to_dds"] = value

# save_tiff_during_conversion:
    @property
    def save_tiff_during_conversion(self):
        return self.__CONFIG["save_tiff_during_conversion"]

    @save_tiff_during_conversion.setter
    def save_tiff_during_conversion(self, value):
        self.__CONFIG["save_tiff_during_conversion"] = value

# refresh_rc:
    @property
    def refresh_rc(self):
        return self.__CONFIG["refresh_rc"]

    @refresh_rc.setter
    def refresh_rc(self, value):
        self.__CONFIG["refresh_rc"] = value

# include_ik:
    @property
    def include_ik(self):
        return self.__CONFIG["include_ik"]

    @include_ik.setter
    def include_ik(self, value):
        self.__CONFIG["include_ik"] = value

# correct_weight:
    @property
    def correct_weight(self):
        return self.__CONFIG["correct_weight"]

    @correct_weight.setter
    def correct_weight(self, value):
        self.__CONFIG["correct_weight"] = value

# make_layer:
    @property
    def make_layer(self):
        return self.__CONFIG["make_layer"]

    @make_layer.setter
    def make_layer(self, value):
        self.__CONFIG["make_layer"] = value

# run_in_profiler:
    @property
    def run_in_profiler(self):
        return self.__CONFIG["run_in_profiler"]

    @run_in_profiler.setter
    def run_in_profiler(self, value):
        self.__CONFIG["run_in_profiler"] = value

    def save(self):
        cbPrint("Saving configuration file.", "debug")

        if os.path.isdir(self.__CONFIG_PATH):
            try:
                with open(self.__CONFIG_FILEPATH, "wb") as f:
                    pickle.dump(self.__CONFIG, f, -1)
                    cbPrint("Configuration file saved.")

                cbPrint("Saved %s" % self.__CONFIG_FILEPATH)

            except:
                cbPrint("[IO] can not write: %s" % self.__CONFIG_FILEPATH,
                        "error")

        else:
            cbPrint("Configuration file path is missing %s"
                    % self.__CONFIG_PATH,
                    "error")

    def __load(self, current_configuration):
        new_configuration = {}
        new_configuration.update(self.__DEFAULT_CONFIGURATION)
        new_configuration.update(current_configuration)

        if os.path.isfile(self.__CONFIG_FILEPATH):
            try:
                with open(self.__CONFIG_FILEPATH, "rb") as f:
                    new_configuration.update(pickle.load(f))
                    cbPrint("Configuration file loaded.")
            except:
                cbPrint("[IO] can not read: %s" % self.__CONFIG_FILEPATH,
                        "error")

        return new_configuration


Configuration = __Configuration()
