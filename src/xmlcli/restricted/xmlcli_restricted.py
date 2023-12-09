#!/usr/bin/env python
__author__ = ["Gahan Saraiya", "ashinde"]

# Built-in Imports
import os
import re
import sys
import glob
import shutil
import struct
import binascii

# Custom Imports
from ..common import utils
from ..common.logger import log
from .. import XmlCliLib as clb
from .. import UefiFwParser as fwp


__all__ = ["fetch_spi", "convert_inc_to_pdb", "process_ucode",
           "AutomateProUcode", "ExeSvCode", "spi_flash", "FetchSpi", "SpiFlash", "ProcessUcode"]


def _passwd_check(new_password):
  special_sym = "~`!@#$%^&*()_-+={}[]:>;',</?*-+"
  if new_password == "":
    return_val = True
  elif len(new_password) < 9:
    return_val = False
  elif re.search("[0-9]", new_password) is None:
    return_val = False
  elif re.search("[a-z]", new_password) is None:
    return_val = False
  elif re.search("[A-Z]", new_password) is None:
    return_val = False
  elif not any((char in special_sym for char in new_password)):
    return_val = False
  else:
    return_val = True
  return return_val


def fetch_spi(filename, block_offset, block_size, fetch_address=0, delay=1):
  """

  :param filename: Absolute file path to store the result data
  :param block_offset: offset for region block which is to be read
  :param block_size: size of the region block to be read from offset (in bytes)
  :param fetch_address:
  :param delay: number of seconds between each retry attempt to wait for expected response buffer generated from XmlCli driver
  :return:
  """
  clb.LastErrorSig = 0x0000
  clb.InitInterface()
  dram_mailbox_address = clb.GetDramMbAddr()  # Get Dram Mailbox Address.
  dram_mailbox_buffer = clb.memBlock(dram_mailbox_address, 0x110)  # Read/save parameter buffer
  request_buffer_address = clb.readclireqbufAddr(dram_mailbox_buffer)  # Get CLI Request Buffer Address
  response_buffer_address = clb.readcliresbufAddr(dram_mailbox_buffer)  # Get CLI Response Buffer Address
  response_buffer_size = clb.readcliresbufSize(dram_mailbox_buffer)  # Get CLI Response Buffer Size
  log.info(f"CLI Request Buffer Addr = 0x{request_buffer_address:x}   CLI Response Buffer Addr = 0x{response_buffer_address:x}")
  if request_buffer_address == 0 or response_buffer_address == 0:
    log.error('CLI buffers are not valid or not supported, Aborting due to Error!')
    clb.CloseInterface()
    clb.LastErrorSig = 0xC140  # XmlCli Req or Resp Buffer Address is Zero
    return 1

  log.info(f"Fetch RegionOffset = 0x{block_offset:x}  RegionSize = 0x{block_size:x}")
  # Clear CLI Command & Response buffer headers
  clb.ClearCliBuff(request_buffer_address, response_buffer_address)
  if fetch_address == 0:
    if response_buffer_size < (block_size + 0x100):
      clb.LastErrorSig = 0x51E9  # CLI buffer Size Error
      log.error(f'Not Enough size available (0x{response_buffer_size-0x100:x}) in CLI Response Buffer, Aborting....')
      clb.CloseInterface()
      return 1
    fetch_address = response_buffer_address + 0x100
  clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_CMD_OFF, 8, clb.FETCH_BIOS_CMD_ID)
  clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4, 0x10)  # program Parameter size
  clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 0x4, 4, int(block_offset))  # program Offset
  clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 0x8, 4, int(block_size))  # program BIOS Image Size
  clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 0xC, 8, int(fetch_address))  # program Fetch Address for the BIOS Image Size
  clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_SIG_OFF, 4, clb.CLI_REQ_READY_SIG)
  log.info('CLI Mailbox programmed, now issuing S/W SMI to program BIOS..')

  status = clb.TriggerXmlCliEntry()  # trigger S/W SMI for CLI Entry
  if status:
    log.error('Error while triggering CLI Entry Point, Aborting....')
    clb.CloseInterface()
    return 1
  if clb.WaitForCliResponse(response_buffer_address, delay, 8) != 0:
    log.error('CLI Response not ready, Aborting....')
    clb.CloseInterface()
    return 1

  response_parameter_size = int(clb.memread(response_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4))
  if response_parameter_size == 0:
    log.error('CLI Response buffers Parameter size is 0, hence Aborting..')
    clb.CloseInterface()
    clb.LastErrorSig = 0xC4E0  # XmlCli Resp Buffer Parameter Size is Zero
    return 1

  response_parameter_buffer = clb.memBlock((response_buffer_address + clb.CLI_REQ_RES_BUFF_HEADER_SIZE), response_parameter_size)
  source_address = int(clb.ReadBuffer(response_parameter_buffer, 0, 8, clb.HEX))
  clb.memsave(filename, source_address, int(block_size))

  clb.CloseInterface()
  return 0


def convert_inc_to_pdb(inc_file, pdb_file):
  """
  Convert `.inc` microcode extension file to `.pdb` extension file

  :param inc_file: microcode file with extension `.inc`
  :param pdb_file: microcode file with extension `.pdb`
  :return: status code 0 - success, non-zero - failure
  """
  with open(inc_file, 'r') as f:
    lines = f.readlines()
  with open(pdb_file, 'wb') as f:
    log.info('  convert_inc_to_pdb: start writing to pdb file...')
    for line in lines:
      line = line.split(';')[0].strip()
      if line:
        if line[:4] == 'dd 0' and line[12:] == 'h':
          value = int(line[4:12], 16)
          f.write(struct.pack('<L', value))
        else:
          return 1  # AssertionError
  log.info('  convert_inc_to_pdb: done..')
  return 0


