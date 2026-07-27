# -*- coding: utf-8 -*-

# Built-in imports
import os
import sys
import shutil
import warnings
import unittest

warnings.simplefilter("ignore", ResourceWarning)

# Custom imports
from .UnitTestHelper import *
from xmlcli.UefiFwParser import ProcessBin, PrintLogFile
from xmlcli.common import utils
from xmlcli.common import structure
from xmlcli.common import bios_fw_parser
from xmlcli.common import configurations

__author__ = "Gahan Saraiya"

PARSE_ALL = True
# To override logging level while executing the test
LOG_LEVEL = "DEBUG"  # options for LOG_LEVEL = DEBUG|INFO|ERROR|WARN


class UtilityTest(UnitTestHelper):
  def test_guid_structure_read(self):
    guid = "0x92daaf2f-0xc02b-0x455b-0xb2-0xec-0xf5-0xa3-0x59-0x4f-0x4a-0xea"
    guid_struct = structure.Guid()
    guid_struct.read_guid(guid)
    self.assertEqual(utils.guid_formatter(guid_struct.guid, string_format="xmlcli"), guid)


class UefiParserTest(UnitTestHelper):
  guid_lis1 = [
    # GUIDs available in ADL_FSP_0496_00_D.rom  (may exist in other rom)
    "fc8fe6b5-cd9b-411e-bd8f31824d0cde3d",
    "eed5ea31-38e2-463d-b623-2c57702b8a1c",
    "a6aef1f6-f25a-4082-af39-22-29-bc-f5-a6-e1",
    "1b45cc0a-156a-428a-af-62-49-86-4d-a0-e6-e6",
    "0x9faad0ff-0x0e0c-0x4885-0xa738bab4e4fa1e66",
    "0x1008aed2-0x40bb-0x47c8-0xae8e-0x4e8fbefe8a1f",
    "0xf57757fc-0x2603-0x404f-0xaa-0xe2-0x34-0xc6-0x23-0x23-0x88-0xe8",
    ["4f84e985", "4c3b", "4825", "9f42889109019422"],
    ["8958d092", "7b26", "4e47", "bb98", "16ae2dc315a2"],
    ["0x9b7fa59d", "0x71c6", "0x4a36", "0x906e9725ea6add5b"],
    [0xae265864, 0xcf5d, 0x41a8, 0x91, 0x3d, 0x71, 0xc1, 0x55, 0xe7, 0x64, 0x42],
    ["0x6141e486", "0x7543", "0x4f1a", "0xa5", "0x79", "0xff", "0x53", "0x2e", "0xd7", "0x8e", "0x75"],
  ]
  guid_lis2 = [
    [0x615E6021, 0x603D, 0x4124, 0xB7, 0xEA, 0xC4, 0x8A, 0x37, 0x37, 0xBA, 0xCD],
    [0xe3e49b8d, 0x1987, 0x48d0, 0x9a, 0x1, 0xed, 0xa1, 0x79, 0xca, 0xb, 0xd6],
    [0xABBCE13D, 0xE25A, 0x4d9f, 0xA1, 0xF9, 0x2F, 0x77, 0x10, 0x78, 0x68, 0x92],
    [0xc09c81cb, 0x31e9, 0x4de6, 0xa9, 0xf9, 0x17, 0xa1, 0x44, 0x35, 0x42, 0x45],
    [0x6B6FD380, 0x2C55, 0x42C6, 0x98, 0xBF, 0xCB, 0xBC, 0x5A, 0x9A, 0xA6, 0x66],
    [0x5c0083db, 0x3f7d, 0x4b20, 0xac, 0x9b, 0x73, 0xfc, 0x65, 0x1b, 0x25, 0x03],
    [0x5498AB03, 0x63AE, 0x41A5, 0xB4, 0x90, 0x29, 0x94, 0xE2, 0xDA, 0xC6, 0x8D],
    [0xaec3ff43, 0xa70f, 0x4e01, 0xa3, 0x4b, 0xee, 0x1d, 0x11, 0xaa, 0x21, 0x69],
    [0xBCEA6548, 0xE204, 0x4486, 0x8F, 0x2A, 0x36, 0xE1, 0x3C, 0x78, 0x38, 0xCE],
    [0x22819110, 0x7f6f, 0x4852, 0xb4, 0xbb, 0x13, 0xa7, 0x70, 0x14, 0x9b, 0x0c],
    [0xCB105C8B, 0x3B1F, 0x4117, 0x99, 0x3B, 0x6D, 0x18, 0x93, 0x39, 0x37, 0x16],
    [0xE6A7A1CE, 0x5881, 0x4b49, 0x80, 0xBE, 0x69, 0xC9, 0x18, 0x11, 0x68, 0x5C],
    [0x21535212, 0x83d1, 0x4d4a, 0xae, 0x58, 0x12, 0xf8, 0x4d, 0x1f, 0x71, 0x0d],
    [0x003e7b41, 0x98a2, 0x4be2, 0xb2, 0x7a, 0x6c, 0x30, 0xc7, 0x65, 0x52, 0x25],
    [0x1ae42876, 0x008f, 0x4161, 0xb2, 0xb7, 0x1c, 0xd, 0x15, 0xc5, 0xef, 0x43],
    [0x8C3D856A, 0x9BE6, 0x468E, 0x85, 0x0A, 0x24, 0xF7, 0xA8, 0xD3, 0x8E, 0x08]
  ]

  @property
  def bios_roms(self):
    bios_rom_location = self.bios_image_dir
    bios_roms = [os.path.join(bios_rom_location, bios_image) for bios_image in os.listdir(bios_rom_location) if self.is_valid_bios_image(bios_image)]
    stored_dump = self.get_online_bios_image
    if ONLINE_MODE and stored_dump:
      online_bios_image = os.path.join(bios_rom_location, "online_bios.bin")
      shutil.copy(stored_dump, online_bios_image)
      bios_roms = [online_bios_image] + bios_roms
    return bios_roms

  @property
  def lookup_guids(self):
    guid_lis = []
    # guid_lis = self.guid_lis1 + self.guid_lis2
    return guid_lis

  @unittest.skipIf(True, "Always skipping this...")
  def test_clean_dir(self):
    # remove all files from temp directory
    self.assertTrue(utils.clean_directory(self.temp_dir))

    files_in_temp_dir = [i for i in os.listdir(self.temp_dir) if os.path.isfile(i)]

    self.assertEqual(files_in_temp_dir, [])

  @unittest.skipIf(not PARSE_ALL, "Not Parsing all binaries as set on flag...")
  def test_parse_multiple_binaries(self):
    for bios_image in self.bios_roms:
      # self.log.info("{0}\n>>>>>>>>> PROCESSING IMAGE: {1} <<<<<<<<<\n{0}".format("=" * 50, bios_image))
      self.parse_image(bios_image=bios_image)

  @unittest.skipIf(PARSE_ALL, "Skipping individual test as parsing all...")
  def test_write_to_json(self):
    self.parse_image(self.bios_image)

  def test_replace_driver(self):
    self.replace_ffs(self.bios_image, self.new_driver_file, self.replaced_image_file)

  def parse_image(self, bios_image):
    self.log.info(f"{'=' * 50}\n>>>>>>>>> PROCESSING IMAGE: {bios_image} <<<<<<<<<\n{'=' * 50}")
    binary_file_name = os.path.splitext(bios_image)[0]  # get filename without extension
    platform = "_{}".format(sys.platform)
    output_file = os.path.join(self.bios_image_dir, "{}{}{}.json".format(binary_file_name, configurations.PY_VERSION, platform))  # create output json file to store
    base_address = 0x0  # base address to be specified
    # Initialize class instance
    uefi_parser = bios_fw_parser.UefiParser(bin_file=bios_image,
                                            parsing_level=0,
                                            base_address=base_address,
                                            guid_to_store=self.lookup_guids
                                            )
    # Override logging level
    uefi_parser.override_log_level(LOG_LEVEL)
    # parse binary
    output_dict = uefi_parser.parse_binary()
    output_dict = uefi_parser.sort_output_fv(output_dict)
    # write content to json file
    uefi_parser.write_result_to_file(output_file, output_dict=output_dict)
    # Validate whether content written in json or not
    self.assertGreater(os.path.getsize(output_file), 0)

    if uefi_parser.guid_to_store:
      # additional test for GUIDs to store
      result = uefi_parser.guid_store_dir  # result of passed guid
      user_guid_out_file = os.path.join(result, "{}{}{}_guids.json".format(binary_file_name, configurations.PY_VERSION, platform))
      # Store guid stored result to json file
      uefi_parser.write_result_to_file(user_guid_out_file, output_dict=uefi_parser.stored_guids)
      # Validate whether content written in json or not
      self.assertGreater(os.path.getsize(user_guid_out_file), 0)

  def replace_ffs(self, bios_image, driver_image, replaced_image):
    self.log.info(f"{'=' * 50}\n>>>>>>>>> REPLACING DRIVER: {driver_image} <<<<<<<<<\n{'=' * 50}")
    uefi_parser = bios_fw_parser.UefiParser(bin_file=bios_image,  # binary file to parse
                                parsing_level=0,  # parsing level to manage number of parsing features
                                base_address=0,  # (optional) provide base address of bios FV region to start the parsing (default 0x0)
                                guid_to_store=[]  # if provided the guid for parsing then parser will look for every GUID in the bios image
                                )

    newffs_parser = bios_fw_parser.UefiParser(bin_file=driver_image,  # binary file to parse
                                    parsing_level=0,  # parsing level to manage number of parsing features
                                    base_address=0,  # (optional) provide base address of bios FV region to start the parsing (default 0x0)
                                    guid_to_store=[]  # if provided the guid for parsing then parser will look for every GUID in the bios image
                                    )

    # parse bios image into a binary_tree
    bios_output_dict = uefi_parser.parse_binary()

    # parse driver ffs image into a binary tree node
    ffs_output_dict = newffs_parser.parse_binary()
    # get the target ffs guid through ffs file, extract the target tree node
    TargetFfsGuid = newffs_parser.binary_tree.Position.ChildNodeList[0].Data.Name
    newffsnode = newffs_parser.binary_tree.Position.ChildNodeList[0]

    # replace the target ffs with new one
    uefi_parser.find_ffs_node(TargetFfsGuid)
    uefi_parser.ReplaceFfs(newffsnode, uefi_parser.TargetFfsList[0])
    uefi_parser.binary_tree.WholeTreeData = b''
    uefi_parser.Encapsulate_binary(uefi_parser.binary_tree)
    uefi_parser.dump_binary(replaced_image)

  def test_compare_with_old(self):
    for bios_image in self.bios_roms:
      with open(bios_image, 'rb') as BiosBinFile:
        BiosBinListBuff = list(BiosBinFile.read())
      BiosEnd = len(BiosBinListBuff)
      with open(PrintLogFile, "w") as LogFile:
        ProcessBin(BiosBinListBuff=BiosBinListBuff, BiosFvBase=0x00, Files2saveGuidList=self.lookup_guids, LogFile=LogFile, BiosRegionEnd=BiosEnd)


class OnlineTest(UefiParserTest):
  @property
  def bios_roms(self):
    bios_rom_location = self.bios_image_dir
    stored_dump = self.get_online_bios_image
    bios_roms = []
    if stored_dump:
      online_bios_image = os.path.join(bios_rom_location, "online_bios.bin")
      shutil.copy(stored_dump, online_bios_image)
      bios_roms = [online_bios_image]
    return bios_roms


class OfflineTest(UefiParserTest):
  @property
  def bios_roms(self):
    bios_rom_location = self.bios_image_dir
    bios_roms = [os.path.join(bios_rom_location, bios_image) for bios_image in os.listdir(bios_rom_location) if self.is_valid_bios_image(bios_image)]
    return bios_roms


if __name__ == "__main__":
  unittest.main()
