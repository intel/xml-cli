# coding=utf-8
"""
This file serves class method which allow to parse
BIOS region from given binary file.

Syntax:

```
from xmlcli_mod.common import bios_fw_parser

bios_image = "absolute-path/to/bios-image.rom"

uefi_parser = bios_fw_parser.UefiParser(
  bin_file=bios_image,  # binary file to parse
  parsing_level=0,  # parsing level to manage number of parsing features
  base_address=0,  # (optional) provide base address of bios FV region to start the parsing (default 0x0)
  guid_to_store=[]  # if provided the guid for parsing then parser will look for every GUID in the bios image
)
# parse binary
output_dict = uefi_parser.parse_binary()
output_dict = uefi_parser.sort_output_fv(output_dict)  # (optional) only to sort output by FV address

# write content to json file
output_file = "absolute-path/to/output.json"
uefi_parser.write_result_to_file(output_file, output_dict=output_dict)

# Below code block is only to store map result to json for FV region(s) extracted by guid lookup
if uefi_parser.guid_to_store:
    # additional test for GUIDs to store
    result = uefi_parser.guid_store_dir  # result of passed guid
    user_guid_out_file = "absolute-path/to/guid-stored/output.json"
    # Store guid stored result to json file
    uefi_parser.write_result_to_file(user_guid_out_file, output_dict=uefi_parser.stored_guids)
```
"""

# Built-in imports
import os
import json
import logging
import shutil
from collections import namedtuple

# Custom imports
from . import utils
from . import compress
from . import structure
from . import configurations


__version__ = "0.0.1"
__author__ = "Gahan Saraiya"

log = logging.getLogger(__name__)

FirmwareVolumeGuid = namedtuple("FirmwareVolumeGuid", ["name", "guid", "method", "description"])

RAW_SECTION_EFI_INITIAL_OFFSET = 0x26


