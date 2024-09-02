# -*- coding: utf-8 -*-

# Built-in imports
import os
import ctypes
import binascii
import logging
from collections import OrderedDict

# Custom imports
from .. import xmlclilib as clb
from . import utils


log = logging.getLogger(__name__)

NVAR_OPERATIONS = {
  "get": "0x0",
  "set": "0x1",
  "gms": "0x2",
  "getall": "0x9a"
}


def get_attribute_string(attribute_value):
  attribute = attribute_value if utils.is_integer(attribute_value) else utils.get_integer_value(attribute_value, base=16)
  attribute_string = f"0b{attribute:0>6b} "
  if attribute & 0b0001:
    attribute_string += ' | ' + 'Non Volatile'
  if (attribute & 0b0010) >> 1:
    attribute_string += ' | ' + 'Boot Time'
  if (attribute & 0b0100) >> 2:
    attribute_string += ' | '  'Run Time'
  if (attribute & 0b10000) >> 4:
    attribute_string += ' | '  'Authenticated'
  if not attribute_string:
    return "Unknown"
  return attribute_string


class NvarException(utils.XmlCliException):
  """Used to raise exception related to NVAR"""
  pass


def create_nvar_structure(nvar_name_length=1, data_length=0):
  class NvarDetails(utils.StructureHelper):
    _pack_ = 1
    _fields_ = [
      ("guid", utils.Guid),  # `16 bytes` indicating GUID of UEFI variable
      ("attributes", ctypes.c_uint32),  # `4 bytes` indicating attributes of UEFI variable
      ("size", ctypes.c_uint32),  # `4 bytes` size of UEFI variable
      ("status", ctypes.c_uint32),  # `4 bytes` status of Nvar status (determined whether nvar exists on Target System or not)
      ("operation", ctypes.c_uint8),  # `1 byte` indicates operation such as 00-Get, 01-Set, 02-GMS
      ("name", ctypes.ARRAY(ctypes.c_char, nvar_name_length)),  # `NULL terminated string` name of UEFI Variable
      ("null", ctypes.c_char),  # null character to represent end of string for name
      ("data", ctypes.ARRAY(ctypes.c_uint8, data_length))  # Knob data values of the nvar (set to zero by default) as not always necessary to read it!
    ]

    def nvar_key(self):
      return f"{self.nvar_name}_{self.get_guid()}"

    def get_guid(self):
      return utils.guid_formatter(self.guid.get_str(), string_format="xmlcli_mod")

    def get_attribute_string(self):
      return get_attribute_string(self.get_value("attributes"))

    def get_nvar_data(self):
      result = " ".join(f"{i:0>2x}" for i in self.data[:])
      return result if result else "N.A."

    def read_knob_data(self, start=None, end=None, endian="little"):
      data = self.data[start:end]
      if endian == "little":
        data = data[::-1]
      return self.array_to_int(data)

    def display_data(self, var_no=0, min_adjust=70):
      log.debug("#" * min_adjust)
      log.debug(f"{f' Displaying Data as Requested[NVAR:{var_no:0^2}] ' :#^{min_adjust}}")
      out_data = f'Name       = {self.get_value("name")}\n ' \
                 f'Guid       = {self.get_guid()}\n' \
                 f'Size       = {self.get_value("size")}\n' \
                 f'Attributes = {self.get_attribute_string()}\n' \
                 f'Operation  = {self.get_value("operation")}\n' \
                 f'Status     = {self.get_value("status")}\n' \
                 f'Data       = {self.get_nvar_data()}'
      log.debug(out_data)

  return NvarDetails()


