# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os
import sys
import glob
import shutil

# Custom imports
from xmlcli import XmlCli as cli
from xmlcli import XmlCliLib as clb
from xmlcli.common.logger import log
from xmlcli import UefiFwParser as fwp


def automate_program_knobs(input_bios, config_dir, output_dir, new_major_ver="", new_minor_ver=""):
    """Function to perform the CvProgKnobs for multiple bios images using configuration file

    :param input_bios: absolute path to the folder contains bios images or absolute path to the bios file
    :param config_dir: absolute path to the folder contains bios knobs configuration file(.ini)
    :param output_dir: absolute path of the directory to store the output files
    :param new_major_ver: new major version for the file
    :param new_minor_ver: new minor version for the file
    """
    bios_knob_config_files = glob.glob(os.path.join(config_dir, "*.ini"))
    original_knobs_config = clb.KnobsIniFile
    input_bios_files = []
    if os.path.isdir(input_bios):
        input_bios_files = glob.glob(os.path.join(input_bios, "*.bin"))
    elif os.path.isfile(input_bios):
        input_bios_files = [input_bios]
    for KnobsIni in bios_knob_config_files:
        clb.KnobsIniFile = KnobsIni
        suffix_text = os.path.splitext(os.path.basename(KnobsIni))[0]
        for BiosBinFile in input_bios_files:
            log.info(f"Processing BIOS file = {BiosBinFile}")
            cli.CvProgKnobs(0, BiosBinFile, suffix_text, True)
            temp_file = clb.OutBinFile
            fwp.UpdateBiosId(clb.OutBinFile, new_major_ver, new_minor_ver)
            if clb.OutBinFile != "":
                shutil.move(clb.OutBinFile, output_dir)
            clb.RemoveFile(temp_file)
    clb.KnobsIniFile = original_knobs_config


if __name__ == "__main__":
    pass