def process_ucode(Operation='READ', BiosBinaryFile=0, UcodeFile=0, ReqCpuId=0, outPath='', BiosBinListBuff=0, ReqCpuFlags=0xFFFF, PrintEn=True, Resiliency=False):
  """

  :param Operation: Valid operation to perform from - read, update, delete, save, saveall, deleteall, fixfit
  :param BiosBinaryFile: For offline mode, provide bios or ifwi file path
  :param UcodeFile: For Update operation provide microcode file path as list i.e. ["path/to/microcode.pdb"]
  :param ReqCpuId: CPU Id for microcode patch to be read/delete/update
  :param outPath: For offline mode, new binary output path location
  :param BiosBinListBuff:
  :param ReqCpuFlags:
  :param PrintEn: Enable log print on console or not
  :param Resiliency: Specify to True if slot size of microcode to be maintained
  :return:
  """
  clb.LastErrorSig = 0x0000
  fwp.FwIngredientDict['Ucode'] = {}
  Entry = 0
  Operation = Operation.upper()
  FixFitTable = 0
  BiosFileExt = ".bin"
  OrgUcodeFvFile = os.path.join(clb.TempFolder, "OrgUcodeFv.bin")
  ChgUcodeFvFile = os.path.join(clb.TempFolder, "ChgUcodeFv.bin")
  ChgFitSecFile = os.path.join(clb.TempFolder, "ChgFitSec.bin")
  ChgSecFitPtrFile = os.path.join(clb.TempFolder, "ChgSecFitPtr.bin")
  clb.OutBinFile = ''

  if Operation == "FIXFIT":
    Opeartion = "READ"
    FixFitTable = 1
  ErrorFlag = 0
  ReqPatchInfo = ''
  if BiosBinaryFile == 0:
    clb.InitInterface()
    BiosBinListBuff = 0
    BinSize = 0x1000000  # default Bios Flash size as 16 MB
    if clb.memread((0x100000000 - BinSize), 8) == 0:  # found Zero vector
      if clb.memread((0x100000000 - BinSize + 8), 8) == 0:  # found Zero vector, FV & BIOS region starts from here
        BinSize = BinSize * 2  # Size is 32 MB
  else:
    if BiosBinListBuff == 0:
      BiosFileExt = os.path.splitext(BiosBinaryFile)[1]
      with open(BiosBinaryFile, 'rb') as BiosBinFile:
        BiosBinListBuff = list(BiosBinFile.read())
      UpdateOnlyBiosRegion = False
      BiosRegionBase = 0
      BiosEnd = len(BiosBinListBuff)
      IfwiBinListBuff = []
      Status = fwp.FlashRegionInfo(BiosBinListBuff, False)
      if Status == 0:
        if fwp.FwIngredientDict["FlashDescpValid"] != 0:
          BiosEnd = fwp.FwIngredientDict["FlashRegions"][fwp.BIOS_Region]["EndAddr"] + 1
          if BiosEnd != len(BiosBinListBuff):
            BiosRegionBase = fwp.FwIngredientDict["FlashRegions"][fwp.BIOS_Region]["BaseAddr"]
            log.result(f"Bios Region Range 0x{BiosRegionBase:X} - 0x{BiosEnd:X}")
            IfwiBinListBuff = BiosBinListBuff
            BiosBinListBuff = BiosBinListBuff[BiosRegionBase:BiosEnd]
            UpdateOnlyBiosRegion = True
    BinSize = len(BiosBinListBuff)
    SaveNewBiosBinFile = 0

  if PrintEn:
    log.info("Fetch MicroCode Firmware Volume Base Address from FIT table")
  UcodeFVbase = 0
  ErrorFlag = 1
  UcodeFvList = {}
  UcodeFvFitBaseAddr = []
  UcodeFvIndex = 0
  FitTableEntries = fwp.GetFitTableEntries(BiosBinListBuff)
  slot_size = 0
  if Resiliency:
    ucode_addresses = [BinSize - (0x100000000 - val['Address']) for key, val in FitTableEntries.items() if val["Type"] == 1]
    if len(ucode_addresses) > 1:
      slot_size = ucode_addresses[1] - ucode_addresses[0]
  for count in FitTableEntries:
    if FitTableEntries[count]["Type"] == fwp.UCODE_ENTRY_TYPE_1:
      UcodeFVbase = (FitTableEntries[count].get("Address", 0) & 0xFFFF0000)
      SkipThisItr = False
      if UcodeFvIndex:
        for FvIndex in UcodeFvList:
          if (UcodeFVbase >= UcodeFvList[FvIndex]["UcodeFVbase"]) and (
            UcodeFVbase < (UcodeFvList[FvIndex]["UcodeFVbase"] + UcodeFvList[FvIndex]["UcodeFVsize"])):
            SkipThisItr = True
      if SkipThisItr:
        continue  # this Ucode entry is within the current FV range
      for FvIndex in range(0, 0x40):
        FvGuid_low = clb.ReadBios(BiosBinListBuff, BinSize, UcodeFVbase + 0x10, 8)
        FvGuid_high = clb.ReadBios(BiosBinListBuff, BinSize, UcodeFVbase + 0x18, 8)
        UcodeFVsize = clb.ReadBios(BiosBinListBuff, BinSize, UcodeFVbase + 0x20, 4)
        if (FvGuid_low == 0x4F1C8A3D8C8CE578) and (FvGuid_high == 0xD32DC38561893599):
          UcodeFvList[UcodeFvIndex] = {'UcodeFVbase': UcodeFVbase, 'UcodeFVsize': UcodeFVsize}
          UcodeFvIndex = UcodeFvIndex + 1
          ErrorFlag = 0
          break
        else:
          UcodeFVbase = UcodeFVbase - 0x10000

  if (ErrorFlag == 1):
    log.error('UcodeFVbase = 0, Aborting due to error!')
    if BiosBinaryFile == 0:
      clb.CloseInterface()
    clb.LastErrorSig = 0x3CF9  # process_ucode: Microcode Firmware Volume not found
    return 1

  if type(ReqCpuId) is list:
    pass
  else:
    if ReqCpuId == 0:
      ReqCpuId = []
    else:
      ReqCpuId = [ReqCpuId]
  if type(ReqCpuFlags) is list:
    pass
  else:
    ReqCpuFlags = [ReqCpuFlags]

  InputFileError = True
  UcodePdbDict = {}
  UcodePdbList = []
  if Operation == 'UPDATE':
    ReqPatchInfo = '_newUc'
    if type(UcodeFile) is list:
      UcloopCnt = len(UcodeFile)
    else:
      UcloopCnt = 1
    if PrintEn:
      log.result('|----------|------------|------------|------------|----------|--------|------------|')
      log.result('|  CPUID   | CPU Flags  |  Patch ID  | mm.dd.yyyy |   Size   |CheckSum| Operation  |')
    for tmpCnt in range(0, UcloopCnt):
      if type(UcodeFile) is list:
        UcodeFileName = UcodeFile[tmpCnt]
      else:
        UcodeFileName = UcodeFile
      FileExt = os.path.splitext(UcodeFileName)[1].lower()
      if FileExt in ('.pdb', '.mcb'):
        UcodePdbFile = UcodeFileName
      elif FileExt == '.inc':
        UcodePdbFile = os.path.join(clb.TempFolder, 'TempPdbFile.pdb')
        RetStatus = convert_inc_to_pdb(UcodeFileName, UcodePdbFile)
        if RetStatus:
          log.error('Error Converting inc to pdb format, aborting..')
          clb.LastErrorSig = 0x3CCE  # process_ucode: Error Converting inc to pdb format
          continue
      else:
        log.error('Wrong Ucode Patch File, we expect the Ucode patch file in either .inc or .pdb or .mcb format ')
        clb.LastErrorSig = 0x3CFE  # process_ucode: Wrong Ucode Patch File Format or Extension
        continue
      with open(UcodePdbFile, 'rb') as PdbFile:
        CurPdbFilelistBuff = list(PdbFile.read())
      CheckSum = 0
      PdbUcodeSize = clb.ReadList(CurPdbFilelistBuff, 0x20, 4)
      for Count in range(0, int(PdbUcodeSize / 4)):
        CheckSum = (CheckSum + clb.ReadList(CurPdbFilelistBuff, (Count * 4), 4)) & 0xFFFFFFFF
      if CheckSum != 0:
        log.error(f'Warning: Found invalid checksum (0x{CheckSum:X}) for the given PDB file, aborting !')
        clb.LastErrorSig = 0x3CFC  # process_ucode: Found invalid checksum for the given PDB file
        continue
      Date = clb.ReadList(CurPdbFilelistBuff, 0x8, 4)
      PdbCpuId = clb.ReadList(CurPdbFilelistBuff, 0xC, 4)
      ReqPatchId = clb.ReadList(CurPdbFilelistBuff, 0x4, 4)
      PdbCpuFlags = clb.ReadList(CurPdbFilelistBuff, 0x18, 4)
      ReqCpuId.append(PdbCpuId)
      ReqCpuFlags.append(PdbCpuFlags)
      PatchStr = f'{ReqPatchId:08X}'
      UcodePdbDict[(PdbCpuId, PdbCpuFlags)] = CurPdbFilelistBuff
      UcodePdbList.append((PdbCpuId, PdbCpuFlags))
      ReqPatchInfo = ReqPatchInfo + '_' + hex(PdbCpuId)[2:] + '_' + PatchStr
      InputFileError = False
      if PrintEn:
        log.result(f'| 0x{PdbCpuId:06X} | 0x{PdbCpuFlags:08X} | 0x{ReqPatchId:08X} | {(Date >> 24):02X}.{((Date >> 16) & 0xFF):02X}.{(Date & 0xFFFF):04X} | 0x{PdbUcodeSize:06X} | 0x{CheckSum:04X} | {Operation:<9}  |')
    if PrintEn:
      log.result('|----------|------------|------------|------------|----------|--------|------------|')
    if (InputFileError):
      return 1

  NewUcodeDict = {}
  UcodeEntry = 0
  UpdateFitTable = 0
  ValidUcodeFvFound = False
  UcodeFvNos = len(UcodeFvList)
  for FvIndex in range(0, UcodeFvNos):
    UcodeFVbase = UcodeFvList[FvIndex]['UcodeFVbase']
    UcodeFVsize = UcodeFvList[FvIndex]['UcodeFVsize']
    if BiosBinaryFile == 0:
      UcodeFVlistbuff = list(clb.memBlock(int(UcodeFVbase), int(UcodeFVsize)))
    else:
      UcodeFVlistbuff = BiosBinListBuff[(BinSize - (0x100000000 - UcodeFVbase)):((BinSize - (0x100000000 - UcodeFVbase)) + UcodeFVsize)]

    CheckSum = 0
    for  Count in range (0, 0x24):
      CheckSum = (CheckSum + clb.ReadList(UcodeFVlistbuff, (Count*2), 2)) & 0xFFFF
    if PrintEn:
      log.info(f'UcodeFVbase = 0x{UcodeFVbase:08X}  UcodeFVsize  = 0x{UcodeFVsize:08X}  FVcheckSum = 0x{CheckSum:04X}')
    if (clb.ReadList(UcodeFVlistbuff, 0x34, 2)):
      UcodeFFSbaseOff = 0x78
      NewAddr = 0x90
    else:
      UcodeFFSbaseOff = 0x48
      NewAddr = 0x60
    for loopcount in range (0, 0x40):  # iterate until we find Ucode FFS guid
      if(UcodeFFSbaseOff >= UcodeFVsize):
        break
      FvGuid_low  = clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff, 8)
      FvGuid_high = clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+0x08, 8)
      if (FvGuid_low, FvGuid_high) in fwp.MICRO_CODE_FIRMWARE_GUIDS:
        break
      FFSAttr = clb.ReadList(UcodeFVlistbuff, (UcodeFFSbaseOff+0x13), 1)
      UcodeFFSsize = (clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+0x14, 4) & 0xFFFFFF)
      if((UcodeFFSsize == 0xFFFFFF) or ((FFSAttr & fwp.FFS_ATTRIB_LARGE_FILE) == fwp.FFS_ATTRIB_LARGE_FILE)):
        UcodeFFSsize = clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+fwp.FFS_FILE_HEADER_SIZE, 4)
      UcodeFFSbaseOff = (UcodeFFSbaseOff + UcodeFFSsize + 7) & 0xFFFFFFF8    # this is because FFS sits on a 8 byte boundary
    if (FvGuid_low, FvGuid_high) in fwp.MICRO_CODE_FIRMWARE_GUIDS:
      with open(OrgUcodeFvFile, 'wb') as org_file:  # opening for writing
        org_file.write(bytearray(UcodeFVlistbuff))
      UcodeFFSsize = (clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+0x14, 4) & 0xFFFFFF)
      UcodeSpaceAvailaile = (UcodeFVsize - NewAddr - UcodeFFSsize)
      UcodeDataOff = UcodeFFSbaseOff+0x18
      UcodeFvFitBaseAddr.append(UcodeFVbase+UcodeDataOff)
      FFsHdrCheckSum = 0
      for  Count in range (0, 0x17):    # Ignore offset 0x11 & 0x18 of the FFS header to calculate FFS header Checksum.
        if (Count != 0x11):
          FFsHdrCheckSum = (FFsHdrCheckSum + int(clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+Count, 1))) & 0xFF
      if PrintEn:
        log.result(f'Ucode Space Available = 0x{UcodeSpaceAvailaile:08X}  UcodeFFSsize = 0x{UcodeFFSsize:X} FFSHdrcheckSum = 0x{FFsHdrCheckSum:04X}')
        if Resiliency:
          log.result(f'SlotSize = 0x{slot_size:04X}')
      FFsFileState = clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+0x17, 1)
      if ( (FFsHdrCheckSum == 0) and PrintEn ):
        log.info('Current FFsHdrCheckSum is Valid!')
      CurrUcodeSize = clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+0x20, 4)
      DeletedSize = 0
      AddedSize = 0
      if PrintEn:
        log.result('|----------|------------|------------|------------|----------|-----------|')
        log.result('|  CPU ID  | CPU Flags  |  Patch ID  | mm.dd.yyyy |   Size   | Operation |')
        log.result('|----------|------------|------------|------------|----------|-----------|')
      UcodeFFSendOff = UcodeFFSbaseOff+UcodeFFSsize
      for count in range (0, 20):
        if( UcodeDataOff >= (UcodeFFSendOff) ):
          break
        if(clb.ReadList(UcodeFVlistbuff, UcodeDataOff, 1) == 0xFF):
          RemFFSsize = UcodeFFSendOff - UcodeDataOff
          for count3 in range (0, RemFFSsize, 0x100):  # Usually Ucode size is always in multiple of 1KB, but in this case its safe to assume as 256 bytes.
            if( (clb.ReadList(UcodeFVlistbuff, UcodeDataOff, 1) == 0xFF) and (UcodeDataOff < UcodeFFSendOff) ):
              UcodeDataOff = UcodeDataOff + 0x100
              # log.error(f'Valid Ucode data at Ucode Data Offset (0x{UcodeDataOff:X}) not found')
            else:
              break
        if( UcodeDataOff >= UcodeFFSendOff ):
          break

        CurrOp = 'READ'
        if Operation == 'DELETEALL':
          del UcodeFVlistbuff[UcodeDataOff:UcodeFFSendOff]
          DeletedSize = UcodeFFSendOff - UcodeDataOff
          UcodeFFSendOff = UcodeDataOff
          CurrOp = Operation
          ReqPatchInfo = '_delAllUc'
          break

        CurrUcodeSize = clb.ReadList(UcodeFVlistbuff, UcodeDataOff + 0x20, 4)
        Date = clb.ReadList(UcodeFVlistbuff, UcodeDataOff + 0x8, 4)
        CpuId = clb.ReadList(UcodeFVlistbuff, UcodeDataOff + 0xC, 4)
        PatchId = clb.ReadList(UcodeFVlistbuff, UcodeDataOff + 0x4, 4)
        CpuFlags = clb.ReadList(UcodeFVlistbuff, UcodeDataOff + 0x18, 4)
        if (CurrUcodeSize > UcodeFFSsize) or (Date == 0xFFFFFFFF) or (CpuId == 0xFFFFFFFF) or (PatchId == 0xFFFFFFFF):
          break

        if Operation == 'DELETE':
          if (CpuId in ReqCpuId) and ((0xFFFF in ReqCpuFlags) or (CpuFlags in ReqCpuFlags)):
            PaddingSize = 0
            if clb.ReadList(UcodeFVlistbuff, UcodeDataOff + CurrUcodeSize, 1) == 0xFF:
              RemFFSsize = UcodeFFSendOff - (UcodeDataOff+CurrUcodeSize)
              for CurDataOff in range(0, RemFFSsize, 0x100):  # Usually Ucode size is always in multiple of 1KB, but in this case its safe to assume as 256 bytes.
                if (clb.ReadList(UcodeFVlistbuff, UcodeDataOff + CurrUcodeSize + CurDataOff, 1) == 0xFF) and (UcodeDataOff + CurrUcodeSize + CurDataOff < UcodeFFSendOff):
                  PaddingSize = PaddingSize + 0x100
                else:
                  break
            del UcodeFVlistbuff[UcodeDataOff:UcodeDataOff + (CurrUcodeSize + PaddingSize)]
            DeletedSize = DeletedSize + (CurrUcodeSize + PaddingSize)
            UcodeFFSendOff = UcodeFFSendOff - (CurrUcodeSize + PaddingSize)
            PatchStr = f'{PatchId:08X}'
            ReqPatchInfo = f'{ReqPatchInfo}_delUc_{hex(CpuId)[2:]}_{PatchStr}'
            CurrOp = Operation

        if (Operation == 'SAVE') or (Operation == 'SAVEALL'):
          if (((CpuId in ReqCpuId) and ((0xFFFF in ReqCpuFlags) or (CpuFlags in ReqCpuFlags))) or (Operation == 'SAVEALL')):
            PatchStr = f'{PatchId:08X}'
            SaveUcodeFile = os.path.join(clb.TempFolder, 'm' + hex(CpuFlags)[2:] + hex(CpuId)[2:] + '_' + PatchStr + '.pdb')
            with open(SaveUcodeFile, 'wb') as patch_file:  # opening for writing
              patch_file.write(bytearray(UcodeFVlistbuff[UcodeDataOff: UcodeDataOff + CurrUcodeSize]))
            log.result(f'file saved as {SaveUcodeFile}')
            CurrOp = Operation
            UcodeDataOff = UcodeDataOff + CurrUcodeSize

        if (Operation == 'UPDATE'):
          # NewUcodeDict[UcodeEntry] = {'CpuId':NewCpuId, 'CpuFlags':NewCpuFlags, 'Version':NewPatchId, 'Address':(UcodeFVbase+NewAddr), 'UcodeSize': UcodeSize, 'FoundInFit': 0}
          if (CpuId, CpuFlags) in UcodePdbList and (CpuId, CpuFlags) in UcodePdbDict:
            ucode_size = len(UcodePdbDict[(CpuId, CpuFlags)])
            slot_size = slot_size if slot_size else CurrUcodeSize
            if Resiliency and ucode_size <= slot_size:
              # For resiliency bios, if user input ucode size is lesser than existing ucode slot size
              # add padding for the difference bytes to keep slot size intact
              padding_ucode = [0xff] * (slot_size - ucode_size)
              UcodePdbDict[(CpuId, CpuFlags)] = UcodePdbDict[(CpuId, CpuFlags)] + padding_ucode  # creating ucode slot
              del UcodeFVlistbuff[UcodeDataOff:UcodeDataOff + slot_size]
              DeletedSize = DeletedSize + slot_size
              UcodeFFSendOff = UcodeFFSendOff - slot_size
            else:
              del UcodeFVlistbuff[UcodeDataOff:UcodeDataOff + CurrUcodeSize]
              DeletedSize = DeletedSize + CurrUcodeSize
              UcodeFFSendOff = UcodeFFSendOff - CurrUcodeSize
            # inserts new ucode into existing and shifts following ucode entries
            UcodeFVlistbuff[UcodeDataOff:UcodeDataOff] = UcodePdbDict[(CpuId, CpuFlags)]
            PdbBuffListSize = len(UcodePdbDict[(CpuId, CpuFlags)])
            UcodeDataOff = UcodeDataOff + PdbBuffListSize
            AddedSize = AddedSize + PdbBuffListSize
            UcodeFFSendOff = UcodeFFSendOff + PdbBuffListSize
            UcodePdbDict.pop((CpuId, CpuFlags))
            CurrOp = Operation

        if (CurrOp == 'READ'):
          UcodeDataOff = UcodeDataOff + CurrUcodeSize
        DateStr = f'{(Date >> 24):02X}.{((Date >> 16) & 0xFF):02X}.{(Date & 0xFFFF):04X}'
        fwp.FwIngredientDict['Ucode'][Entry] = {'CpuId'    : CpuId, 'CpuFlags': CpuFlags, 'Version': PatchId, 'Date': DateStr,
                                                'UcodeSize': CurrUcodeSize, 'Operation': CurrOp}
        Entry = Entry + 1
        if PrintEn:
          log.result(f'| 0x{CpuId:06X} | 0x{CpuFlags:08X} | 0x{PatchId:08X} | {DateStr} | 0x{CurrUcodeSize:06X} | {CurrOp:<9} |')
      if PrintEn:
        log.result('|----------|------------|------------|------------|----------|-----------|')
      NewUcodeFFSsize = UcodeFFSsize
      if (Operation == 'UPDATE') or (Operation == 'DELETE') or (Operation == 'DELETEALL'):
        if Operation == 'UPDATE':
          UcodeSpaceAvailaile = UcodeSpaceAvailaile + DeletedSize
          PdbBuffListSize = 0
          ClearUcodeMemList = []
          CurUcodeOff = UcodeDataOff
          for UcodeMember in UcodePdbList:
            if UcodeMember in UcodePdbDict:
              CurPdbSize = len(UcodePdbDict[UcodeMember])
              if UcodeSpaceAvailaile >= CurPdbSize:
                UcodeFVlistbuff[CurUcodeOff:CurUcodeOff] = UcodePdbDict[UcodeMember]
                PdbBuffListSize = PdbBuffListSize + CurPdbSize
                CurUcodeOff = CurUcodeOff + CurPdbSize
                UcodeSpaceAvailaile = UcodeSpaceAvailaile - CurPdbSize
                ClearUcodeMemList.append(UcodeMember)
              else:
                log.result(f'Not Enough Space in Current Ucode FV, Skipping Patch update for CpuId = 0x{UcodeMember[0]:X}  CpuFlagsID = 0x{UcodeMember[1]:X}')
                if ((UcodeFvNos > 1) and (FvIndex < (UcodeFvNos - 1))):
                  log.result('\tWill Attempt Adding the above Ucode patch in Next Ucode FV..')
          for UcodeMember in ClearUcodeMemList:
            UcodePdbDict.pop(UcodeMember)
          AddedSize = AddedSize + PdbBuffListSize

        if (DeletedSize != 0) or (AddedSize != 0):
          UnusedFVspace = UcodeFVsize - (UcodeFFSbaseOff + UcodeFFSsize)
          InsertInUnusedFV = 0
          RemoveFromUnusedFV = 0
          if (DeletedSize != AddedSize):
            UcodeFFSsize = (clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff + 0x14, 4) & 0xFFFFFF)
            if (DeletedSize > AddedSize):
              InsertInUnusedFV = DeletedSize - AddedSize
              NewUcodeFFSsize = ((UcodeFFSsize - InsertInUnusedFV) & 0xFFFFFF)
              BlankBuff = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
              CurIndex = UcodeFFSbaseOff + NewUcodeFFSsize
              for SizeCount in range(0, 20):  # This is good enough for us to achieve 8 MB of blank Buffer
                BlankBuff = BlankBuff + BlankBuff
                if len(BlankBuff) >= InsertInUnusedFV:
                  break
              UcodeFVlistbuff[CurIndex:CurIndex] = BlankBuff[0:InsertInUnusedFV]
            else:
              RemoveFromUnusedFV = AddedSize - DeletedSize
              NewUcodeFFSsize = ((UcodeFFSsize + RemoveFromUnusedFV) & 0xFFFFFF)
              if NewUcodeFFSsize > (UcodeFVsize - UcodeFFSbaseOff):
                log.error('not enough space in Current Ucode FV, please create some space by deleting some entries')
                log.error('Aborting due to above error !')
                clb.RemoveFile(OrgUcodeFvFile)
                clb.LastErrorSig = 0x3C5E  # ProcessUcode: Not enough space in Ucode FV
                return 1
              del UcodeFVlistbuff[UcodeFFSbaseOff + NewUcodeFFSsize:UcodeFFSbaseOff + NewUcodeFFSsize + RemoveFromUnusedFV]
            UcodeFVlistbuff.pop(UcodeFFSbaseOff + 0x14)
            UcodeFVlistbuff.pop(UcodeFFSbaseOff + 0x14)
            UcodeFVlistbuff.pop(UcodeFFSbaseOff + 0x14)
            UcodeFVlistbuff.insert(UcodeFFSbaseOff + 0x14, clb.ListInsertVal(NewUcodeFFSsize))
            UcodeFVlistbuff.insert(UcodeFFSbaseOff + 0x15, clb.ListInsertVal(NewUcodeFFSsize >> 8))
            UcodeFVlistbuff.insert(UcodeFFSbaseOff + 0x16, clb.ListInsertVal(NewUcodeFFSsize >> 16))
            FFsHdrCheckSum = 0
            for  Count in range (0, 0x17):
              if (Count != 0x11) and (Count != 0x10):
                FFsHdrCheckSum = (FFsHdrCheckSum + int(clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+Count, 1))) & 0xFF
            FFsHdrCheckSum = (0x100 - FFsHdrCheckSum) & 0xFF
            UcodeFVlistbuff.pop(UcodeFFSbaseOff+0x10)
            UcodeFVlistbuff.insert(UcodeFFSbaseOff+0x10, clb.ListInsertVal(FFsHdrCheckSum))
          if PrintEn:
            log.info(f' New UnusedFVspace = 0x{(UcodeFVsize - UcodeFFSbaseOff - NewUcodeFFSsize):X}  InsertInUnusedFV = 0x{InsertInUnusedFV:X}  RemoveFromUnusedFV = 0x{RemoveFromUnusedFV:X}  NewFFsHdrCkSum[0x10] = 0x{FFsHdrCheckSum:04X}')

        with open(ChgUcodeFvFile, 'wb') as chg_file:  # opening for writing
          chg_file.write(bytearray(UcodeFVlistbuff))
        if (open(ChgUcodeFvFile, "rb").read() == open(OrgUcodeFvFile, "rb").read()):
          log.result('No changes detected, Skip writing back to the BIOS!')
          UcodeUpdated = 0
        else:
          UcodeUpdated = 1
          log.result('Changes Detected!, Writing back the Updated FV to BIOS')

        if ( (len(UcodeFVlistbuff) == UcodeFVsize) and (UcodeUpdated == 1) ):
          FixFitTable = int(1 and not Resiliency)
          if (BiosBinaryFile == 0):
            DescFile = os.path.join(clb.TempFolder, 'DescFile.bin')
            Status = fetch_spi(DescFile, 0, 0x1000)   # get the descriptor region to know the BIOS Base.
            if(Status == 0):
              with open(DescFile, 'rb') as DescBinFile:
                DescBinListBuff = list(DescBinFile.read())
              UpdateOnlyBiosRegion = False
              Status = fwp.FlashRegionInfo(DescBinListBuff, False)
              clb.RemoveFile(DescFile)
              # BiosStart = fwp.FwIngredientDict['FlashRegions'][fwp.BIOS_Region]['BaseAddr']
              BinSize = fwp.FwIngredientDict['FlashRegions'][fwp.BIOS_Region]['EndAddr'] + 1
            spi_flash('write', ChgUcodeFvFile, region_offset=(BinSize - (0x100000000 - UcodeFVbase))) # program modified Ucode FV image
          else:
            BiosBinListBuff[(BinSize-(0x100000000-UcodeFVbase)):((BinSize-(0x100000000-UcodeFVbase)) + UcodeFVsize )] = UcodeFVlistbuff[0:UcodeFVsize]
            SaveNewBiosBinFile = 1

      UcodeSize = 0
      UcodeFFSsize = (clb.ReadList(UcodeFVlistbuff, UcodeFFSbaseOff+0x14, 4) & 0xFFFFFF)
      UcodeFFSendOff = UcodeFFSbaseOff+UcodeFFSsize
      CurrentUcodeOffset = UcodeFFSbaseOff + 0x18
      while(CurrentUcodeOffset < UcodeFFSsize):
        PaddingSize = 0
        if(clb.ReadList(UcodeFVlistbuff, CurrentUcodeOffset, 1) == 0xFF):
          RemFFSsize = UcodeFFSendOff - CurrentUcodeOffset
          for CurDataOff in range (0, RemFFSsize, 0x100):  # Usually Ucode size is always in multiple of 1KB, but in this case its safe to assume as 256 bytes.
            if( (clb.ReadList(UcodeFVlistbuff, CurrentUcodeOffset+CurDataOff, 1) == 0xFF) and (CurrentUcodeOffset+CurDataOff < UcodeFFSendOff) ):
              PaddingSize = PaddingSize + 0x100
            else:
              break
        CurrentUcodeOffset = CurrentUcodeOffset + PaddingSize
        NewPatchId = clb.ReadList(UcodeFVlistbuff, CurrentUcodeOffset+0x4, 4)
        NewCpuId = clb.ReadList(UcodeFVlistbuff, CurrentUcodeOffset+0xC, 4)
        NewCpuFlags = clb.ReadList(UcodeFVlistbuff, CurrentUcodeOffset+0x18, 4)
        UcodeSize = clb.ReadList(UcodeFVlistbuff, CurrentUcodeOffset+0x20, 4)
        if( (UcodeSize > UcodeFFSsize) or (NewCpuId == 0xFFFFFFFF) ):
          break
        NewUcodeDict[UcodeEntry] = {'CpuId':NewCpuId, 'CpuFlags':NewCpuFlags, 'Version':NewPatchId, 'Address':(UcodeFVbase+CurrentUcodeOffset), 'UcodeSize': UcodeSize, 'FoundInFit': 0}
        UcodeEntry = UcodeEntry + 1
        CurrentUcodeOffset = CurrentUcodeOffset + UcodeSize
      ValidUcodeFvFound = True
    # End of Ucode FV loop
  if (ValidUcodeFvFound):
    for count in FitTableEntries:
      if(FitTableEntries[count]['Type'] == fwp.UCODE_ENTRY_TYPE_1):
        FitUcodeAddr = FitTableEntries[count].get('Address', 0)
        FoundThisEntry = False
        for Entry in NewUcodeDict:
          if (NewUcodeDict[Entry]['FoundInFit'] == 0):
            if (NewUcodeDict[Entry]['Address'] == FitUcodeAddr):
              NewUcodeDict[Entry]['FoundInFit'] = 1
              FoundThisEntry = True
              break
        if ((FitUcodeAddr not in UcodeFvFitBaseAddr) and (FoundThisEntry == False)):
          fwp.FITChkSum = 1  # force FIT Checksum as Bad
          print(f"Fit Entry (0x{FitUcodeAddr:X}) Not Found in Ucode FV or is a Duplicate FIT Entry, Fix FIT")
    for Entry in NewUcodeDict:
      if(NewUcodeDict[Entry]['FoundInFit'] == 0):
        log.error(f'CpuId 0x{NewUcodeDict[Entry]["CpuId"]:X} CpuFlags 0x{NewUcodeDict[Entry]["CpuFlags"]:X} entry, Addr = 0x{NewUcodeDict[Entry]["Address"]:X} was not found in FIT table, needs update')
        UpdateFitTable = 1
    if( (fwp.FITChkSum != 0) and (FixFitTable == 1) ):
      UpdateFitTable = 1
    if (UpdateFitTable == 0):
      if PrintEn:
        log.result('FIT Table verification for Ucode entries was successful')
    else:
      if(FixFitTable):
        log.error('FIT Table verification failed, fixing it...')
      else:
        log.error('FIT Table verification failed, use \"fixfit\" as first arg to ProcessUcode().')
    FitTablePtr = fwp.FwIngredientDict['FitTablePtr']
    FitTableSector = (FitTablePtr - 0x400) & 0xFFFFF000
    FitSectorSize = 0x1000
    NewFitTblBase = FitTablePtr
    if ( (UpdateFitTable == 1) and (FixFitTable == 1) ):
      if ( (FitTablePtr+0x200) >= (FitTableSector+FitSectorSize) ):
        FitSectorSize = 0x2000
      if (BiosBinaryFile == 0):
        FitListbuff = list(clb.memBlock(FitTableSector, FitSectorSize))
      else:
        FitListbuff = BiosBinListBuff[(BinSize-(0x100000000-FitTableSector)):((BinSize-(0x100000000-FitTableSector)) + FitSectorSize)]
      FitTableOfst = FitTablePtr - FitTableSector
      NewFitTblList = FitListbuff[FitTableOfst : (FitTableOfst + (len(FitTableEntries)*0x10))]
      NewFitTblList.pop(0xF)
      NewFitTblList.insert(0xF, clb.ListInsertVal(0))  # clear the checksum to 0
      FitSig = clb.ReadList(NewFitTblList, 0, 8)
      if (FitSig == 0x2020205F5449465F): # '_FIT_   '
        Entries = clb.ReadList(NewFitTblList, 8, 4) & 0xFFFFFF
        Count = 1
        while ((Count*0x10) < len(NewFitTblList)):
          EntryType = (clb.ReadList(NewFitTblList, (Count*0x10)+0x0E, 1) & 0x7F)
          if (EntryType == fwp.UCODE_ENTRY_TYPE_1):
            UcodeEntryAddr = clb.ReadList(NewFitTblList, (Count*0x10), 4)
            if (UcodeEntryAddr not in UcodeFvFitBaseAddr):    # Dont delete First Entry of Ucode FV
              for index in range (0, 0x10):
                NewFitTblList.pop((Count*0x10))
              Entries = Entries - 1
              Count = Count - 1
          Count = Count + 1
      NewEntries = int(len(NewFitTblList)/0x10)
      for Entry in NewUcodeDict:
        if(NewUcodeDict[Entry]['Address'] in UcodeFvFitBaseAddr):
          continue
        NewEntries = NewEntries + 1
        TmpUcodeList = [(NewUcodeDict[Entry]['Address'] & 0xFF), ((NewUcodeDict[Entry]['Address'] >> 8) & 0xFF), ((NewUcodeDict[Entry]['Address'] >> 16) & 0xFF), 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00]
        for index in range (0, 0x10):
          NewFitTblList.insert(0x10+(0x10*Entry)+index, clb.ListInsertVal(TmpUcodeList[index]))
      NewFitTblList.pop(8)
      NewFitTblList.insert(8, clb.ListInsertVal(NewEntries))  # update number of entries
      NewChksm = 0
      for Index in range (0, len(NewFitTblList)):
        NewChksm = (NewChksm + clb.ReadList(NewFitTblList, Index, 1)) & 0xFF
      NewChksm = (0x100 - NewChksm) & 0xFF
      NewFitTblList.pop(0xF)
      NewFitTblList.insert(0xF, clb.ListInsertVal(NewChksm))
      SkipOrgSig = False
      FitSigOrg = clb.ReadList(FitListbuff, (FitTableOfst + 0x200), 8)
      OrgFitSize = len(FitTableEntries)*0x10
      NewFitSize = len(NewFitTblList)
      if(NewFitSize > OrgFitSize):
        log.error('New FIT Table size is bigger than the original FIT table, \n checking if we have enough Valid space to accommodate new entries in FIT')
        # Verify if the new Fit Table Base is really free or if we are accidentally overriding something else.
        for BuffCount in range (0, (NewFitSize-OrgFitSize)):
          if(clb.ReadList(FitListbuff, (FitTableOfst + (len(FitTableEntries)*0x10) + BuffCount), 1) != 0xFF):
            log.error('Not enough space to accommodate new entries in current FIT, Finding New space and creating a new Copy')
            NewFitTblBase = 0
            break
      if(NewFitSize < OrgFitSize):
        for BuffCount in range (0, (OrgFitSize-NewFitSize)):
          NewFitTblList.insert(len(NewFitTblList), clb.ListInsertVal(0xFF))
      if (FitSigOrg == 0x47524F5F5449465F): # '_FIT_ORG'
        NewFitTblBase = FitTablePtr    # means the Original table already existed and current one is already an override, so init it to all F's and re-use it.
        for entrycnt in range (0, len(FitTableEntries)):
          FitListbuff[FitTableOfst + (entrycnt * 0x10) : (FitTableOfst + (entrycnt * 0x10) + 0x10)] = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
      if(NewFitTblBase != FitTablePtr):
        if((FitTablePtr-0x240) > FitTableSector):
          NewFitTblBase = FitTablePtr - 0x200
        else:
          if((FitTablePtr-0x100) > FitTableSector):
            NewFitTblBase = FitTablePtr - 0x100
          else:
            UpdateFitTable = 0
      NewFitTblOfst = NewFitTblBase - FitTableSector
      if (NewFitTblBase != FitTablePtr):
        # Verify if the new Fit Table Base is really free or if we are accidentally overriding something else.
        for BuffCount in range (0, len(NewFitTblList)):
          if(clb.ReadList(FitListbuff, (NewFitTblOfst + BuffCount), 1) != 0xFF):
            NewFitTblBase = FitTablePtr + (len(FitTableEntries)*0x10) - len(NewFitTblList) # init it appropriately.
            if(NewFitTblBase > FitTablePtr):
              Bytes2Clear = NewFitTblBase - FitTablePtr
              for  Count in range (0, Bytes2Clear):
                NewFitTblList.insert(len(NewFitTblList), clb.ListInsertVal(0xFF))
              NewFitTblBase = FitTablePtr
            SkipOrgSig = True
            NewFitTblOfst = NewFitTblBase - FitTableSector
            break
      FitListbuff[NewFitTblOfst : (NewFitTblOfst + len(NewFitTblList))] = NewFitTblList[0 : len(NewFitTblList)]
      if ((NewFitTblBase != FitTablePtr) and (SkipOrgSig == False)):
        FitListbuff.pop(FitTableOfst + 5)
        FitListbuff.insert(FitTableOfst + 5, clb.ListInsertVal(0x4F)) # 'O'
        FitListbuff.pop(FitTableOfst + 6)
        FitListbuff.insert(FitTableOfst + 6, clb.ListInsertVal(0x52)) # 'R'
        FitListbuff.pop(FitTableOfst + 7)
        FitListbuff.insert(FitTableOfst + 7, clb.ListInsertVal(0x47)) # 'G'
      with open(ChgFitSecFile, 'wb') as chgFit_file:  # opening for writing
        chgFit_file.write(bytearray(FitListbuff))
      FitPtrList = [str(chr((NewFitTblBase & 0xFF))), str(chr(((NewFitTblBase >> 8) & 0xFF))), str(chr(((NewFitTblBase >> 16) & 0xFF))), str(chr(((NewFitTblBase >> 24) & 0xFF)))]
      if (BiosBinaryFile == 0):
        spi_flash('write', ChgFitSecFile, region_offset=(BinSize - (0x100000000 - FitTableSector)))       # program modified FIT sector
        if(NewFitTblBase != FitTablePtr):
          FvSecListbuff = list(clb.memBlock(0xFFFFF000, 0x1000))
          FvSecListbuff[0xFC0 : 0xFC4] = FitPtrList[0:4]
          with open(ChgSecFitPtrFile, 'wb') as chgFitPtr_file:  # opening for writing
            chgFitPtr_file.write(bytearray(FvSecListbuff))
          spi_flash('write', ChgSecFitPtrFile, region_offset=(BinSize - 0x1000))       # program modified FIT pointer
      else:
        BiosBinListBuff[(BinSize-(0x100000000-FitTableSector)): ((BinSize-(0x100000000-FitTableSector))+FitSectorSize)] = FitListbuff[0:FitSectorSize]
        if(NewFitTblBase != FitTablePtr):
          BiosBinListBuff[(0xFFFFFFC0 & (BinSize-1)): ((0xFFFFFFC0 & (BinSize-1))+4)] = FitPtrList[0:4]
        SaveNewBiosBinFile = 1
    if PrintEn:
      log.info(f' UcodeFVdataDeleted = 0x{DeletedSize:X}  UcodeFVdataAdded = 0x{AddedSize:X}')
    if (BiosBinaryFile == 0):
      clb.CloseInterface()
    else:
      if(SaveNewBiosBinFile):
        OrgBinFileName = os.path.splitext(os.path.basename(BiosBinaryFile))[0]
        if ( (UpdateFitTable == 1) and (FixFitTable == 1) ):
          ChgBinFileName = OrgBinFileName + ReqPatchInfo + '_NewFit' + BiosFileExt
        else:
          ChgBinFileName = OrgBinFileName + ReqPatchInfo + BiosFileExt
        ChgBiosBinFile = os.path.join(clb.TempFolder, ChgBinFileName)
        clb.OutBinFile = ChgBiosBinFile
        with open(ChgBiosBinFile, 'wb') as chgBios_file:  # opening for writing
          if(UpdateOnlyBiosRegion):
            IfwiBinListBuff[BiosRegionBase:BiosEnd] = BiosBinListBuff
            chgBios_file.write(bytearray(IfwiBinListBuff))
          else:
            chgBios_file.write(bytearray(BiosBinListBuff))
        if outPath != '':
          shutil.move(ChgBiosBinFile,outPath)
          log.result(f'Saving the output Binary file as {outPath}')
        else:
          log.result(f'Saving the output Binary file as {ChgBiosBinFile}')
    clb.RemoveFile(OrgUcodeFvFile)
    clb.RemoveFile(ChgUcodeFvFile)
    clb.RemoveFile(ChgFitSecFile)
    clb.RemoveFile(ChgSecFitPtrFile)

    return 0
  if (BiosBinaryFile == 0):
    clb.CloseInterface()
  clb.LastErrorSig = 0x3CF9  # process_ucode: Microcode Firmware Volume not found
  return 1