def create_nvar_request_buffer(operation="get", xml_file=None, name="", guid="", attributes="0x0", size="0x0", nvar_data=None, nvar_dict=None, knob_string=None):
  """Create the Request buffer for one or more Nvars based on data passed.
  Input data can either be passed via xml file or argument to function

  :param operation: type of operation, must be either of "get", "set", "gms"
  :param xml_file: If provided then nvar details will only be read from xml and all other arguments will be ignored
  :param name: name of the NVAR
  :param guid: guid of the NVAR
  :param attributes: attributes of the NVAR (applicable if operation is `set` or `gms`)
  :param size: size of the NVAR (applicable if operation is `set` or `gms`)
  :param nvar_data: Nvar Data as hex string i.e. if size is 0x6 then nvar_data could be : `"000100020408"` (applicable if operation is `set` or `gms`)
  :param nvar_dict: Receive Nvar Dictionary from user
  :param knob_string: Alternative to nvar_data, especially for `gms`, allows to modify only specific knob value if not wish to provide the all knob values
  :return: bytearray of nvar data, nvar_dict if success else `False`
  """
  nvar_dict = nvar_dict if nvar_dict else OrderedDict()
  key = f"{name}_{guid}"
  operation_code = NVAR_OPERATIONS.get(operation.lower(), None)

  if nvar_dict:
    log.info("Parsing the user provided nvar_dict")
  elif xml_file:  # Parse xml file
    nvar_dict = utils.load_nvar_xml(xml_file=xml_file)
  elif name and guid:
    # Non Xml File
    nvar_dict[key] = {
      "name"       : name,
      "guid"       : guid,
      "size"       : utils.get_integer_value(size, base=16),
      "attributes" : attributes,
      "operation"  : operation_code,
      "status"     : 0x00,
      "knobs"      : {}
    }
    if nvar_data:  # Either Nvar Data must be passed (applicable to set and gms mode only)
      nvar_data_size = int(len(list(nvar_data)) / 2)
      if nvar_data_size != nvar_dict[key]["size"]:
        err_msg = f"NVRAM size: 0x{nvar_dict[key]['size']:x} does not match the data length of size: 0x{nvar_data_size:x}"
        log.error(err_msg)
        return bytearray(), {}
    elif knob_string:  # or pass the knob string (applicable to set and gms mode only)
      knob_list = list(open(knob_string, "r").read().split("\n")) if os.path.isfile(knob_string) else knob_string.split(",")
      for knob in knob_list:
        # parse knob details from the data values separated by `;`
        # name=Knob_1;knob_type="oneof";value="0x0";size="0x1";offset="0x0";description="content description"
        knob_content = {line.split("=")[0]: line.split("=")[1] for line in knob.split(";")}
        _offset = 0
        knob_details = {
          "name"         : knob_content["name"],
          "knob_type"    : knob_content["knob_type"],
          "value"        : utils.get_integer_value(knob_content["value"], base=16),
          "current_value": utils.get_integer_value(knob_content["value"], base=16),
          "size"         : utils.get_integer_value(knob_content["size"], base=16),
          "offset"       : utils.get_integer_value(knob_content.get("offset", _offset), base=16),
          "description"  : knob_content.get("description", knob_content["name"]),  # set description value to name if not specified
        }
        _offset += knob_details["size"]  # auto calculate offset for knob if not specified
        knob_key = knob_details["name"]
        nvar_dict[key]["knobs"][knob_key] = knob_details

  log.debug(f"using nvar_dict: \n{nvar_dict}")
  nvar_structure_lis = []  # store the nvar detailed structure component in the list
  request_buffer = bytearray()

  for key, nvar_details in nvar_dict.items():
    # create dynamic NVAR structure
    data_length = 0 if operation.lower() == "get" else utils.get_integer_value(nvar_details["size"], base=16)
    nvar_structure = create_nvar_structure(nvar_name_length=len(nvar_details["name"]), data_length=data_length)
    # assigning values to the structure
    nvar_structure.name = utils.convert_to_bytes(nvar_details["name"])
    nvar_structure.guid.read_guid(nvar_details["guid"])
    nvar_structure.size = utils.get_integer_value(nvar_details["size"], base=16)
    nvar_structure.attributes = utils.get_integer_value(nvar_details["attributes"], base=16)
    nvar_structure.operation = utils.get_integer_value(operation_code, base=16)
    nvar_structure.status = utils.get_integer_value(nvar_details.get("status", "0x00"), base=16)
    # store the nvar structure to the list
    nvar_structure_lis.append(nvar_structure)

    # Pull back the changes to nvar_dict
    nvar_dict[key]["status"] = nvar_structure.status
    nvar_dict[key]["operation"] = nvar_structure.operation

    if operation in ("set", "gms"):
      # Further processing require for set and gms operation
      nvar_knobs = [knob for key, knob in nvar_details["knobs"].items()]
      knob_data_buffer = bytearray()
      knobs_sorted_by_offset = sorted(nvar_knobs, key=lambda x: x["offset"])
      if nvar_details["knobs"]:
        for knob in knobs_sorted_by_offset:
          knob_data_buffer += utils.convert_to_bytes(utils.get_integer_value(knob["current_value"]), utils.get_integer_value(knob["size"]))
      elif not xml_file and nvar_data:
        knob_data_buffer += binascii.unhexlify(nvar_data)
      else:
        err_msg = "Invalid parameters, neither valid knob details nor nvar data is provided."
        log.error(err_msg)
      # In the event of reserved space or invalid data padding will be added to maintain nvar with reserved size
      log.debug("Constructing empty bytes to align NVAR region...")
      knob_data_buffer += bytearray(utils.get_integer_value(nvar_details["size"]) - utils.get_integer_value(len(knob_data_buffer)))
      # store the knob data buffer
      nvar_structure.data[:] = knob_data_buffer

    request_buffer += nvar_structure.get_bytes()

  return request_buffer, nvar_dict


