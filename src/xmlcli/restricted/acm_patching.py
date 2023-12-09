# -*- coding: utf-8 -*-
import os
import ctypes

from . import structure_restricted
from ..common.logger import log
from ..common import structure
from ..common import utils
from ..common import configurations


__all__ = ["Acm", "ProcessAcm"]

FIT_TYPE = 0x02  # FIT Type = 0x02 for Startup ACM Entry in the FIT table
ACM_GUID = "7fc03aaa-46a7-18db-2eac698f8d417f5a"
DEFAULT_ACM_SIZE = 0x40000

# Dictionary for ACM HeaderVersion and corresponding ACM GUID offset
ACM_GUID_OFFSET = {
  0x0: 0x4C0,  # For Header version 0.0 ACM GUID will be at offset 0x4C0 from ACM header
  0x30000: 0x6C0,  # For Header version 3.0 ACM GUID will be at offset 0x4C0 from ACM header
  0x40000: 0x1C80  # For Header version 4.0 ACM GUID will be at offset 0x4C0 from ACM header
}
table_header = ["HeaderVersion", "ModuleSubType", "ChipsetID", "Flags", "ModuleVendor", "dd.mm.yyyy", "Size",
                "Version"]


def get_fit_header(binary_image, bios_start_address=0, bios_end_address=None):
  """Function to get Firmware Interface Table (FIT) header content and Firmware Interface Table offset

  :param binary_image: IFWI/BIOS binary
  :return: function will return FIT header and FIT offset if the FIT table is valid
  """
  if not bios_end_address:
    bios_end_address = len(binary_image)
  fit_address = ctypes.c_uint32.from_buffer(binary_image, bios_end_address + structure.FitEntry.FIT_OFFSET)
  bios_size= bios_end_address-bios_start_address
  fit_offset = bios_start_address + (fit_address.value & (bios_size - 1))
  buffer = utils.get_buffer(binary_image)
  buffer.seek(fit_offset)
  fit_header = structure.FitEntry.read_from(buffer)
  if structure.FitEntry.FIT_SIGNATURE != utils.convert_to_bytes(fit_header.Address):
    log.error("Cannot find FIT table!")
    return False
  return fit_header, fit_offset


def display_acm_details(acm_bin, acm_offset):
  """Function to display the ACM related information

  :param acm_bin: Startup ACM binary
  :param acm_offset : Startup ACM header offset in the IFWI/BIOS binary
  :return: None
  """

  acm_bin = utils.get_buffer(acm_bin)
  acm_bin.seek(acm_offset)
  acm_header_info = structure_restricted.AcmHeader.read_from(acm_bin)
  acm_header_values = acm_header_info.get_value_list  # Get ACM related information in a list

  if acm_header_info.HeaderVersion in ACM_GUID_OFFSET:
    offset = acm_offset + ACM_GUID_OFFSET.get(acm_header_info.HeaderVersion)
    acm_bin.seek(offset)
    acm_header_values.append(structure_restricted.AcmGuidStructure.read_from(acm_bin).get_version_str)
    log.result(utils.Table().create_table(header=table_header, data=acm_header_values, width=0))