class UefiParser(object):
  """
  Class Method allows to parse BIOS Region as per UEFI Specification
  """

  def __init__(self, bin_file, parsing_level=0, **kwargs):
    """Uefi Binary Parsing Utility

    :param bin_file: binary file to parse
    :param parsing_level: parsing level to manage number of parsing features
    :param kwargs:
      - base_address (optional): user can provide base address of bios FV region to start the parsing (default 0x0)
      - guid_to_store (optional): if user provides the guid for parsing then parser will look for every GUID in the bin_file
    """
    log.info("Initializing Uefi Firmware Parser..")
    self.parsing_level = utils.PARSING_LEVEL_MAP.get(parsing_level, utils.PARSING_LEVEL_MAP.get(0))
    self.user_specified_base_address = kwargs.get("base_address", None)
    self.guid_to_store = kwargs.get("guid_to_store", [])  # if passed guid_to_store, list of guid then store the respective binary by guid
    if self.guid_to_store:
      self.guid_to_store = [utils.guid_formatter(guid) for guid in self.guid_to_store]
    log.info(f"GUID bins to store: {self.guid_to_store}")
    self.parse_efi_variable = kwargs.get("parse_efi_variable", True)
    self.efi_variables = {}  # this data would be populated if parse_efi_variable set to `True`.
    # reformat guids to specific format
    self.stored_guids = {utils.guid_formatter(guid): [] for guid in self.guid_to_store}
    log.debug(self.stored_guids)
    self.base_address = self.set_base_address(bin_file=bin_file)
    self.buffer = self.set_buffer(bin_file=bin_file)
    self.root_dir = os.path.dirname(os.path.abspath(bin_file))
    self.base_file_name = os.path.splitext(os.path.basename(bin_file))[0]
    self.bin_dir = os.path.join(self.root_dir, self.base_file_name)
    self.guid_store_dir = os.path.join(self.root_dir, self.base_file_name, "guid_stored")
    self.bin_file_size = self.get_file_size(file=bin_file)
    log.info(
      f"Binary file: {bin_file}" +
      f"\nBinary file size: 0x{self.bin_file_size:x}" +
      f"\nBuffer start at: 0x{self.base_address:x}"
    )
    self.output = {}

    self.firmware_volume_guids = {
      "7a9354d9-0468-444a-81ce0bf617d890df": FirmwareVolumeGuid("FFS1",         [0x7a9354d9, 0x0468, 0x444a, 0x81, 0xce, 0x0b, 0xf6, 0x17, 0xd8, 0x90, 0xdf], self.parse_ffs, ""),
      "8c8ce578-8a3d-4f1c-9935896185c32dd3": FirmwareVolumeGuid("FFS2",         [0x8c8ce578, 0x8a3d, 0x4f1c, 0x99, 0x35, 0x89, 0x61, 0x85, 0xc3, 0x2d, 0xd3], self.parse_ffs, "The firmware volume header contains a data field for the file system GUID"),
      "5473c07a-3dcb-4dca-bd6f1e9689e7349a": FirmwareVolumeGuid("FFS3",         [0x5473c07a, 0x3dcb, 0x4dca, 0xbd, 0x6f, 0x1e, 0x96, 0x89, 0xe7, 0x34, 0x9a], self.parse_ffs, "EFI_FIRMWARE_FILE_SYSTEM3_GUID indicates support for FFS_ATTRIB_LARGE_SIZE and thus support for files 16MB or larger. "),
      "1ba0062e-c779-4582-8566336ae8f78f09": FirmwareVolumeGuid("VTF",          [0x1BA0062E, 0xC779, 0x4582, 0x85, 0x66, 0x33, 0x6A, 0xE8, 0xF7, 0x8F, 0x09], self.parse_ffs, "A Volume Top File (VTF) is a file that must be located such that the last byte of the file is also the last byte of the firmware volume. Regardless of the file type"),
      "fff12b8d-7696-4c8b-a9852747075b4f50": FirmwareVolumeGuid("NVRAM_EVSA",   [0xfff12b8d, 0x7696, 0x4c8b, 0xa9, 0x85, 0x27, 0x47, 0x07, 0x5b, 0x4f, 0x50], self.parse_null, ""),
      "cef5b9a3-476d-497f-9fdce98143e0422c": FirmwareVolumeGuid("NVRAM_NVAR",   [0xcef5b9a3, 0x476d, 0x497f, 0x9f, 0xdc, 0xe9, 0x81, 0x43, 0xe0, 0x42, 0x2c], self.parse_null, ""),
      "00504624-8a59-4eeb-bd0f6b36e96128e0": FirmwareVolumeGuid("NVRAM_EVSA2",  [0x00504624, 0x8a59, 0x4eeb, 0xbd, 0x0f, 0x6b, 0x36, 0xe9, 0x61, 0x28, 0xe0], self.parse_null, ""),
      "04adeead-61ff-4d31-b6ba64f8bf901f5a": FirmwareVolumeGuid("APPLE_BOOT",   [0x04adeead, 0x61ff, 0x4d31, 0xb6, 0xba, 0x64, 0xf8, 0xbf, 0x90, 0x1f, 0x5a], self.parse_null, ""),
      "16b45da2-7d70-4aea-a58d760e9ecb841d": FirmwareVolumeGuid("PFH1",         [0x16b45da2, 0x7d70, 0x4aea, 0xa5, 0x8d, 0x76, 0x0e, 0x9e, 0xcb, 0x84, 0x1d], self.parse_null, ""),
      "e360bdba-c3ce-46be-8f37b231e5cb9f35": FirmwareVolumeGuid("PFH2",         [0xe360bdba, 0xc3ce, 0x46be, 0x8f, 0x37, 0xb2, 0x31, 0xe5, 0xcb, 0x9f, 0x35], self.parse_null, ""),
    }

  def parse_null(self, *args, **kwargs):
    return {}

  @staticmethod
  def is_bios(bin_file):
    return True

  @staticmethod
  def is_ifwi(bin_file):
    return False

  @staticmethod
  def get_file_size(file):
    """Calculate size of the bin file to be read

    :param file:
    :return:
    """
    return os.path.getsize(file)

  @staticmethod
  def set_buffer(bin_file):
    if bin_file:
      return open(bin_file, "rb")

  @staticmethod
  def override_log_level(level):
    log.setLevel(level=level)
    for log_handler in log.handlers:
      log_handler.setLevel(level=level)

  def run_cleaner(self):
    """Clean up the directories containing temporary file(s)
    from previous session
    """
    utils.clean_directory(self.guid_store_dir)
    utils.clean_directory(os.path.join(self.root_dir, self.base_file_name))
    utils.clean_directory(utils.get_temp_folder())

  def set_base_address(self, bin_file):
    """Set base address of the bios image

    :param bin_file: bin file to find out base address
    :return: base address of start of BIOS region in the file
    """
    if self.user_specified_base_address:
      log.debug("Using user specified base address")
      return self.user_specified_base_address
    else:
      if self.is_bios(bin_file):
        log.debug("BIOS only address")
        return 0x00
      elif self.is_ifwi(bin_file):
        # calculate bios start region
        log.debug("Calculating for IFWI to find BIOS region")
        return 0x00

  def store_guid(self, buffer, start, end, guid, nesting_level, is_compressed=False, _type="FV", **kwargs):
    """Utility to store content of buffer in file system.
    Enabling this utility will actually decomposes all the binaries in BIOS file system to
    folder structure

    :param buffer: buffer which is to be stored
    :param start: start region from where to binary to be stored
    :param end: end region at which binary should hold storing the value
    :param guid: unique guid if available otherwise empty string
    :param nesting_level: nesting level of current fv/ffs/section
    :param is_compressed: Determines whether current FV is part of compressed section or not
    :param _type: type of the buffer to be stored
    :return:
    """
    dir_path = kwargs.get("dir_path", self.guid_store_dir)
    log.debug(f"Checking to store guid: {guid}")
    if guid in self.stored_guids.keys():
      log.debug(f"Storing guid instance for guid: {guid}")
      guids = self.stored_guids.get(guid)
      instance = "" if len(guids) == 0 else f"_instance_{len(guids)}"
      dir_path = utils.make_directory(dir_path)
      log.debug(f"PARAMS: \nDIR: {dir_path} \nstart: 0x{start:x}\nend: 0x{end:x}")
      buffer.seek(start)
      content = buffer.read(end - start)
      buffer.seek(start)

      file_name = f"{guid}{instance}.{_type.lower()}"
      file_location = os.path.join(self.guid_store_dir, file_name)
      # Write file to file_location
      with open(file_location, "wb") as f:
        f.write(content)

      output = {
        "file_name": file_location,
        "start": start,
        "size": end - start,
        "is_compressed": is_compressed
      }
      log.debug(output)
      guids.append(output)

  @staticmethod
  def is_valid_fv(firmware_volume_header):
    has_valid_signature = firmware_volume_header.Signature == structure.FV_SIGNATURE
    has_valid_zero_vector = utils.get_integer_value(firmware_volume_header.get_value("ZeroVector")) == 0
    if has_valid_signature and has_valid_zero_vector:
      return True
    else:
      log.debug(firmware_volume_header.dump_dict())
      return False

  def parse_binary(self, **kwargs):
    """Parse Binary file for BIOS region

    :param kwargs:
      buffer: Buffer to be read to parse firmware volume(s)
      start: start of BIOS region
      file_size: size of BIOS file/region for end region
      bin_dir: specifies directory to store the parsed firmware volume
    :return: Dictionary of Parsed binary
    """
    buffer_pointer = kwargs.get("start", self.base_address)
    file_size = kwargs.get("file_size", self.bin_file_size)
    bin_dir = kwargs.get("bin_dir", self.bin_dir)
    buffer = kwargs.get("buffer", self.buffer)
    log.debug(f"{'Reading Binary':*^80}")
    log.debug(f"Reading file of size: 0x{self.bin_file_size:x} from 0x{buffer_pointer:x}")
    bios_size = file_size - buffer_pointer
    log.debug(f"Size of BIOS: {bios_size} bytes ({bios_size // 1024} KB)")

    self.output.update(self.parse_firmware_volume(buffer, buffer_pointer, end_point=file_size, bin_dir=bin_dir))
    log.debug(self.stored_guids)
    return self.output

  def parse_firmware_volume(self, buffer, buffer_pointer, end_point, nesting_level=0, is_compressed=False, **kwargs):
    """Parse the Firmware Volume(s) from given buffer

    :param buffer: Buffer to be read to parse firmware volume(s)
    :param buffer_pointer: pointer to start reading the firmware volume(s)
    :param end_point: end address of buffer till which to lookup for firmware volume
    :param nesting_level: Specifies level of nesting encapsulation
    :param is_compressed: Determines whether current FV is part of compressed section or not
    :param kwargs:
            is_sub_fv [Optional]: Specifies whether it is the root FV of BIOS binary or not (does not specifies the nesting level)
            bin_dir: specifies directory to store the parsed firmware volume
    :return: Dictionary of parsed firmware volume
    """
    log.info(f"{f'Firmware Volume @ 0x{buffer_pointer:x} [Nesting Level: {nesting_level}]' :~^80}")
    is_sub_fv = kwargs.get("is_sub_fv", False)
    bin_dir = kwargs.get("bin_dir", self.bin_dir)
    utils.store_buffer(dir_path=bin_dir, buffer=buffer, start=buffer_pointer, end=end_point, _type="fv")

    result = {}  # construct empty dictionary to store content of current FV
    if buffer_pointer >= end_point:
      log.info(f"[BUFFER (0x{buffer_pointer:x}) OUT OF end_point: 0x{end_point:x}] for firmware header. Nothing to Parse...")
      return result
    fv = structure.EfiFirmwareVolumeHeader()

    if buffer_pointer + fv.cls_size > end_point:
      # if buffer is beyond the file limit then break the recursion flow
      log.info(f"[BUFFER (0x{buffer_pointer:x}) OUT OF end_point: 0x{end_point:x}] for firmware header. Nothing to Parse...")
      # self.output.update(result)
      return result
    else:  # Valid firmware volume is parsed
      log.info(f"Parsing FVs {'[is_sub_fv]' if is_sub_fv else ''} from 0x{buffer_pointer:x} till end: 0x{end_point:x}")

    buffer.seek(buffer_pointer)  # seek to specified buffer pointer
    firmware_volume_header = fv.read_from(buffer)  # read header structure from buffer
    log.debug("FV parsed...")

    # construct Directory name to store file system of the current FV
    fv_dir = os.path.join(bin_dir, f"FV_0x{buffer_pointer:x}_to_0x{buffer_pointer + firmware_volume_header.FvLength:x}")

    if self.is_valid_fv(firmware_volume_header):  # FV signature must be `_FVH`:
      key = f"0x{buffer_pointer:x}-{'FVI'}-0x{firmware_volume_header.FvLength:x}"  # construct key to store fv values
      result[key] = firmware_volume_header.dump_dict()  # store result of fv header data in the dictionary
      fv_guid = firmware_volume_header.FileSystemGuid.guid  # Get GUID of the FV

      if fv_guid in self.firmware_volume_guids:  # parse only valid FV GUIDs
        if firmware_volume_header.ExtHeaderOffset:  # recalculate fv header length if extended header offset
          buffer.seek(buffer_pointer + firmware_volume_header.ExtHeaderOffset)  # seek/shift to extended header offset buffer
          # read extended header from buffer
          firmware_volume_extended_header = structure.EfiFirmwareVolumeExtHeader().read_from(buffer)
          # Override New Header Length
          firmware_volume_header.HeaderLength = firmware_volume_header.ExtHeaderOffset + firmware_volume_extended_header.ExtHeaderSize
          result[key]["HeaderLength"] = hex(firmware_volume_header.HeaderLength)  # Override Header Length in dictionary
          result[key]["FvNameGuid"] = firmware_volume_extended_header.FvName.guid  # add new unique fv guid key
          if self.guid_to_store:
            self.store_guid(dir_path=self.guid_store_dir,
                            buffer=buffer,
                            start=buffer_pointer,
                            end=buffer_pointer + firmware_volume_header.FvLength,
                            guid=firmware_volume_extended_header.FvName.guid,
                            nesting_level=nesting_level,
                            is_compressed=is_compressed,
                            _type="FV")

        log.debug(f"Header Length of FV ({fv_guid}): 0x{firmware_volume_header.HeaderLength:x}")
        start = buffer_pointer + firmware_volume_header.HeaderLength  # calculate start region of ffs data within this FV
        end = buffer_pointer + firmware_volume_header.FvLength  # calculate end region of ffs data within this FV (till FV Length)
        log.debug(f"Start: 0x{start:x}  | END: 0x{end:x} | BIN_FILE_SIZE: 0x{end_point:x}")
        # Parse the file system according to the
        data_or_code = self.firmware_volume_guids.get(fv_guid)  # get type of Filesystem by GUID
        result[key][data_or_code.name] = data_or_code.method(buffer, start, end, nesting_level, is_compressed, bin_dir=fv_dir)
      else:
        # GUID is invalid or GUID for this parsing method not implemented yet
        err_msg = f"Parsing firmware volume for GUID: {fv_guid} is not implemented"
        log.error(err_msg)

      # Increment buffer pointer to be read next FV
      buffer_pointer = buffer_pointer + firmware_volume_header.FvLength
    else:
      log.debug(f"Invalid FV Signature: {firmware_volume_header.Signature.decode('utf-16')} at 0x{buffer_pointer:x}")
      invalid_fv_start = buffer_pointer  # store offset where invalid fv found
      while not self.is_valid_fv(firmware_volume_header) and buffer_pointer + fv.cls_size <= end_point:
        # loop till finding the next valid fv to avoid maximum recursion depth
        # Skip FV reading to next alignment block if end_point is not reached
        buffer_pointer += structure.FV_BLOCK_ALIGNMENT
        if buffer_pointer < end_point:
          buffer.seek(buffer_pointer)
          firmware_volume_header = fv.read_from(buffer)
        else:
          break
      key = f"0x{invalid_fv_start:x}-{'InvalidFVI'}-0x{buffer_pointer - invalid_fv_start:x}"  # construct key to store fv values
      result[key] = fv.dump_dict()
      log.debug(f"Invalid Signature of FV from 0x{invalid_fv_start:x} to: 0x{buffer_pointer:x}")
    if not is_sub_fv:
      if buffer_pointer == 0x2612000:
        pass
      self.output.update(self.parse_firmware_volume(buffer, buffer_pointer, end_point=end_point, nesting_level=nesting_level, is_compressed=is_compressed))
    return result

  def parse_ffs(self, buffer, buffer_pointer, end_point, nesting_level, is_compressed, **kwargs):
    """Parse File System of type FFS1, FFS2, FFS3

    :param buffer: buffer from where filesystem to be parsed
    :param buffer_pointer: pointer to start reading the FFS
    :param end_point: end address of buffer till which to lookup for FFS
    :param nesting_level: Specifies level of nesting encapsulation
    :param is_compressed: Determines whether current FFS is part of compressed section or not
    :param kwargs:
            bin_dir: specifies directory to store the parsed firmware volume
    :return: dictionary of the ffs parsed
    """
    log.info(f"{f'FFS [Nesting Level: {nesting_level}]' :*^80}")
    log.debug(f"Parsing FFS from buffer: 0x{buffer_pointer:x} till 0x{end_point:x}")
    result = {}  # construct empty dictionary to store content of current FFS
    align_buffer = utils.round_up(buffer_pointer, structure.FFS_ALIGNMENT)  # align buffer with FFS alignment
    bin_dir = kwargs.get("bin_dir")  # directory to store the ffs bins
    utils.store_buffer(dir_path=bin_dir, buffer=buffer, start=buffer_pointer, end=end_point, _type="fv")

    while align_buffer < end_point:  # parse all ffs under FV region
      log.info(f"{f'FFS [Nesting Level: {nesting_level}]' :*^80}")
      log.debug(f"Parsing FFS from aligned buffer: {hex(align_buffer)} / {hex(end_point)}")
      # read valid ffs data from buffer
      ffs_data = structure.read_structure(method=structure.efi_ffs_file_header,
                                          base_structure=structure.EfiFfsFileHeader,
                                          buffer=buffer,
                                          buffer_pointer=align_buffer)
      # dump parsed ffs data to the dictionary
      ffs_data_dict = ffs_data.dump_dict()

      log.debug(ffs_data)
      key = f"0x{align_buffer:x}-{'FFS'}-0x{ffs_data.size:x}"  # construct key to store fv values
      result[key] = ffs_data_dict
      if ffs_data.Type not in structure.FFS_FILE_TYPE_MAP:
        # FFS type not found in ffs file type map
        err_msg = f"Encountered unknown ffs type: {ffs_data.Type} at 0x{align_buffer:x} at nesting level: {nesting_level}"
        log.error(err_msg)
        return result
      elif ffs_data.size == 0:
        # All bytes padded with zeroes
        err_msg = f"Encountered all bytes padded to zeroes at: 0x{align_buffer:x} at nesting level: {nesting_level}"
        log.error(err_msg)
        return result
      ffs_type = structure.FFS_FILE_TYPE_MAP.get(ffs_data.Type).name  # text for ffs type

      start = align_buffer + ffs_data.cls_size  # calculate start pointer of ffs data (first section)
      end = align_buffer + ffs_data.size  # calculate location of next ffs
      if self.guid_to_store:
        self.store_guid(dir_path=self.guid_store_dir,
                        buffer=buffer,
                        start=start,
                        end=end,
                        guid=ffs_data.Name.guid,
                        nesting_level=nesting_level,
                        is_compressed=is_compressed,
                        _type="FFS")

      # create FFS directory name to store section content
      ffs_dir = os.path.join(bin_dir, f"FFS_0x{start:x}_to_0x{end:x}")
      # parse all section within the ffs and store it in the dictionary
      result[key]["section"] = self.parse_ffs_section(buffer, start, end, ffs_data, _type=ffs_type,
                                                      nesting_level=nesting_level, is_compressed=is_compressed, bin_dir=ffs_dir)
      log.debug(f">>>>--- buffer: 0x{align_buffer:x}\nffs size: 0x{ffs_data.size:x}\nend: 0x{end:x}")
      align_buffer += ffs_data.size  # increment aligned buffer to read next ffs
      # align the buffer for ffs alignment boundary
      align_buffer = utils.round_up(align_buffer, structure.FFS_ALIGNMENT)
    return result

  def parse_ffs_section(self, buffer, buffer_pointer, end_point, ffs_data, _type, nesting_level, is_compressed, **kwargs):
    """Parse sections within given file system (FFS)

    :param buffer: buffer to parse section from
    :param buffer_pointer: pointer to buffer from where to start parsing section(s)
    :param end_point: end point of ffs till which section(s) to be parsed
    :param ffs_data: ffs data within which section is parsed
    :param _type: type of ffs file system map
    :param nesting_level: Specifies level of nesting encapsulation
    :param is_compressed: Determines whether current Section is part of compressed section or not
    :param kwargs:
            bin_dir: specifies directory to store the parsed firmware volume
    :return: dictionary of parsed section(s) within the ffs
    """
    ffs_guid = ffs_data.Name.guid
    log.info(f"{f'Section @FFS-{ffs_guid} [Nesting Level: {nesting_level}]' :`^80}")
    result = {}  # construct empty dictionary to store content of current FFS
    if self.parsing_level.level >= 4:  # SKIP_SECTION_PARSING
      return result
    align_buffer = buffer_pointer
    bin_dir = kwargs.get("bin_dir")  # directory to store the ffs bins
    utils.store_buffer(dir_path=bin_dir, buffer=buffer, start=buffer_pointer, end=end_point, _type="ffs")

    while align_buffer < end_point:  # parse all sections within ffs region
      log.debug(f"Parsing Section from aligned buffer: 0x{align_buffer:x} / 0x{end_point:x}")
      if ffs_guid == structure.DEFAULT_GUID or _type == "FV_FILETYPE_RAW" or ffs_data.size == 0x0:
        # no section can be found in this case
        # TODO: reveal blackbox
        log.debug(f"No SECTION found for GUID: {ffs_guid} _type: {_type}")
        return result
      # read section data from file
      try:
        buffer.seek(align_buffer)  # seek to aligned buffer
      except Exception as e:
        err_msg = f"buffer seek error: {e}"
        log.error(err_msg)
        buffer = utils.get_buffer(buffer)
        buffer.seek(align_buffer)
      section = structure.section_finder(buffer=buffer, buffer_pointer=align_buffer)  # parse valid section from buffer
      log.debug(section)
      key = f"0x{align_buffer:x}-{'SEC'}-0x{section.get_section_size():x}"  # construct key to store fv values
      # construct section tuple if valid section type
      section_tuple = structure.FFS_SECTION_TYPE_MAP.get(section.section_type)
      if not section_tuple:
        # TODO: reveal blackbox
        err_msg = f"No SECTION for FFS ({_type}):- {ffs_guid} at 0x{align_buffer:x} FOR: {section}"
        log.error(err_msg)
      else:  # found valid section to process
        result[key] = section.dump_dict()  # dump section data to dictionary
        start = align_buffer + section.cls_size  # calculate start of the section buffer
        end = align_buffer + section.get_section_size()  # calculate end of the section buffer
        # create name for section directory to store data/code parsed within it
        section_dir = os.path.join(bin_dir, f"SECTION_0x{align_buffer:x}_to_0x{end:x}")
        if ffs_guid in self.guid_to_store and section_tuple.name == "EFI_SECTION_RAW":
          self.parse_efi_variable_data(buffer, buffer_pointer=buffer_pointer + RAW_SECTION_EFI_INITIAL_OFFSET,
                                       end_point=end)
          print(self.efi_variables)
        if section_tuple.is_encapsulated:  # encapsulation sections
          # value can be 0x1 - EFI_SECTION_COMPRESSION, 0x2 -EFI_SECTION_GUID_DEFINED or 0x3 - EFI_SECTION_DISPOSABLE
          nesting_level += 1
          log.debug("Encountered encapsulated section")
          result[key]["encapsulation"] = self.read_encapsulation_section(buffer,
                                                                         buffer_pointer=start,
                                                                         end_point=end,
                                                                         section=section,
                                                                         section_tuple=section_tuple,
                                                                         nesting_level=nesting_level,
                                                                         is_compressed=is_compressed,
                                                                         ffs_data=ffs_data,
                                                                         bin_dir=section_dir)
        elif section_tuple.name == "EFI_SECTION_FIRMWARE_VOLUME_IMAGE":  # value: 0x17
          # parse firmware volume under the current section
          if self.parsing_level.level < 3:
            result[key]["FV"] = self.parse_firmware_volume(buffer=buffer,
                                                           buffer_pointer=start,
                                                           end_point=end,
                                                           nesting_level=nesting_level,
                                                           is_compressed=is_compressed,
                                                           bin_dir=section_dir)
            if utils.SORT_FV:
              result[key]["FV"] = self.sort_output_fv(result[key]["FV"])

      log.debug(f"Aligned buffer: 0x{align_buffer:x}")
      align_buffer += section.get_section_size()
      log.debug(f"Incremented Aligned buffer: 0x{align_buffer:x}")
      align_buffer = utils.round_up(align_buffer, structure.SECTION_ALIGNMENT)
      log.debug(f"Aligned buffer at 0x{structure.SECTION_ALIGNMENT:x} bytes: 0x{align_buffer:x}")

    return result

  def read_encapsulation_section(self, buffer, buffer_pointer, end_point, section, section_tuple, nesting_level, is_compressed, ffs_data, **kwargs):
    """Read Encapsulation section under the FFS,
    can be compressed section or guided defined section

    :param buffer: buffer to be parsed for encapsulation section
    :param buffer_pointer: pointer from where to start parsing encapsulation section
    :param end_point: end offset till which encapsulation section to be parsed
    :param section: section under which encapsulation section exists
    :param section_tuple: parsed section tuple to get value and type to determine which kind of encapsulation to be processed
    :param nesting_level: Specifies level of nesting encapsulation
    :param is_compressed: Determines whether current encapsulation is part of compressed section or not
    :param ffs_data: parsed ffs structure under which current encapsulation section exists
    :param kwargs:
            bin_dir: specifies directory to store the parsed firmware volume
    :return: dictionary containing parsed encapsulation section
    """
    log.info(f"{f'Encapsulation Section [Nesting Level: {nesting_level}]' :.^50}")
    result = {}  # construct empty dictionary to store content of current FFS
    if self.parsing_level.level >= 2:  # SKIP_ENCAPSULATION
      return result
    align_buffer = buffer_pointer
    bin_dir = kwargs.get("bin_dir")  # directory to store the ffs bins
    utils.store_buffer(dir_path=bin_dir, buffer=buffer, start=buffer_pointer, end=end_point, _type="enc_section")
    section_type = section_tuple.value
    log.debug(f"Encountered section_type: {section_tuple.name} (0x{section_type:x})")
    # TODO: cross-check the section size and offset is as expected or not
    key = f"0x{align_buffer:x}-{'SEC'}-0x{section.get_section_size():x}"

    if section_type == 0x01:  # EFI_SECTION_COMPRESSION
      if section.CompressionType == 0x1:
        log.debug("Standard Compression as per UefiSpec")
        section_guid = "a31280ad-481e-41b6-95e8127f4c984779"  # TIANO_CUSTOM_DECOMPRESS_GUID
        tiano_compress = structure.TianoCompressHeader().read_from(buffer)
        log.debug(tiano_compress)
        section_dir = os.path.join(bin_dir, f"ENCAPSULATED_SECTION_0x{align_buffer:x}_to_0x{align_buffer + section.get_section_size():x}")
        result[key] = self.read_guid_defined_section(buffer, section_guid, align_buffer, section, nesting_level, is_compressed, ffs_data, bin_dir=section_dir)
      else:  # 0x0 means no compression
        # TODO: read if this case to be handled or not
        log.error("NO COMPRESSION....")
    elif section_type == 0x02:  # EFI_SECTION_GUID_DEFINED
      guid = section.SectionDefinitionGuid
      attrib = section.Attributes
      start = align_buffer
      section_guid = guid.guid
      log.debug(f"EFI_SECTION_GUID: {section_guid}\nattrib: 0x{attrib:X}")
      if attrib & 0x01:  # Bit 1: EFI_GUIDED_SECTION_PROCESSING_REQUIRED
        # section requires further processing to obtain meaningful data from the section contents
        # section content can be encrypted or compressed
        # beginning of the encapsulated section defined by `DataOffset`
        log.debug(f"EFI_GUIDED_SECTION_PROCESSING_REQUIRED for GUID: {section_guid}")

        signed_section_tuple = structure.SIGNED_SECTION_GUIDS.get(section_guid)  # fetch type of signed section from GUID
        log.debug(signed_section_tuple)
        if signed_section_tuple:
          # The signed section is an encapsulation section in which the section data is cryptographically signed.
          # To process the contents and extract the enclosed section stream, the section data integrity must be
          # accessed by evaluating the enclosed data via the cryptographic information in the
          # PI Spec > Page 3-58 > EFI Signed Sections
          log.debug(f"EXTRA DEBUG:- {signed_section_tuple.name}")
          guid_process_method = signed_section_tuple.method
          start, section_guid, section = guid_process_method(buffer=buffer,
                                                             buffer_pointer=align_buffer,
                                                             section=section)
        if section_guid in compress.COMPRESSION_GUIDS:
          # create directory name to be stored compression section
          section_dir = os.path.join(bin_dir, f"COMPRESSION_SECTION_0x{start:x}_to_0x{end_point:x}")
          result[key] = self.read_guid_defined_section(buffer, section_guid, start, section, nesting_level, is_compressed, ffs_data, bin_dir=section_dir)
        else:
          # create directory name to be stored uncompressed section
          section_dir = os.path.join(bin_dir, f"FFS_SECTION_0x{start:x}_to_0x{end_point:x}")
          result[key] = self.parse_ffs_section(buffer=buffer,
                                               buffer_pointer=start,
                                               end_point=end_point,
                                               ffs_data=ffs_data,
                                               _type=structure.FFS_FILE_TYPE_MAP.get(ffs_data.Type).name,
                                               nesting_level=nesting_level, bin_dir=section_dir,
                                               is_compressed=is_compressed)
      elif attrib & 0x02:  # EFI_GUIDED_SECTION_AUTH_STATUS_VALID
        # section contains authentication data
        # TODO: check what can be done in this case
        err_msg = "attribute: EFI_GUIDED_SECTION_AUTH_STATUS_VALID is not handled yet."
        log.error(err_msg)
    elif section_type == 0x03:  # EFI_SECTION_DISPOSABLE
      # TODO: check what can be done in this case
      err_msg = "section type: EFI_SECTION_DISPOSABLE is not handled yet."
      log.error(err_msg)
    buffer.seek(align_buffer)
    return result

  def read_guid_defined_section(self, buffer, guid, buffer_pointer, section, nesting_level, is_compressed, ffs_data, **kwargs):
    """

    :param buffer: buffer to be parse for guided defined section
    :param guid: GUID of the the section
    :param buffer_pointer: pointer from where to start parsing guided defined section
    :param section: section containing guided defined section
    :param nesting_level: Specifies level of nesting encapsulation
    :param is_compressed: Determines whether current section is part of compressed section or not
    :param ffs_data: parsed ffs structure under which current guided defined section exists
    :param kwargs:
            bin_dir: specifies directory to store the parsed firmware volume
            section_content_size: size of the section content/data
    :return: dictionary containing parsed guid defined section
    """
    log.info(f"{f'Compressed section [Nesting Level: {nesting_level}]' :-^40}")
    result = {}  # construct empty dictionary to store content of current FFS
    if self.parsing_level.level >= 1:  # SKIP_DECOMPRESSION
      return result
    buffer.seek(buffer_pointer)
    bin_dir = kwargs.get("bin_dir")  # directory to store the ffs bins
    section_content_size = kwargs.get("section_content_size", None)
    section_content_size = section_content_size if section_content_size else (section.get_section_size() - (section.DataOffset if hasattr(section, "DataOffset") else section.cls_size))
    start = buffer_pointer
    end = buffer_pointer + section_content_size

    utils.store_buffer(dir_path=bin_dir, buffer=buffer, start=start, end=end, _type="guided_section")

    log.debug(f"Reading from 0x{buffer_pointer:x} to 0x{buffer_pointer + section_content_size:x} (0x{section_content_size:x} bytes)")
    log.debug(f"section {section}")
    compressed_data = buffer.read(section_content_size)
    decompress_obj = compress.ProcessEncapsulatedData(guid=guid, compressed_data=compressed_data, section=section)
    decompressed_data = decompress_obj.decompress()
    key = f"0x{start:x}-{'SEC'}-0x{section_content_size:x}"

    log.debug(f"===>>> Compressed file: {decompress_obj.temp_file_path}")
    log.debug(f"===>>> DeCompressed file: {decompress_obj.decompressed_file_path}")
    if decompressed_data:
      is_compressed = True
      log.debug(f".........Going to nesting firmware level: {nesting_level}.........")
      if utils.EXTRACT_FV_FFS:
        # copy decompressed and compressed files for debugging purpose
        compressed_file_name = f"C_nested_fv_lvl_{nesting_level}_base_address_0x{buffer_pointer:x}{configurations.PY_VERSION}.bin"
        decompressed_file_name = f"D_nested_fv_lvl_{nesting_level}_base_address_0x{buffer_pointer:x}{configurations.PY_VERSION}.bin"
        file_dir = os.path.join(configurations.OUT_DIR, "temp")
        utils.make_directory(file_dir)  # create the directory if not exists
        shutil.copy(decompress_obj.temp_file_path, os.path.join(file_dir, compressed_file_name))
        shutil.copy(decompress_obj.decompressed_file_path, os.path.join(file_dir, decompressed_file_name))
      with open(decompress_obj.decompressed_file_path, "rb") as decompressed_data:
        # construct guided defined directory to store content within it
        guid_defined_dir = os.path.join(bin_dir, f"GUID_DEFINED_SECTION_0x{start:x}_to_0x{end:x}")
        result[key] = self.parse_ffs_section(buffer=decompressed_data,
                                             buffer_pointer=0x00,
                                             end_point=os.path.getsize(decompress_obj.decompressed_file_path),
                                             ffs_data=ffs_data,
                                             _type=structure.FFS_FILE_TYPE_MAP.get(ffs_data.Type, 0),
                                             nesting_level=nesting_level, bin_dir=guid_defined_dir,
                                             is_compressed=is_compressed
                                             )
    return result

  def parse_efi_variable_data(self, buffer, buffer_pointer=0x0, end_point=0x0):
    if not self.parse_efi_variable:
      log.info("EFI Variable parsing Skipped")
      return False
    log.debug(f"=======> offset: 0x{buffer_pointer:X} end: 0x{end_point:X}")
    efi_var_struct = structure.efi_variable_structure()
    if efi_var_struct.cls_size + buffer_pointer <= end_point:
      buffer.seek(buffer_pointer)
      efi_var_data = efi_var_struct.read_from(buffer)
      if efi_var_data.guid.guid != '00000000-0000-0000-0000000000000000' and efi_var_data.name_length and efi_var_data.data_length:
        efi_var_struct = structure.efi_variable_structure(name_length=efi_var_data.name_length,
                                                          data_length=efi_var_data.data_length)
        if efi_var_struct.cls_size + buffer_pointer <= end_point:
          buffer.seek(buffer_pointer)
          efi_var_data = efi_var_struct.read_from(buffer)
          log.debug(efi_var_data)
          _key = f"{efi_var_data.get_name}_{efi_var_data.guid.guid}"
          self.efi_variables[_key] = efi_var_data.dump_dict()
          return self.parse_efi_variable_data(buffer, buffer_pointer=buffer_pointer + efi_var_data.cls_size, end_point=end_point)
        else:
          print("No data available to parse")
          return False

  def sort_output_fv(self, input_dict=None):
    from collections import OrderedDict
    input_dict = input_dict if input_dict else self.output
    sorted_dict = OrderedDict()
    sorted_keys = sorted(input_dict, key=lambda x: int(x.split("-")[0], 16))
    log.info(sorted_keys)
    for key in sorted_keys:
      sorted_dict[key] = input_dict.pop(key)
    return sorted_dict

  def write_result_to_file(self, file_path, **kwargs):
    """Write dictionary to json structure

    :param file_path: file location at where the json file to be written
    :param kwargs:
        output_dict: dictionary which is to be stored as json
            [DEFAULT]: it takes self.output
    :return: True status if file successfully dumped
    """
    output_dict = {
      "name": self.base_file_name,
      "size": self.bin_file_size,
      "location": file_path,
      "script_version": __version__,
      "module_version": None,
      "data": kwargs.get("output_dict", self.output)
    }
    try:
      import xmlcli
      output_dict["module_version"] = xmlcli._version.__version__.vstring
      del xmlcli
    except ImportError or AttributeError:
      pass

    with open(file_path, "w") as f:
      log.info("dumping content into json...")
      json.dump(output_dict, f, indent=4, sort_keys=kwargs.get("sort_keys", False))
    log.info(f"File successfully stored at: {os.path.abspath(file_path)}")
    return True


if __name__ == "__main__":
  print("Please run test suite for the testing")