def read_response_buffer(buffer_file=None, buffer_data=None, xml_file=None, nvar_dict=None, display_result=False):
  """Takes Buffer data file or buffer data itself as an input
  reads the buffer data according to the provided nvar_dict (generated from xml_file if not provided)

  :param buffer_file: absolute file path to buffer file
  :param buffer_data: already read buffer data in bytes
  :param xml_file: xml file which is to be referred for reading the buffer_data
  :param nvar_dict: nvar dictionary used to refer for reading the buffer_data
  :param display_result: Toggle control to decide whether to display the nvar details which is read or not
  :return: nvar_dict with updated values of: status of NVAR, current value of knob
  """
  if not buffer_data:
    if buffer_file:
      with open(buffer_file, "rb") as f:
        buffer_data = f.read()
    else:
      raise NvarException("Neither buffer data or file provided!")

  if not nvar_dict:
    nvar_dict = utils.load_nvar_xml(xml_file=xml_file)

  start = 0x00
  end = len(buffer_data)
  buffer_pointer = start

  buffer_data = utils.get_buffer(buffer_data)
  if buffer_pointer < end:
    buffer_data.seek(buffer_pointer)
    # read and update nvar dict
    for nvar_key, nvar_details in nvar_dict.items():
      nvar_struct = create_nvar_structure(len(nvar_details["name"]), utils.get_integer_value(nvar_details["size"], base=16))
      nvar_struct_data = nvar_struct.read_from(buffer_data)
      # update values of dict as per cli response buffer for Nvar(s)
      nvar_dict[nvar_key]["status"] = hex(nvar_struct_data.status)
      nvar_dict[nvar_key]["input_size"] = utils.get_integer_value(nvar_dict[nvar_key]["size"], base=16)
      nvar_dict[nvar_key]["size"] = nvar_struct_data.size
      nvar_dict[nvar_key]["data"] = list(nvar_struct_data.data)
      if nvar_dict[nvar_key]["name"] == nvar_struct_data.get_value("name") and nvar_dict[nvar_key]["guid"] == nvar_struct_data.get_guid():
        nvar_dict[nvar_key]["is_exist"] = bool(nvar_struct_data.status == 0)
        log.debug(nvar_struct_data)
        if utils.get_integer_value(nvar_dict[nvar_key]["size"], base=16) != nvar_struct_data.size:
          err_msg = f"Anomaly in size for nvar: {nvar_dict[nvar_key]}\nSize specified: {nvar_dict[nvar_key]['size']}\nSize in response: {nvar_struct_data.size}"
          log.warning(err_msg)
        if nvar_struct_data.size:
          knob_end = buffer_pointer + nvar_struct_data.size
          # Increment buffer pointer to skip nvar structure data!
          knob_offset = 0
          if display_result:
            nvar_struct_data.display_data()
          for knob_name, knob_details in nvar_dict[nvar_key]["knobs"].items():
            if buffer_pointer + knob_details["size"] <= knob_end <= end and knob_details["size"]:
              # current buffer region must enclosed by it's total size and shall not exceed the total response buffer size
              knob_size = utils.get_integer_value(knob_details["size"], base=16)
              knob_value = nvar_struct_data.data[knob_offset:knob_offset+knob_size]
              nvar_dict[nvar_key]["knobs"][knob_name]["current_value"] = nvar_struct_data.read_knob_data(knob_offset, knob_offset+knob_size)
              knob_offset += knob_size
              # store all values in dict as hex string
              nvar_dict[nvar_key]["knobs"][knob_name]["size"] = hex(nvar_dict[nvar_key]["knobs"][knob_name]["size"])
              nvar_dict[nvar_key]["knobs"][knob_name]["offset"] = hex(nvar_dict[nvar_key]["knobs"][knob_name]["offset"])
              if display_result:
                if nvar_dict[nvar_key]["knobs"][knob_name]["offset"] == "0x0":
                  print("|" + "-"*60 + "|")
                  print(f"|{'Offset':>6} | {'Name':^32} | {'Size':^6} | {'Value':^6} |")
                  print("|" + "-"*60 + "|")
                print(
                  f"|{nvar_dict[nvar_key]['knobs'][knob_name]['offset']:>6} "
                  f"| {nvar_dict[nvar_key]['knobs'][knob_name]['name']:^32} "
                  f"| {nvar_dict[nvar_key]['knobs'][knob_name]['size']:^6} "
                  f"| {nvar_dict[nvar_key]['knobs'][knob_name]['current_value']:^6} |"
                )
            else:
              err_msg = f"Anomaly to read size for knob: {knob_name}\n{knob_details}"
              log.error(err_msg)
      buffer_pointer += nvar_struct_data.cls_size
  # Finally return the nvar_dict which is having updated values!
  return nvar_dict


