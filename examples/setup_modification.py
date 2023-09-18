# -*- coding: utf-8 -*-
"""
This file is example to demonstrate usage of XmlCli to modify Values specified
by user.

Aim: Have various function demonstrating example of usage for xmlcli to modify
setup option values in `ONLINE` mode. Intended to be executed on target platform

Pre-requisite:
1. Python Software (Python version 3.6 or above [64-bit])
2. XmlCli source code
3. Elevated Privilege [Execution access to run as administrator/root]

For the example we are taking setup options below:
------------------------------------|----------------
Setup Option                        | Possible Value
------------------------------------|----------------
CvfSupport                          |    0,1,2
MipiCam_ControlLogic0               |    0,1
MipiCam_ControlLogic1               |    0,1
MipiCam_Link0                       |    0,1
MipiCam_Link1                       |    0,1
MipiCam_Link1_SensorModel           |    0,1
MipiCam_Link1_DriverData_CrdVersion |    0x10, 0x20
------------------------------------|----------------
"""
__author__ = "Gahan Saraiya"

# Built-in imports
import sys

# Custom imports
# Importing API for xmlcli
from xmlcli import XmlCli as cli

KNOBS_TO_MODIFY = [
    "CvfSupport=1",
    "MipiCam_ControlLogic0=1",
    "MipiCam_ControlLogic1=1",
    "MipiCam_Link0=1",
    "MipiCam_Link1=1",
    "MipiCam_Link1_SensorModel=1",
    "MipiCam_Link1_DriverData_CrdVersion=0x20",
]


def simple_program_knobs_from_sut():
    """
    Simplest flow to read/program values
    :return:
    """
    from xmlcli import XmlCli as cli

    cli.clb._setCliAccess("linux")
    cli.clb.ConfXmlCli()
    cli.CvReadKnobs(", ".join(KNOBS_TO_MODIFY))  # read+verify
    cli.CvProgKnobs(", ".join(KNOBS_TO_MODIFY))  # modify
    _status = cli.CvReadKnobs(", ".join(KNOBS_TO_MODIFY))  # read+verify
    return _status


def program_knobs_from_sut(access_method="linux", knob_lis=None, config_file=None):
    """

    :param access_method:
              For linux:
                linux
              For more access method and choices, visit
    :param knob_lis: list of setup options to modify
          i.e. ["CvfSupport=1", "MipiCam_ControlLogic0=1"]
    :param config_file: absolute path to bios knobs configuration file to read knob and value
          i.e. refer `cfg/BiosKnobs.ini` under xmlcli source
    :return:
    """
    cli.clb._setCliAccess(access_method)  # on console one should see that the access method is correctly set.
    if cli.clb.InterfaceType != access_method:
        # validation to confirm interface is selected correctly
        # if failed to set interface the return from flow.
        return -1

    return_status = cli.clb.ConfXmlCli()
    if return_status == 0:  # XmlCli is supported and enabled.
        # Here we can perform our desire operation...
        if not knob_lis and not config_file:
            print("Please either provide knob list or config file")
            return -1
        if knob_lis:
            knobs = ", ".join(knob_lis)
            status = cli.CvReadKnobs(knobs)  # result can be observed in detail in log/console
            print(f"status of read: {status}")
            if status == 0:  # all values are set as expected, do nothing
                return status
            else:  # at least one knob is not having expected value
                status = cli.CvProgKnobs(knobs)
                if status != 0:  # unable to modify knobs
                    return status
                else:  # Verify the modification status
                    status = cli.CvReadKnobs(knobs)
                    if status == 0:  # success
                        print("Successfully modified and verified values")
                    else:
                        print("Write was successful but could not verify the value")
                return status
        elif config_file:
            cli.clb.KnobsIniFile = config_file
            status = cli.CvReadKnobs()  # result can be observed in detail in log/console
            print(f"status of read: {status}")
            if status == 0:  # all values are set as expected, do nothing
                return status
            else:  # at least one knob is not having expected value
                status = cli.CvProgKnobs()
                if status != 0:  # unable to modify knobs
                    return status
                else:  # Verify the modification status
                    status = cli.CvReadKnobs()
                    if status == 0:  # success
                        print("Successfully modified and verified values")
                    else:
                        print("Write was successful but could not verify the value")
                return status
    elif return_status == 2:  # Reboot requires
        print("RESTART SYSTEM")
        return return_status
    else:
        print("ERROR...")
        return -1


if __name__ == "__main__":
    # simple_program_knobs_from_sut()

    # METHOD 1: With Knobs list
    status = program_knobs_from_sut(access_method="linux", knob_lis=KNOBS_TO_MODIFY)  # [user-param]
    print(f"Execution status result={status}")

    # METHOD 2: With config file  [comment METHOD 1 and uncomment below line for METHOD 2]
    # status = program_knobs_from_sut(access_method="linux", config_file="BiosKnobs.ini")  # [user-param]