def AutomateProUcode(InBios, outBiosFolder, PdbFile, CpuId=0):
  if(os.path.isdir(InBios)):
    InBiosBinFileList = glob.glob(os.path.join(InBios, '*.bin'))
    if(len(InBiosBinFileList) == 0):
      InBiosBinFileList = glob.glob(os.path.join(InBios, '*.rom'))
  elif(os.path.isfile(InBios)):
    InBiosBinFileList = [InBios]
  for BiosBinFile in InBiosBinFileList:
    log.info(f'Processing BIOS file = {BiosBinFile}')
    if(CpuId):
      process_ucode('delete', BiosBinFile, ReqCpuId=CpuId)
      TmpOutFileToDelete = clb.OutBinFile
      process_ucode('update', clb.OutBinFile, PdbFile)
      clb.RemoveFile(TmpOutFileToDelete)
    else:
      process_ucode('update', BiosBinFile, PdbFile)
    TmpOutFileToDelete = clb.OutBinFile
    if (clb.OutBinFile != ''):
      log.info(f'{clb.OutBinFile}')
      shutil.move(clb.OutBinFile, outBiosFolder)
    clb.RemoveFile(TmpOutFileToDelete)


def spi_flash(operation="read", target_file_path="", region=fwp.Invalid_Region, region_offset=0, size=0, delay=2):
  """
  Performs specified Flash operation on SPI

  :param operation: operation to be performed on SPI, choices: `read`, `write`
  :param target_file_path: Absolute path to target file,
          for write operation it would be location where file should exists to write data on SPI
          for read operation it would be location where file will be created with data read from SPI
  :param region: Region Type
  :param region_offset: Offset Address from where operation of read/write to be performed
  :param size: number of bytes to be read/write
  :param delay: number of seconds between each retry attempt to wait for expected response buffer generated from XmlCli driver
  :return:
  """
  clb.LastErrorSig = 0x0000
  clb.InitInterface()
  dram_mailbox_address = clb.GetDramMbAddr()  # Get Dram Mailbox Address.
  dram_mailbox_buffer = clb.memBlock(dram_mailbox_address, 0x110)  # Read/save parameter buffer
  request_buffer_address = clb.readclireqbufAddr(dram_mailbox_buffer)  # Get CLI Request Buffer Address
  response_buffer_address = clb.readcliresbufAddr(dram_mailbox_buffer)  # Get CLI Response Buffer Address
  response_buffer_size = clb.readcliresbufSize(dram_mailbox_buffer)  # Get CLI Response Buffer Size
  log.info(f"CLI Request Buffer Addr = 0x{request_buffer_address:x}   CLI Response Buffer Addr = 0x{response_buffer_address:x}")
  if request_buffer_address == 0 or response_buffer_address == 0:
    log.error("CLI buffers are not valid or not supported, Aborting due to Error!")
    clb.CloseInterface()
    clb.LastErrorSig = 0xC140  # XmlCli Req or Resp Buffer Address is Zero
    return 1

  # Clear CLI Command & Response buffer headers
  clb.ClearCliBuff(request_buffer_address, response_buffer_address)

  if region != fwp.Invalid_Region:
    if region == fwp.Descriptor_Region:
      region_offset = 0
      size = 0x1000
    else:
      log.info("Fetching Region Offset & Size from the Descriptor section")
      descriptor_section_file_path = os.path.join(clb.TempFolder, "descriptor_section.bin")
      status = fetch_spi(descriptor_section_file_path, 0, 0x1000)
      if status == 0:
        with open(descriptor_section_file_path, "rb") as descriptor_section_file:
          descriptor_section_buffer = list(descriptor_section_file.read())
        UpdateOnlyBiosRegion = False
        status = fwp.FlashRegionInfo(descriptor_section_buffer, False)
        clb.RemoveFile(descriptor_section_file_path)
        if status == 0:
          if fwp.FwIngredientDict["FlashDescpValid"] != 0:
            if region == fwp.SpiRegionAll:
              region_offset = 0
              valid_end_address_lis = []
              for FlashRegion in range(0, 10):  # Check valid End Addresses of all possible regions
                end_address = fwp.FwIngredientDict["FlashRegions"][FlashRegion]["EndAddr"]
                if end_address == 0xFFFFFFFF:
                  continue
                valid_end_address_lis.append(end_address)
              size = max(valid_end_address_lis) + 1
            else:
              region_offset = fwp.FwIngredientDict["FlashRegions"][region]["BaseAddr"]
              size = fwp.FwIngredientDict["FlashRegions"][region]["EndAddr"] + 1 - region_offset
          else:
            status = 1
      if status != 0:
        log.error("Descriptor section not Valid, please provide RegionOffset & size, Aborting due to Error!")
        clb.CloseInterface()
        clb.LastErrorSig = 0xD5E9  # spi_flash: Descriptor section not Valid
        return 1
  elif (size == 0) and (operation == "write"):
    size = os.path.getsize(target_file_path)

  if size == 0:
    log.error("Invalid request, Aborting due to Error!")
    clb.CloseInterface()
    clb.LastErrorSig = 0x14E5  # spi_flash: Invalid Request
    return 1

  log.info(f"{operation} RegionOffset = 0x{region_offset:x}  RegionSize = 0x{size:x}")
  block_size = 0x100000
  if response_buffer_size < (block_size + 0x100):
    block_size = (response_buffer_size - 0x100) & 0xFFFF0000
    if block_size == 0:
      clb.LastErrorSig = 0x51E9  # CLI buffer Size Error
      log.error(f"Not Enough size (0x{block_size:x}) available in CLI Respose Buffer, Aborting....")
      clb.CloseInterface()
      return 1
  total_chunks = size // block_size
  last_chunk_size = size % block_size
  offset = region_offset
  if operation == "write":
    with open(target_file_path, "rb") as binary_file:
      tmpFilePart = binary_file.read(0)
      for chunk_idx in range(0, total_chunks):  # divide file in chunks of specified block size
        chunk_data = binary_file.read(block_size)
        chunk_file = os.path.join(clb.TempFolder, f"BinPart_{chunk_idx}.bin")
        with open(chunk_file, 'wb') as chunk:
          chunk.write(chunk_data)
      if last_chunk_size != 0:
        chunk_data = binary_file.read(last_chunk_size)
        chunk_file = os.path.join(clb.TempFolder, f"BinPart_{max(0, total_chunks-1)}.bin")
        with open(chunk_file, 'wb') as chunk:
          chunk.write(chunk_data)
  if last_chunk_size != 0:
    total_chunks = total_chunks + 1
  for chunk_idx in range(0, total_chunks):
    chunk_file = os.path.join(clb.TempFolder, f"BinPart_{chunk_idx}.bin")
    if (chunk_idx == (total_chunks - 1)) and (last_chunk_size != 0):
      chunk_size_to_flash = last_chunk_size
    else:
      chunk_size_to_flash = block_size
    # Clear CLI Command & Response buffer headers
    clb.ClearCliBuff(request_buffer_address, response_buffer_address)
    if operation == 'write':
      clb.load_data(chunk_file, (request_buffer_address + 0x100))
      clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_CMD_OFF, 8, clb.PROG_BIOS_CMD_ID)
      clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4, 0x10)
      clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 0x4, 8, (request_buffer_address + 0x100))
      clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 0x10, 4, chunk_size_to_flash)
      clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 0xC, 4, offset)
      clb.memwrite(request_buffer_address + clb.CLI_REQ_RES_READY_SIG_OFF, 4, clb.CLI_REQ_READY_SIG)
      log.info("CLI Mailbox programmed, now issuing S/W SMI to program SPI..")

      status = clb.TriggerXmlCliEntry()  # trigger S/W SMI for CLI Entry
      if status:
        log.error("Error while triggering CLI Entry Point, Aborting....")
        clb.CloseInterface()
        return 1
      if clb.WaitForCliResponse(response_buffer_address, delay, 10, 0) != 0:
        log.error("CLI Response not ready, Aborting....")
        clb.CloseInterface()
        return 1

      log.result(f"Flashed 0x{chunk_size_to_flash:X} bytes at Rom Binary offset = 0x{offset:X} ")
      clb.RemoveFile(chunk_file)
    elif operation == 'read':
      status = fetch_spi(chunk_file, offset, chunk_size_to_flash)
      if status:
        log.error("Error while Reading SPI API, Aborting....")
        clb.CloseInterface()
        return 1
      log.result(f"Fetched 0x{chunk_size_to_flash:x} bytes from Rom Binary offset = 0x{offset:x} ")
    offset = offset + chunk_size_to_flash
  if operation == "write":
    log.result("SPI Region Flashed successfully.")
  elif operation == 'read':
    with open(target_file_path, 'wb') as target_file:
      log.result(f"Combining all individual files into one {target_file_path} file ")
      for chunk_idx in range(0, total_chunks):
        chunk_file = os.path.join(clb.TempFolder, f"BinPart_{chunk_idx}.bin")
        with open(chunk_file, "rb") as binary_file:
          target_file.write(binary_file.read())
        clb.RemoveFile(chunk_file)
  clb.CloseInterface()
  return 0