def get_set_var(operation="get", xml_file=None, knob_string="", nvar_name="", nvar_guid="", nvar_attrib="0x0", nvar_size="0x0", nvar_data="", nvar_dict=None, display_result=True):
  """Allows to read or create the nvar and modify the knob value of nvar

  Must require argument is operation
  for rest user can either provide xml_file, or nvar_dict or rest other arguments

  :param operation: type of operation, must be either of "get", "set", "gms"
  :param xml_file: If provided then nvar details will only be read from xml and all other arguments will be ignored
  :param knob_string: Alternative to nvar_data, especially for `gms`, allows to modify only specific knob value if not wish to provide the all knob values
  :param nvar_name: name of the NVAR
  :param nvar_guid: guid of the NVAR
  :param nvar_attrib: attributes of the NVAR (applicable if operation is `set` or `gms`)
  :param nvar_size: size of the NVAR (applicable if operation is `set` or `gms`)
  :param nvar_data: Nvar Data as hex string i.e. if size is 0x6 then nvar_data could be : `"000100020408"` (applicable if operation is `set` or `gms`)
  :param nvar_dict: Allows feeding python dictionary of the nvar data.
    sample dict could be as -
      OrderedDict({
        "SADS_0x92daaf2f-0xc02b-0x455b-0xb2-0xec-0xf5-0xa3-0x59-0x4f-0x4a-0xea": {
          "name"       : "SADS",
          "guid"       : "0x92daaf2f-0xc02b-0x455b-0xb2-0xec-0xf5-0xa3-0x59-0x4f-0x4a-0xea",
          "operation"  : uefi_variable.NVAR_OPERATIONS["get"],
          # This are default values below, has to keep in structure
          "size"       : 0,
          "attributes" : 0x07,
          "status"     : 0x00,
          "knobs"      : {}
        },
        "SSDBLINK0_0x5ce47087-0x8ac7-0x493a-0x9f-0xc0-0xc5-0xe1-0x25-0x5a-0x5c-0x73": {
          "name"       : "SSDBLINK0",
          "guid"       : "0x5ce47087-0x8ac7-0x493a-0x9f-0xc0-0xc5-0xe1-0x25-0x5a-0x5c-0x73",
          "operation"  : uefi_variable.NVAR_OPERATIONS["get"],
          # This are default values below, has to keep in structure
          "size"       : 0,
          "attributes" : 0x07,
          "status"     : 0x00,
          "knobs"      : {}
        },
      }
    )
  :param display_result: toggle whether to show the output result or not
  :return: dictionary containing updated status of the nvar (synced with bios NVRAM data values)
  """
  clb.LastErrorSig = 0x0
  nvar_request_buffer_file = os.path.join(clb.TempFolder, "NvarReqBuff.bin")
  nvar_response_buffer_file = os.path.join(clb.TempFolder, "NvarRespBuff.bin")
  operation_code = NVAR_OPERATIONS.get(operation, None)

  if not operation_code:
    err_msg = f"Invalid Operation!! (Valid Operations are: {', '.join(NVAR_OPERATIONS)}). ABORTING..."
    clb.LastErrorSig = 0x9E51  # GetSetVar: Invalid Operation
    raise NvarException(err_msg, error_code=clb.LastErrorSig)

  if operation == "getall":
    # system must have xmlcli_mod BIOS version >= 5
    log.debug(f"Operation: {operation} to be executed")
  else:
    request_buffer, nvar_dict = create_nvar_request_buffer(operation=operation, xml_file=xml_file, knob_string=knob_string, name=nvar_name,
                                                           guid=nvar_guid, attributes=nvar_attrib, size=nvar_size, nvar_data=nvar_data, nvar_dict=nvar_dict)

    if not request_buffer:
      # raise exception if request buffer not generated
      err_msg = "Request buffer not generated!!"
      raise NvarException(err_msg)

    with open(nvar_request_buffer_file, "wb") as f:
      f.write(request_buffer)

  # start cli interface
  clb.InitInterface()
  dram_mb_address = clb.GetDramMbAddr()  # Get DRAM mailbox address
  dram_shared_mb_buffer = clb.read_mem_block(dram_mb_address, 0x200)  # Read/save parameter buffer
  cli_request_buffer_address = clb.readclireqbufAddr(dram_shared_mb_buffer)
  cli_response_buffer_address = clb.readcliresbufAddr(dram_shared_mb_buffer)
  log.info(f"CLI Request Buffer Addr = 0x{cli_request_buffer_address:x}   CLI Response Buffer Addr = 0x{cli_response_buffer_address:x}")

  if cli_request_buffer_address == 0 or cli_response_buffer_address == 0:
    err_msg = "CLI buffers are not valid or not supported, Aborting due to Error!"
    clb.CloseInterface()
    clb.LastErrorSig = 0xC140  # XmlCli Req or Resp Buffer Address is Zero
    return NvarException(err_msg, error_code=clb.LastErrorSig)

  clb.ClearCliBuff(cli_request_buffer_address, cli_response_buffer_address)

  if operation == 'getall':
    clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4, 0)  # Set LoopCount to 0
    clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_BUFF_HEADER_SIZE, 8, 0)
    clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 0x08, 8, 0)
    clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 0x10, 8, 0)
    clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 0x18, 4, 0)
    clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 0x1C, 4, 0x9A)  # Set Operation as "getall"
  else:
    clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4, len(nvar_dict))
    log.info(f"Request Buffer Bin file used is: {nvar_request_buffer_file}")
    clb.load_data(nvar_request_buffer_file, cli_request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 4)

  clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_READY_CMD_OFF, 4, clb.GET_SET_VARIABLE_OPCODE)
  clb.memwrite(cli_request_buffer_address + clb.CLI_REQ_RES_READY_SIG_OFF, 4, clb.CLI_REQ_READY_SIG)
  log.info("CLI Mailbox programmed, issuing S/W SMI to program knobs...")

  status = clb.TriggerXmlCliEntry()  # trigger s/w SMI for CLI Entry
  if status:
    log.error("Error while triggering CLI Entry Point, Aborting....")
    clb.CloseInterface()
    return 1

  if clb.WaitForCliResponse(cli_response_buffer_address, 2, 3):
    log.error("CLI Response not ready, Aborting....: \nPossible cause: None of the nvar provided does not exists!!!")
    clb.CloseInterface()
    return 1

  if logger.LOG_LEVEL.lower() == "debug":
    # For debug use only, store cli buffer with address
    clb.memsave(os.path.join(clb.TempFolder, "cli_header_request_buff.bin"), cli_request_buffer_address, 0x100)
    clb.memsave(os.path.join(clb.TempFolder, "cli_header_response_buff.bin"), cli_response_buffer_address, 0x100)

  current_param_size = utils.get_integer_value(clb.memread(cli_response_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4))
  log.debug(f"current_param_size: {current_param_size}")
  if current_param_size:
    current_param_buffer = clb.read_mem_block(cli_response_buffer_address + clb.CLI_REQ_RES_BUFF_HEADER_SIZE, current_param_size)
    with open(nvar_response_buffer_file, "wb") as out_file:
      out_file.write(current_param_buffer)
      log.info(f"Response Buffer Bin file for Current Nvar saved as {nvar_response_buffer_file}")
  else:
    err_msg = "Response buffer invalid or not generated..."
    raise NvarException(err_msg)

  response_nvar_dict = read_response_buffer(buffer_data=current_param_buffer, nvar_dict=nvar_dict, display_result=display_result)
  if display_result:
    log.debug(response_nvar_dict)
  # pprint(response_nvar_dict)

  log.info('Nvar GetSet CLI Command ended successfully')
  clb.CloseInterface()
  return response_nvar_dict


if __name__ == "__main__":
  pass
