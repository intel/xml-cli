# -*- coding: utf-8 -*-

# Built-in imports
import os
from random import SystemRandom
import unittest

# Custom imports
from collections import namedtuple

from .UnitTestHelper import *
from xmlcli.common import utils
from xmlcli.common import configurations
from xmlcli import XmlCli as cli
from xmlcli.common.logger import log

try:
  from defusedxml import ElementTree as ET
except ModuleNotFoundError as e:
  log.warn("You are using ElementTree to parse untrusted XML data which is known to be vulnerable to XML attacks")
  from xml.etree import ElementTree as ET

__author__ = "Gahan Saraiya"

sys_random = SystemRandom()
SKIP_RANDOM_KNOB_TESTING = TEST_SUITE_CONFIG.getboolean("KNOB_TESTING", "SKIP_RANDOM_KNOB_TESTING")
SKIP_BATCH_KNOB_TESTING = TEST_SUITE_CONFIG.getboolean("KNOB_TESTING", "SKIP_BATCH_KNOB_TESTING")
SKIP_INDIVIDUAL_KNOB_TESTING = TEST_SUITE_CONFIG.getboolean("KNOB_TESTING", "SKIP_INDIVIDUAL_KNOB_TESTING")
MAXIMUM_RANDOM_KNOBS_PER_TYPE = TEST_SUITE_CONFIG.getint("KNOB_TESTING", "MAXIMUM_RANDOM_KNOBS_PER_TYPE")
KNOB_FILE_TESTING = TEST_SUITE_CONFIG.get("KNOB_TESTING", "KNOB_FILE_TESTING")
UEFI_NVAR_XML_LOCATION = TEST_SUITE_CONFIG.get("UEFI_NVAR_TESTING", "UEFI_NVAR_XML_LOCATION")
# if any of the string contains in either nvar name, knob name, prompt or in bios path, it will be ignored
IGNORE_RANDOM_TESTING = ["XmlCli", "SecureBoot", "BootOrder", "BootFirstToShell", "setShellFirst", "XmlCliSupport", "PublishSetupPgPtr"]


