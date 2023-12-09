#!/usr/bin/env python
__author__ = ["Gahan Saraiya", "ashinde"]

# Built-in Imports
import hmac
import hashlib

# Custom Imports
from xmlcli import XmlCliLib as clb
from xmlcli import UefiFwParser as fwp
from xmlcli.common.logger import log

DIGEST_SIZE = int(256 / 8)  # 32 bytes (0x20)

GUID_SIZE = 0x10
KEY_OFFSET = GUID_SIZE
KEY_SIZE = 0x20  # Random number generated to be feed as key
DIGEST_OFFSET = KEY_OFFSET + KEY_SIZE  # 0x30

XMLCLI_REQUEST_VALIDATED_SIG1 = 0xB05ADC0D3EB0079A
XMLCLI_REQUEST_VALIDATED_SIG2 = 0xD095BE110E9AB1ED
RESPONSE_READY_SIG_SIZE = 0x8


__version__ = "2.0.0"


class XmlCliEnable(object):
  def __init__(self):
    self.search1 = (fwp.gXmlCliInterfaceBufferGuid[2] << 48) + (fwp.gXmlCliInterfaceBufferGuid[1] << 32) + fwp.gXmlCliInterfaceBufferGuid[0]
    self.search2 = (fwp.gXmlCliInterfaceBufferGuid[10] << 56) + (fwp.gXmlCliInterfaceBufferGuid[9] << 48) + (fwp.gXmlCliInterfaceBufferGuid[8] << 40) + (fwp.gXmlCliInterfaceBufferGuid[7] << 32) + (fwp.gXmlCliInterfaceBufferGuid[6] << 24) + (fwp.gXmlCliInterfaceBufferGuid[5] << 16) + (fwp.gXmlCliInterfaceBufferGuid[4] << 8) + fwp.gXmlCliInterfaceBufferGuid[3]

  def buffer_matched(self, match1, match2):
    return bool(match1 == self.search1 and match2 == self.search2)

  def _write_hash_key(self, interface_address):
    hash_buffer_found = False
    buffer_match = False
    for AdrCount in range(0, 0xFFFF, 0x40):
      # Search for valid address by step of 0x40 bytes alignment
      _match1 = int(clb.memread(interface_address + AdrCount, 8))
      _match2 = int(clb.memread(interface_address + AdrCount + 8, 8))
      buffer_match = self.buffer_matched(_match1, _match2)
      if buffer_match:
        hash_buffer_found = True
        interface_address = interface_address + AdrCount
        break

    if hash_buffer_found:
      if buffer_match:
        key = clb.memBlock(interface_address + KEY_OFFSET, DIGEST_SIZE)
        digest = hmac.new(key, bytearray([0xee, 0x83, 0x84, 0x5b, 0xf6, 0x0a, 0xa0, 0x4c, 0x7c, 0x80, 0x31, 0x0d, 0xef, 0xd9, 0x4a, 0x32]), hashlib.sha256).digest()
        # digest returns byte object in python3 but string object in python2
        for idx, _val in enumerate(digest):
          clb.memwrite(interface_address + DIGEST_OFFSET + idx, 1, _val)

    if hash_buffer_found:
      return 0, interface_address
    else:
      return 1, 0

  def enable_xmlcli(self):
    clb.InitInterface()
    clb.writeIO(0x72, 1, 0xF0)
    result0 = clb.readIO(0x73, 4) & 0xFF
    clb.writeIO(0x72, 1, 0xF1)
    result1 = clb.readIO(0x73, 4) & 0xFF
    if (result0 == 0xFF and result1 == 0xFF) or (result0 == 0x0 and result1 == 0x0):
      clb.writeIO(0x70, 1, 0x78)
      result0 = int(clb.readIO(0x71, 1) & 0xFF)
      clb.writeIO(0x70, 1, 0x79)
      result1 = int(clb.readIO(0x71, 1) & 0xFF)
    interface_address = (result1 << 24) + (result0 << 16)
    shared_mailbox_sig1 = clb.memread((interface_address+clb.SHAREDMB_SIG1_OFF), 4)
    shared_mailbox_sig2 = clb.memread((interface_address+clb.SHAREDMB_SIG2_OFF), 4)
    if (shared_mailbox_sig1 == clb.SHAREDMB_SIG1) and (shared_mailbox_sig2 == clb.SHAREDMB_SIG2):
      version = clb.memread((interface_address+clb.CLI_SPEC_VERSION_MINOR_OFF), 4)
      if version >= 0x800:
        if clb.memread((interface_address + clb.LEGACYMB_SIG_OFF), 4) == clb.XML_CLI_DISABLED_SIG:
          interface_address = clb.memread((interface_address+clb.LEGACYMB_OFF), 4)
    status, interface_address = self._write_hash_key(interface_address)
    if status == 0:
      log.result("Enabling XmlCli Support")
      clb.triggerSMI(0xF6)
      clb.runcpu()
      clb.haltcpu(delay=2)
      response1 = clb.memread(interface_address + DIGEST_OFFSET, RESPONSE_READY_SIG_SIZE)
      if response1 != XMLCLI_REQUEST_VALIDATED_SIG1:
        clb.runcpu()
        clb.haltcpu(delay=4)
        response1 = clb.memread(interface_address + DIGEST_OFFSET, RESPONSE_READY_SIG_SIZE)
        if response1 != XMLCLI_REQUEST_VALIDATED_SIG1:
          clb.runcpu()
          clb.haltcpu(delay=4)
          response1 = clb.memread(interface_address + DIGEST_OFFSET, RESPONSE_READY_SIG_SIZE)
      response2 = clb.memread(interface_address + DIGEST_OFFSET + RESPONSE_READY_SIG_SIZE, RESPONSE_READY_SIG_SIZE)
      if (response1 == XMLCLI_REQUEST_VALIDATED_SIG1) and (response2 == XMLCLI_REQUEST_VALIDATED_SIG2):
        log.result("Enabled XmlCli support Successfully, Please Reboot..")
        clb.memwrite(interface_address + DIGEST_OFFSET, RESPONSE_READY_SIG_SIZE, 0)
        clb.memwrite(interface_address + DIGEST_OFFSET + RESPONSE_READY_SIG_SIZE, RESPONSE_READY_SIG_SIZE, 0)
        status = 0
      else:
        log.result("No Response, there was some problem, Aborting..")
        status = 1
    else:
      log.result("Interface Buffer Not Found, Aborting..")
      status = 1
    clb.CloseInterface()
    return status

  def validate_xmlcli_request(self):
    clb.InitInterface()
    status = 1
    # CMOS read on F0 and F1
    clb.writeIO(0x72, 1, 0xF0)
    result0 = clb.readIO(0x73, 4) & 0xFF
    clb.writeIO(0x72, 1, 0xF1)
    result1 = clb.readIO(0x73, 4) & 0xFF
    if (result0 == 0xFF and result1 == 0xFF) or (result0 == 0x0 and result1 == 0x0):
      # Fallback CMOS read on 0x78 and 0x79 for signature match
      clb.writeIO(0x70, 1, 0x78)
      result0 = int(clb.readIO(0x71, 1) & 0xFF)
      clb.writeIO(0x70, 1, 0x79)
      result1 = int(clb.readIO(0x71, 1) & 0xFF)
    interface_address = (result1 << 24) + (result0 << 16)
    hash_interface_address = interface_address
    shared_mailbox_sig1 = clb.memread(interface_address + clb.SHAREDMB_SIG1_OFF, 4)
    shared_mailbox_sig2 = clb.memread(interface_address + clb.SHAREDMB_SIG2_OFF, 4)
    if (shared_mailbox_sig1 == clb.SHAREDMB_SIG1) and (shared_mailbox_sig2 == clb.SHAREDMB_SIG2):
      shared_mailbox_entry1_sig = clb.memread(interface_address + clb.LEGACYMB_SIG_OFF, 4)
      if shared_mailbox_entry1_sig == clb.LEGACYMB_SIG:
        legacy_mailbox_offset = clb.memread(interface_address + clb.LEGACYMB_OFF, 4)
        if legacy_mailbox_offset > 0xFFFF:
          hash_interface_address = clb.memread(legacy_mailbox_offset + clb.LEGACYMB_XML_CLI_TEMP_ADDR_OFF, 4)
        else:
          hash_interface_address = clb.memread(
            interface_address + legacy_mailbox_offset + clb.LEGACYMB_XML_CLI_TEMP_ADDR_OFF, 4)
    status, interface_address = self._write_hash_key(hash_interface_address)
    clb.CloseInterface()
    return status


def EnableXmlCli():
  cli_instance = XmlCliEnable()
  return cli_instance.enable_xmlcli()


def XmlCliApiAuthenticate():
  cli_instance = XmlCliEnable()
  return cli_instance.validate_xmlcli_request()


if __name__ == "__main__":
  pass