def ExeSvCode(Codefilename, ArgBinFile=0):
  clb.LastErrorSig = 0x0000
  clb.InitInterface()
  DRAM_MbAddr = clb.GetDramMbAddr()  # Get DRam Mailbox Address.
  DramSharedMBbuf = clb.memBlock(DRAM_MbAddr,0x110) # REad/save parameter buffer
  CLI_ReqBuffAddr = clb.readclireqbufAddr(DramSharedMBbuf)  # Get CLI Request Buffer Address
  CLI_ResBuffAddr = clb.readcliresbufAddr(DramSharedMBbuf)  # Get CLI Response Buffer Address
  CLI_ResBuffSize = clb.readcliresbufSize(DramSharedMBbuf)  # Get CLI Response Buffer Size
  log.info(f'CLI Request Buffer Addr = 0x{CLI_ReqBuffAddr:X}   CLI Response Buffer Addr = 0x{CLI_ResBuffAddr:X}')
  if ( (CLI_ReqBuffAddr == 0) or (CLI_ResBuffAddr == 0) ):
    log.error('CLI buffers are not valid or not supported, Aborting due to Error!')
    clb.CloseInterface()
    clb.LastErrorSig = 0xC140  # XmlCli Req or Resp Buffer Address is Zero
    return 1

  # Clear CLI Command & Response buffer headers
  clb.ClearCliBuff(CLI_ReqBuffAddr, CLI_ResBuffAddr)
  for Count in range (0, 0x20):
    clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + Count, 8, 0 )
  SvSpecificCodePtr = (CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 0x100)
  RetBuffDatafile = os.path.join(clb.TempFolder, 'RetBuffdata.bin')
  clb.load_data(Codefilename, SvSpecificCodePtr)
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_CMD_OFF, 8, clb.EXE_SV_SPECIFIC_CODE_OPCODE )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4, 0x100 )      # program Parameter size
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 4, 8, SvSpecificCodePtr )
  if (ArgBinFile != 0):
    if(os.path.isfile(ArgBinFile)):
      with open(ArgBinFile, 'rb') as ArgFile:
        ArgBuff = list(ArgFile.read())
        ArgBuffSize = len(ArgBuff)
      for Loop in range (0, 0xE8):
        if (Loop == ArgBuffSize):
          break
        clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 4 + 8 + Loop, 1, int(binascii.hexlify(ArgBuff[Loop]), 16) )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_SIG_OFF, 4, clb.CLI_REQ_READY_SIG )
  log.info('CLI Mailbox programmed, now issuing S/W SMI to execute the given command..')

  Status = clb.TriggerXmlCliEntry()  # trigger S/W SMI for CLI Entry
  if(Status):
    log.error('Error while triggering CLI Entry Point, Aborting....')
    clb.CloseInterface()
    return 1
  if (clb.WaitForCliResponse(CLI_ResBuffAddr, 8) != 0):
    log.error('CLI Response not ready, Aborting....')
    clb.CloseInterface()
    return 1

  ResParamSize = int(clb.memread(CLI_ResBuffAddr + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4))
  if (ResParamSize == 0):
    log.error('CLI Response buffers Parameter size is 0, hence Aborting..')
    clb.CloseInterface()
    clb.LastErrorSig = 0xC4E0  # XmlCli Resp Buffer Parameter Size is Zero
    return 1

  RetParamBuffPtr = int(clb.memread(CLI_ResBuffAddr + clb.CLI_REQ_RES_READY_PARAMSZ_OFF + 4, 4))
  RetParamBuffSize = int(clb.memread(RetParamBuffPtr, 4))
  if(RetParamBuffSize != 0):
    clb.memsave(RetBuffDatafile, (RetParamBuffPtr+4), RetParamBuffSize)
  log.info(f'RetParamBuffPtr = 0x{RetParamBuffPtr:X}    RetParamBuffSize = 0x{RetParamBuffSize:X}')
  clb.CloseInterface()
  return 0