class Acm(object):
  """This class provides various utilities and operation to be performed on Acm
  on given BIOS
  """
  def __init__(self, binary_file):
    self.binary_file = binary_file
    with open(self.binary_file, 'rb') as binary_file:
      # self.binary is IFWI/BIOS binary
      self.binary = bytearray(binary_file.read())
    self.descriptor_data = None

  def is_binary_valid(self):
    """Function to check if IFWI/BIOS file is valid or not.

    :return: True if IFWI/BIOS is valid else False
    """
    if structure.is_ifwi(self.binary):
      self.descriptor_data = structure.DescriptorRegion.read_from(self.binary)
      return True
    if structure.is_bios(self.binary):
      return True
    else:
      log.error("The IFWI/BIOS given is not Valid")

  def get_acm_entries(self):
    """Function to get All the Startup ACM (type 2) entries offset

    :return : Returns a list which contains Startup ACM offset
    """
    startup_acm = []
    if self.descriptor_data:
      bios_start_address = self.descriptor_data.bios_address
      bios_end_address = self.descriptor_data.bios_end_address+1
    else:
      bios_start_address = 0x0
      bios_end_address = len(self.binary)
    fit_header, fit_offset = get_fit_header(self.binary, bios_start_address, bios_end_address)
    fit = structure.FitEntry()
    binary = utils.get_buffer(self.binary)
    for idx in range(fit_header.Size):  # fit_header.Size is equal to number of FIT Entries
      binary.seek(fit_offset + (idx + 1) * fit.cls_size)
      fit_entry = structure.FitEntry.read_from(binary)
      if fit_entry.Type == FIT_TYPE:
        img_base = utils.MEMORY_SIZE - bios_end_address
        acm_offset = fit_entry.Address - img_base
        startup_acm.append(acm_offset)
      elif fit_entry.Type > FIT_TYPE:
        break
    return startup_acm

  def save_binary(self, binary_buffer, output_path):
    """Function to save the binary file

    :param binary_buffer: binary content
    :param output_path: Path to save the binary file
    :return: True if the file creation is successful
    """
    with open(output_path, 'wb') as acm_file:
      acm_file.write(binary_buffer)
      return True

  def create_acm_patched_binary(self, startup_acm_bin, acm_header):
    """Function to create a new acm patched binary file

    :param startup_acm_bin : input Startup ACM binary
    :param acm_header : Startup ACM offset
    :return: ACM patched binary
    """

    self.binary[acm_header:acm_header + len(bytearray(startup_acm_bin))] = bytearray(startup_acm_bin)
    return self.binary

  def get_patch_offset(self, acm_header, startup_acm_bin, criteria):
    """Function to check if Header Version, chipset ID and ACM_GUID are matching

    :param acm_header: ACM header offset
    :param startup_acm_bin : Startup ACM binary
    :param criteria: Elements to be matched for patching
    :return: will return patch offset if both ACM binary are valid else False
    """

    bios_bin = utils.get_buffer(self.binary)
    bios_bin.seek(acm_header)
    startup_acm_bin = utils.get_buffer(startup_acm_bin)
    bios_acm = structure_restricted.AcmHeader.read_from(bios_bin)
    input_acm = structure_restricted.AcmHeader.read_from(startup_acm_bin)

    # Comparing both HeaderVersion and Chipset ID
    if bios_acm.HeaderVersion in ACM_GUID_OFFSET and all(
      (getattr(bios_acm, match_criteria) == getattr(input_acm, match_criteria) for match_criteria in criteria)):
      acm_guid_offset = acm_header + ACM_GUID_OFFSET.get(bios_acm.HeaderVersion)
      input_acm_guid_offset = ACM_GUID_OFFSET.get(bios_acm.HeaderVersion)
      bios_bin.seek(acm_guid_offset)
      startup_acm_bin.seek(input_acm_guid_offset)
      acm_guid = structure_restricted.AcmGuidStructure.read_from(bios_bin)
      input_sacm_guid = structure_restricted.AcmGuidStructure.read_from(startup_acm_bin)
      if (str(acm_guid.AcmGuid) == ACM_GUID == str(
        input_sacm_guid.AcmGuid)) and acm_guid.get_version_str == input_sacm_guid.get_version_str:
        log.debug(f"Version of ACM at offset {hex(acm_header)} in the IFWI/BIOS is = {acm_guid.get_version_str}")
        log.debug(f"Version of input ACM binary = {input_sacm_guid.get_version_str}")
        return 1
      elif (str(acm_guid.AcmGuid) == ACM_GUID == str(
        input_sacm_guid.AcmGuid)) and acm_guid.get_version_str != input_sacm_guid.get_version_str:
        log.debug(f"Version of ACM at offset {hex(acm_header)} in the IFWI/BIOS is = {acm_guid.get_version_str}")
        log.debug(f"Version of input ACM binary = {input_sacm_guid.get_version_str}")
        return acm_header

  def acm_read(self, output_path):
    """Function to read the Start up ACM information and extract Startup ACM Binary

    :param output_path : Path to store the Extracted ACM binary
    :return: Will provide the ACM related information and extracted ACM binary file path
    """
    # check if output path is valid and has write permission
    if not (utils.is_write_ok(output_path)):
      output_path = os.path.join(configurations.OUT_DIR, 'ACM_binary.bin')
    acm_entries = self.get_acm_entries()
    for acm_offset in acm_entries:
      log.result(f"Information about Startup ACM with Offset = {hex(acm_offset)} in the IFWI/BIOS")
      bios_bin = utils.get_buffer(self.binary)
      # FFS guid will be located at offset = (ACM header offset -0x18) in the IFWI/BIOS
      bios_bin.seek(acm_offset - ctypes.sizeof(structure.EfiFfsFileHeader))
      ffs_guid = structure.EfiFfsFileHeader.read_from(bios_bin)
      log.debug(f"FFS Guid = {str(ffs_guid.get_guid)}")
      display_acm_details(self.binary, acm_offset)
      bios_bin.seek(acm_offset)
      acm_header_info = structure_restricted.AcmHeader.read_from(bios_bin)
      acm_bin = self.binary[acm_offset:acm_offset + acm_header_info.get_acm_size]
      filename, file_extension = os.path.splitext(output_path)
      output_path = f"{filename}_{hex(acm_offset)}{file_extension}"
      if self.save_binary(acm_bin, output_path):
        log.result(f"Extracted acm binary is stored at = {output_path}\n")
        return 0

  def acm_patching(self, startup_acm_file, output_path, criteria):
    """Function to perform ACM Patching on the given input IFWI/BIOS file

    :param startup_acm_file: Input Startup ACM binary file path
    :param output_path: Path to store the ACM patched IFWI/BIOS
    :param criteria: Elements to be matched for patching
    :return: will provide the ACM related information and ACM patched IFWI/BIOS binary
    """
    acm_patched_bin = None
    # check if output path is valid and has write permission
    if not (utils.is_write_ok(output_path)):
      output_path = os.path.join(configurations.OUT_DIR, 'ACM_Patched_Binary.bin')

    acm_entries = self.get_acm_entries()  # Get all the ACM entries in the IFWI/BIOS
    for acm_offset in acm_entries:
      log.result(f"Information about Startup ACM with Offset = {hex(acm_offset)} in the IFWI/BIOS")
      display_acm_details(self.binary, acm_offset)
      for entries in startup_acm_file:
        log.result(f"Information about the input Startup ACM Binary file = {entries}")
        with open(entries, 'rb') as acm_file:
          startup_acm_bin = bytearray(acm_file.read())
        display_acm_details(startup_acm_bin, 0)
        acm_header = self.get_patch_offset(acm_offset, startup_acm_bin, criteria)
        if not acm_header:
          log.error(
            f"ACM binary at {hex(acm_offset)} in the IFWI/BIOS is not compatible for patching with input Startup "
            f"ACM binary {entries}")
          utils.XmlCliException(error_code='0x5AC04')
          return 1
        elif acm_header == 1:
          log.result(
            f"Startup ACM binary inside IFWI/BIOS and Input Startup ACM binary {entries} are same.. No Patching "
            f"performed")
          utils.XmlCliException(error_code='0x5AC05')
          return 1
        elif acm_header:
          bios_bin = utils.get_buffer(self.binary)
          bios_bin.seek(acm_header)
          acm_header_info = structure_restricted.AcmHeader.read_from(bios_bin)
          acm_size = acm_header_info.get_acm_size
          # Comparing the size of ACM inside the IFWI/BIOS with input start up ACM,if equal perform acm patching
          if acm_size == len(startup_acm_bin):
            acm_patched_bin = self.create_acm_patched_binary(startup_acm_bin, acm_header)
            # If size of the ACM inside the BIOS/IFWI is more than the size of input acm binary, then perform zero
            # padding to input startup acm binary and perform ACM patching
          elif acm_size > len(startup_acm_bin):
            padding_size = acm_size - len(startup_acm_bin)
            startup_acm_bin = utils.zero_padding(startup_acm_bin, padding_size)
            acm_patched_bin = self.create_acm_patched_binary(startup_acm_bin, acm_header)
            # If size of ACM inside the BIOS/IFWI is less than the size of input acm binary and size of input ACM binary
            # is less than 250KB, then perform acm patching with startup acm binary
          elif acm_size < len(startup_acm_bin) < DEFAULT_ACM_SIZE:
            acm_patched_bin = self.create_acm_patched_binary(startup_acm_bin, acm_header)

      if acm_patched_bin and self.save_binary(acm_patched_bin, output_path):
        log.result(f"New IFWI/BIOS image created with ACM patched successfully at ={output_path}")
        return 0

  def process_acm(self, operation=None, startup_acm_file=None, output_path=None, criteria=["HeaderVersion", "ChipsetID"]):
    """Function to Perform Startup ACM patching on the Given Binary and Provide information about the ACM binary

    :param operation : operation to be performed on Startup ACM, choices: `read`, `update`
    :param startup_acm_file: Input Startup ACM binary file path
    :param output_path : Path to store the Patched IFWI/BIOS binary
    :param criteria: Elements to be matched for patching
    :return: if operation == Read then performs the ACM read operation and provides ACM related information and
            save the Extracted ACM binary in the path specified by the user or default path.
            if operation == Update performs patching if the patching criteria  meets
            and save the ACM patched IFWI/BIOS in the specified or default location
    """
    if isinstance(operation, str) and (operation.lower() == "read" or operation.lower() == "update"):
      if utils.is_read_ok(self.binary_file) and self.is_binary_valid():
        if operation.lower() == "read":
          return self.acm_read(output_path=output_path)
        else:
          startup_acm_path = []
          if utils.is_read_ok(startup_acm_file):
            startup_acm_path.append(startup_acm_file)
          elif isinstance(startup_acm_file, list):
            for entries in startup_acm_file:
              if utils.is_read_ok(entries):
                startup_acm_path.append(entries)
          if len(startup_acm_path) != 0:
            _criteria = criteria if set(criteria).issubset(set(table_header)) else ["HeaderVersion", "ChipsetID"]
            return self.acm_patching(startup_acm_file=startup_acm_path, output_path=output_path, criteria=_criteria)
          else:
            utils.XmlCliException(error_code='0x5AC03')
            return 1
      else:
        utils.XmlCliException(error_code='0x5AC02')
        return 1
    else:
      utils.XmlCliException(error_code='0x5AC01')
      return 1


def ProcessAcm(operation=None, binary_file=None, startup_acm_file=None, output_path=None, criteria=["HeaderVersion", "ChipsetID"]):
  """Extension method for process_acm method of `Acm()`"""
  acm_instance = Acm(binary_file)
  return acm_instance.process_acm(
    operation=operation,
    startup_acm_file=startup_acm_file,
    output_path=output_path,
    criteria=criteria
  )


if __name__ == "__main__":
  pass