class XmlCliTest(UnitTestHelper):
  # bios_rom = r"C:\bios_images\ADL_FSP_0496_00_D.rom"  # specify BIOS binary file path
  def setUp(self):
    # Always Executed first...
    self.log.info("Initializing required setup for test")
    # Execution pipeline for testing the knobs!
    self.KnobTestingExecutionPipeLine = namedtuple("ExecutionPipeLine", ["method", "expected_status", "require_args"])
    self.knobs_by_nvar_type = {}
    self.knob_testing_execution_pipeline = [
      self.KnobTestingExecutionPipeLine(cli.CvReadKnobs, [1], True),
      self.KnobTestingExecutionPipeLine(cli.CvProgKnobs, [0], True),
      self.KnobTestingExecutionPipeLine(cli.CvReadKnobs, [0], True),
      self.KnobTestingExecutionPipeLine(cli.CvLoadDefaults, [0], False),
      self.KnobTestingExecutionPipeLine(cli.CvReadKnobs, [1], True),
      self.KnobTestingExecutionPipeLine(cli.CvRestoreModifyKnobs, [0], True),
      self.KnobTestingExecutionPipeLine(cli.CvReadKnobs, [0], True),
      self.KnobTestingExecutionPipeLine(cli.CvLoadDefaults, [0], False),
      self.KnobTestingExecutionPipeLine(cli.CvReadKnobs, [1], True)
    ]
    self.knob_testing_execution_pipeline_lite = [
      self.KnobTestingExecutionPipeLine(cli.ReadKnobsLite, [1], True),
      self.KnobTestingExecutionPipeLine(cli.ProgKnobsLite, [0], True),
      self.KnobTestingExecutionPipeLine(cli.ReadKnobsLite, [0], True),
      self.KnobTestingExecutionPipeLine(cli.LoadDefaultsLite, [0], False),
      self.KnobTestingExecutionPipeLine(cli.ReadKnobsLite, [1], True),
      self.KnobTestingExecutionPipeLine(cli.ResModKnobsLite, [0], True),
      self.KnobTestingExecutionPipeLine(cli.ReadKnobsLite, [0], True),
      self.KnobTestingExecutionPipeLine(cli.LoadDefaultsLite, [0], False),
      self.KnobTestingExecutionPipeLine(cli.ReadKnobsLite, [1], True)
    ]
    self.ignore_resource_warning()

  def pick_knobs_to_filter(self, xml_file=None, min_knob=5):
    """From given knobs xml, pick random knobs of each type

    :param xml_file: absolute XML file path
    :param min_knob: number of knobs to be picked from each knob type
    :return: dictionary of randomly picked knobs by keys!
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    xml_dict = utils.etree_to_dict(root)
    biosknobs = xml_dict.get("SYSTEM", {}).get("biosknobs", {}).get("knob", [])
    knobs_by_nvar = {}
    self.knobs_by_nvar_type = {}
    random_picked_knobs = []
    # filter knobs by varstore index and save to dict
    for knob in biosknobs:
      if "@varstoreIndex" in knob:
        for ignore_val in IGNORE_RANDOM_TESTING:
          _ignore_val = ignore_val.lower()
          if (_ignore_val in knob["@name"].lower()
            or _ignore_val in knob.get("@prompt", "").lower()
            or _ignore_val in knob.get("@Nvar", "").lower()
            or _ignore_val in knob.get("@SetupPgPtr", "").lower()):
            # In case of value to be ignored found in any of setup nvar name, prompt or knob name or setup page pointer
            # then that knob will not be considered as to be added
            break
          else:
            knobs_by_nvar.setdefault(knob['@varstoreIndex'], []).append(knob)
    # filter knobs within nvar by type and save to dict
    for varstore_index in knobs_by_nvar:
      self.knobs_by_nvar_type[varstore_index] = {}

      [self.knobs_by_nvar_type[varstore_index].setdefault(i['@setupType'], []).append(i) for i in knobs_by_nvar[varstore_index] if '@setupType' in i]
      # randomly pick knob of every kind
      for k, v in self.knobs_by_nvar_type[varstore_index].items():
        random_picked_knobs += sys_random.choices(v, k=min(min_knob, len(v)))
    return random_picked_knobs

  def configure_knobs_for_test(self, xml_file):
    test_knob_values = []
    knobs = self.pick_knobs_to_filter(xml_file=xml_file, min_knob=MAXIMUM_RANDOM_KNOBS_PER_TYPE)
    for knob in knobs:
      knob_type = knob["@setupType"]
      _val = knob["@CurrentVal"]
      if knob_type == "numeric":
        _min = int(knob["@min"], 16)
        _max = int(knob["@max"], 16)
        val = int(_val, 16)
        while val == int(_val, 16):
          val = _min + sys_random.getrandbits(len(bin(_max)[2:]))
        test_knob_values.append("{}={}".format(knob["@name"], val))
      elif knob_type == "oneof":
        choices = [int(option["@value"], 16) for option in knob["options"]["option"]]
        val = int(knob["@CurrentVal"], 16)
        while val == int(knob["@CurrentVal"], 16):
          val = sys_random.choice(choices)
        test_knob_values.append("{}={}".format(knob["@name"], val))
      elif knob_type == "checkbox":
        val = int(not int(knob["@CurrentVal"], 16))
        test_knob_values.append("{}={}".format(knob["@name"], val))
    return test_knob_values


class OnlineTest(XmlCliTest):
  def setUp(self):
    super(OnlineTest, self).setUp()
    cli.clb._setCliAccess(self.access_method)
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig, disable_online_mode=True))
    status = cli.clb.ConfXmlCli()
    if status != 0:
      global ONLINE_MODE
      ONLINE_MODE = False
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))

  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_savexml(self):
    self.log.info(f"{'=' * 50}\nTesting savexml\n{'=' * 50}")
    cli.savexml()
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))

    return True

  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_duplicate_knobs(self):
    self.log.info(f"{'=' * 50}\nTesting existence of duplicate knobs in XML\n{'=' * 50}")
    cli.savexml()
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))
    duplicate_knob_lis = cli.prs.find_duplicates(cli.clb.PlatformConfigXml)
    self.assertEqual(duplicate_knob_lis, [], "Duplicate knobs found!! Total {} duplicate knobs in XML".format(len(duplicate_knob_lis)))

    return True

  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_knobs(self):
    self.log.info(f"{'=' * 50}\nTesting CvProgKnobs\n{'=' * 50}")

    status = cli.CvReadKnobs("XmlCliSupport=1")
    self.assertIn(cli.clb.LastErrorSig, [0, 1], self.get_error_string(cli.clb.LastErrorSig, "Return Status: {}".format(status)))
    status = cli.CvRestoreModifyKnobs("XmlCliSupport=1")
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig, "Return Status: {}".format(status)))
    status = cli.CvProgKnobs("XmlCliSupport=1")
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig, "Return Status: {}".format(status)))
    status = cli.CvProgKnobs("BootFirstToShell=1")
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig, "Return Status: {}".format(status)))
    status = cli.CvLoadDefaults()
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig, "Return Status: {}".format(status)))
    cli.CvRestoreModifyKnobs("BootFirstToShell=1")
    status = cli.CvProgKnobs("BootFirstToShell=0")
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig, "Return Status: {}".format(status)))

    return True

  @unittest.skipIf(SKIP_RANDOM_KNOB_TESTING or SKIP_INDIVIDUAL_KNOB_TESTING, "check tests.config file, you may have disabled this test execution")
  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_knob_modification(self):
    self.log.info(f"{'=' * 50}\nTesting Knob Modifications by knobs\n{'=' * 50}")
    cli.savexml()
    knobs_for_test = self.configure_knobs_for_test(xml_file=cli.clb.PlatformConfigXml)
    self.log.info(f"Testing Below settings:\n{knobs_for_test}")

    # by knob testing
    for test_knob in knobs_for_test:
      for pipe in self.knob_testing_execution_pipeline:
        self.log.info(f">> Running cmd: {pipe.method} settings for: {test_knob}")
        self.log.debug(f"Executing: {pipe.method}('{test_knob}')")
        status = pipe.method(test_knob) if pipe.require_args else pipe.method()
        self.log.debug(f"Status: {status}")
        self.assertIn(status, pipe.expected_status, self.get_error_string(cli.clb.LastErrorSig, prefix_err_msg="[Status: {}] ".format(status)))

    return True

  @unittest.skipIf(SKIP_RANDOM_KNOB_TESTING or SKIP_BATCH_KNOB_TESTING, "check tests.config file, you may have disabled this test execution")
  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_knob_modification_batch(self):
    self.log.info(f"{'=' * 50}\nTesting Knob Modifications in batch\n{'=' * 50}")
    cli.savexml()
    knobs_for_test = self.configure_knobs_for_test(xml_file=cli.clb.PlatformConfigXml)
    self.log.info(f"Testing Below settings:\n{knobs_for_test}")
    batch_test_arg = ','.join(knobs_for_test)
    # batch testing
    for pipe in self.knob_testing_execution_pipeline:
      self.log.info(f">> Running cmd: {pipe.method} settings for: {batch_test_arg}")
      self.log.debug(f"Executing: {pipe.method}('{batch_test_arg}')")
      status = pipe.method(batch_test_arg) if pipe.require_args else pipe.method()
      self.log.debug(f"Status: {status}")
      self.assertIn(status, pipe.expected_status, self.get_error_string(cli.clb.LastErrorSig, prefix_err_msg="[Status: {}] ".format(status)))

    return True

  @unittest.skipIf(SKIP_RANDOM_KNOB_TESTING or SKIP_BATCH_KNOB_TESTING, "check tests.config file, you may have disabled this test execution")
  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_restore_modify_knobs(self):
    self.log.info(f"{'=' * 50}\nTesting Restore modify knobs\n{'=' * 50}")
    cli.savexml()
    self.pick_knobs_to_filter(xml_file=cli.clb.PlatformConfigXml, min_knob=MAXIMUM_RANDOM_KNOBS_PER_TYPE)
    knobs_for_test = self.configure_knobs_for_test(xml_file=cli.clb.PlatformConfigXml)
    self.log.info(f"Testing Below settings:\n{knobs_for_test}")
    # restore only 2 knob
    status = cli.CvRestoreModifyKnobs(','.join(knobs_for_test[:2]))
    self.log.debug(f"Status: {status}")
    self.assertIn(status, [0], self.get_error_string(cli.clb.LastErrorSig, prefix_err_msg="[Status: {}] ".format(status)))
    # read all other knobs, should be failed, with return status 1
    status = cli.CvReadKnobs(','.join(knobs_for_test[2:]))
    self.log.debug(f"Status: {status}")
    self.assertIn(status, [1], self.get_error_string(cli.clb.LastErrorSig, prefix_err_msg="[Status: {}] ".format(status)))
    # restore all the knobs
    status = cli.CvRestoreModifyKnobs(','.join(knobs_for_test))
    self.log.debug(f"Status: {status}")
    self.assertIn(status, [0], self.get_error_string(cli.clb.LastErrorSig, prefix_err_msg="[Status: {}] ".format(status)))
    # restore all the knobs, should pass with return status 0
    status = cli.CvReadKnobs(','.join(knobs_for_test))
    self.log.debug(f"Status: {status}")
    self.assertIn(status, [0], self.get_error_string(cli.clb.LastErrorSig, prefix_err_msg="[Status: {}] ".format(status)))

    return True

  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_get_set_var_legacy(self):
    self.log.info(f"{'=' * 50}\nTesting GetSetVar legacy\n{'=' * 50}")

    status = cli.GetSetVar('get', 0, '', 'SADS', '0x92daaf2f-0xc02b-0x455b-0xb2-0xec-0xf5-0xa3-0x59-0x4f-0x4a-0xea')
    self.assertIn(status, [0, 1], self.get_error_string(cli.clb.LastErrorSig))
    status = cli.GetSetVar("set", 0, "", "SSDBLINK0", "0x5ce47087-0x8ac7-0x493a-0x9f-0xc0-0xc5-0xe1-0x25-0x5a-0x5c-0x73", "0x07", "0x08", "00140401000c0002")
    self.assertEqual(status, 0, self.get_error_string(cli.clb.LastErrorSig))
    status = cli.GetSetVar("get", 0, "", "SSDBLINK0", "0x5ce47087-0x8ac7-0x493a-0x9f-0xc0-0xc5-0xe1-0x25-0x5a-0x5c-0x73")
    self.assertEqual(status, 0, self.get_error_string(cli.clb.LastErrorSig))

    return True

  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_get_set_var(self):
    self.log.info(f"{'=' * 50}\nTesting get_set_var\n{'=' * 50}")

    # Passing argument via command line
    result = cli.get_set_var(
      operation="get",
      nvar_name="SADS",
      nvar_guid="0x92daaf2f-0xc02b-0x455b-0xb2-0xec-0xf5-0xa3-0x59-0x4f-0x4a-0xea",
      display_result=True
    )
    status = 0 if result and isinstance(result, dict) else 1
    self.assertIn(status, [0, 1], self.get_error_string(cli.clb.LastErrorSig))

    # Passing argument via xml
    if os.path.exists(os.path.abspath(UEFI_NVAR_XML_LOCATION)):
      xml_location = os.path.abspath(UEFI_NVAR_XML_LOCATION)
    else:
      xml_location = os.path.join(configurations.XMLCLI_DIR, UEFI_NVAR_XML_LOCATION)
    self.log.info(f"Xml Location for Uefi Var: {xml_location}")
    if os.path.exists(xml_location):
      result = cli.get_set_var(
        operation="set",
        xml_file=xml_location,
        display_result=True
      )
      status = 0 if result and isinstance(result, dict) else 1
      self.assertEqual(status, 0, self.get_error_string(cli.clb.LastErrorSig))

      result = cli.get_set_var(
        operation="get",
        xml_file=xml_location,
        display_result=True
      )
      status = 0 if result and isinstance(result, dict) else 1
      self.assertEqual(status, 0, self.get_error_string(cli.clb.LastErrorSig))

      result = cli.get_set_var(
        operation="gms",
        xml_file=xml_location,
        display_result=True
      )
      status = 0 if result and isinstance(result, dict) else 1
      self.assertEqual(status, 0, self.get_error_string(cli.clb.LastErrorSig))

    return True

  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_read_memory(self):
    self.log.info(f"{'=' * 50}\nTesting Memory Reading\n{'=' * 50}")

    cli.clb.InitInterface()
    hex(cli.clb.ReadMSR(0, 0x8B))
    hex(cli.clb.ReadMSR(0, 0x1A0))
    hex(cli.clb.ReadMSR(0, 0x35))
    cli.clb.readallcmos()

    dram_address = cli.clb.GetDramMbAddr()
    cli.clb.memdump(dram_address, 0x80)
    cli.clb.memdump(dram_address, 0x80, 1)
    cli.clb.memdump(dram_address, 0x80, 2)
    cli.clb.memdump(dram_address, 0x80, 4)
    cli.clb.memdump(dram_address, 0x80, 8)
    cli.clb.memdump(dram_address, 0x66, 1)
    cli.clb.memdump(dram_address, 0x66, 2)
    cli.clb.memdump(dram_address, 0x66, 4)
    cli.clb.memdump(dram_address, 0x5F, 8)
    cli.clb.memdump(dram_address, 0x5F, 1)
    cli.clb.memdump(dram_address, 0x5F, 2)
    cli.clb.memdump(dram_address, 0x5F, 4)
    cli.clb.memdump(dram_address, 0x5F, 8)

    return True

  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_savexml_lite(self):
    self.log.info(f"{'=' * 50}\nTesting savexml lite\n{'=' * 50}")

    cli.savexmllite()
    self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))

    return True

  @unittest.skipIf(SKIP_RANDOM_KNOB_TESTING or SKIP_INDIVIDUAL_KNOB_TESTING, "check tests.config file, you may have disabled this test execution")
  @unittest.skipUnless(LITE_FEATURE_TESTING, "Lite Feature execution is disabled in config file")
  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_knob_modification_lite(self):
    self.log.info(f"{'=' * 50}\nTesting knob modification lite\n{'=' * 50}")

    cli.savexml()
    knobs_for_test = self.configure_knobs_for_test(xml_file=cli.clb.PlatformConfigXml)
    # knobs_for_test = ["EnableCrashLog=1", "XmlCliSupport=1"]
    self.log.info(f"Testing Below settings:\n{knobs_for_test}")

    # by knob testing
    for test_knob in knobs_for_test:
      for idx, pipe in enumerate(self.knob_testing_execution_pipeline_lite):
        self.log.info(f">> Running cmd-{idx}: {pipe.method} settings for: {test_knob}")
        self.log.debug(f"Executing: {pipe.method}('{test_knob}')")
        status = pipe.method(test_knob) if pipe.require_args else pipe.method()
        self.log.debug(f"Status: {status}")
        status = 0 if status == 0 else 1
        self.assertIn(status, pipe.expected_status, self.get_error_string(cli.clb.LastErrorSig, prefix_err_msg="[Status: {}] ".format(status)))

    return True

  @unittest.skipIf(SKIP_RANDOM_KNOB_TESTING or SKIP_BATCH_KNOB_TESTING, "check tests.config file, you may have disabled this test execution")
  @unittest.skipUnless(LITE_FEATURE_TESTING, "Lite Feature execution is disabled in config file")
  @unittest.skipUnless(ONLINE_MODE, "`ONLINE MODE` is disabled")
  def test_online_knob_modification_batch_lite(self):
    self.log.info(f"{'=' * 50}\nTesting Knob Modifications in batch with Lite mode\n{'=' * 50}")
    cli.savexml()
    knobs_for_test = self.configure_knobs_for_test(xml_file=cli.clb.PlatformConfigXml)
    self.log.info(f"Testing Below settings:\n{knobs_for_test}")
    batch_test_arg = ','.join(knobs_for_test)
    # batch testing
    for idx, pipe in enumerate(self.knob_testing_execution_pipeline_lite):
      self.log.info(f">> Running cmd-{idx}: {pipe.method} settings for: {batch_test_arg}")
      self.log.debug(f"Executing: {pipe.method}('{batch_test_arg}')")
      status = pipe.method(batch_test_arg) if pipe.require_args else pipe.method()
      self.log.debug(f"Status: {status}")
      status = 0 if status == 0 else 1
      self.assertIn(status, pipe.expected_status, self.get_error_string(cli.clb.LastErrorSig, prefix_err_msg="[Status: {}] ".format(status)))

    return True


class OfflineTest(XmlCliTest):
  def setUp(self):
    super(OfflineTest, self).setUp()

  @unittest.skipUnless(OFFLINE_MODE, "Offline Mode is disabled")
  def test_offline_savexml(self):
    self.ignore_resource_warning()
    self.log.info(f"{'=' * 50}\nTesting savexml\n{'=' * 50}")
    for bios_rom in self.bios_roms:
      self.log.info(f"{'=' * 50}\n>>>>>>>>> PROCESSING IMAGE: {bios_rom} <<<<<<<<<\n{'=' * 50}")
      xml_location = os.path.join(os.path.dirname(bios_rom), os.path.basename(bios_rom) + ".xml")
      cli.savexml(filename=xml_location, BiosBin=bios_rom)
      self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))

      return True

  @unittest.skipUnless(OFFLINE_MODE, "Offline Mode is disabled")
  def test_offline_duplicate_knobs(self):
    self.ignore_resource_warning()
    self.log.info(f"{'=' * 50}\nTesting existence of duplicate knobs in XML\n{'=' * 50}")
    for bios_rom in self.bios_roms:
      self.log.info(f"{'=' * 50}\n>>>>>>>>> PROCESSING IMAGE: {bios_rom} <<<<<<<<<\n{'=' * 50}")
      xml_location = os.path.join(os.path.dirname(bios_rom), os.path.basename(bios_rom) + ".xml")
      cli.savexml(filename=xml_location, BiosBin=bios_rom)
      self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))
      duplicate_knob_lis = cli.prs.find_duplicates(xml_location)
      self.assertEqual(duplicate_knob_lis, [], "Duplicate knobs found!! Total {} duplicate knobs in XML".format(len(duplicate_knob_lis)))

    return True

  @unittest.skipUnless(OFFLINE_MODE, "Offline Mode is disabled")
  def test_offline_program_knobs(self):
    self.ignore_resource_warning()
    self.log.info(f"{'=' * 50}\nTesting CvProgKnobs\n{'=' * 50}")
    for bios_rom in self.bios_roms:
      self.log.info(f"{'=' * 50}\n>>>>>>>>> PROCESSING IMAGE: {bios_rom} <<<<<<<<<\n{'=' * 50}")
      utils.clean_directory(cli.clb.TempFolder)
      cmd = "XmlCliSupport=1"
      cli.CvProgKnobs(cmd, bios_rom)
      self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))
      if not cli.clb.OutBinFile:
        # if programmed change already exist then out bin file may not be created;
        # in which case we revert the program value and test again
        cmd = "XmlCliSupport=0"
        cli.CvProgKnobs(cmd, bios_rom)
        self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))
      cli.CvProgKnobs(cmd, cli.clb.OutBinFile)
      self.assertEqual(cli.clb.LastErrorSig, 0, self.get_error_string(cli.clb.LastErrorSig))

      return True



if __name__ == "__main__":
  unittest.main()