def patch_on_all_bios(in_folder='', out_folder='', patch_file=''):
  """
  Example utility to allow to perform patching of microcode operation on
  multiple bios/ifwi within specified folder.

  :param in_folder: input folder consisting of bios/ifwi file
  :param out_folder: output folder where patched binary to be stored
  :param patch_file: patch file to apply on bios image
  :return:
  """
  for dir_path, dir_name, filenames in os.walk(in_folder):
    for file in filenames:
      if not file.endswith('bin'):
        continue
      try:
        bin_file = os.path.join(dir_path, file)
        process_ucode(Operation='update', BiosBinaryFile=bin_file, UcodeFile=patch_file, ReqCpuId=0, outPath=out_folder)
      except WindowsError:
        log.error('There was an issue accessing the paths specified.')


@utils.deprecated("This function is deprecated, Please use `fetch_spi` instead")
def FetchSpi(filename, BlkOffset, BlockSize, FetchAddr=0, CliDelay=1):
  return fetch_spi(filename, BlkOffset, BlockSize, FetchAddr, CliDelay)


@utils.deprecated("This function is deprecated, Please use `fetch_spi` instead")
def SpiFlash(Operation='read', FilePtr='', Region=fwp.Invalid_Region, RegionOffset=0, RegionSize=0, CliDelay=2):
  return spi_flash(Operation, FilePtr, Region, RegionOffset, RegionSize, CliDelay)


@utils.deprecated("This function is deprecated, Please use `process_ucode` instead")
def ProcessUcode(Operation='READ', BiosBinaryFile=0, UcodeFile=0, ReqCpuId=0, outPath='', BiosBinListBuff=0, ReqCpuFlags=0xFFFF, PrintEn=True, Resiliency=False):
  return process_ucode(Operation, BiosBinaryFile, UcodeFile, ReqCpuId, outPath, BiosBinListBuff, ReqCpuFlags, PrintEn, Resiliency)
