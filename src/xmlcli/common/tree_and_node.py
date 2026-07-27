# -*- coding: utf-8 -*-

# Built-in imports
from collections import namedtuple

# custom imports
import structure
from logger import log


__version__ = "0.0.1"
__author__ = "Christine Chen & Yuting2 Yang"

class TreeStructure:
  def __init__(self) -> None:
    self.ParentNode = None
    self.ChildNodeList = []

class TreeNode:
  def __init__(self, Key) -> None:
    self.Key = Key
    self.Type = None
    self.Data = b''
    self.WholeTreeData = b''
    self.Position = TreeStructure()

  def HasChild(self):
    if self.Position.ChildNodeList != []:
      return True
    else:
      return False
  
  def InsertChildNode(self, NewChild, order=None):
    if order is not None:
      self.Position.ChildNodeList.insert(order, NewChild)
      NewChild.Position.ParentNode = self
    else:
      self.Position.ChildNodeList.append(NewChild)
      NewChild.Position.ParentNode = self

  def RemoveChildNode(self, RemoveChild):
    self.Position.ChildNodeList.remove(RemoveChild)

  def FindNode(self, key, findlist) -> None:
    if self.Type == 'FFS' and self.Data.Name.guid==key.guid:
      findlist.append(self)
    for item in self.Position.ChildNodeList:
      item.FindNode(key, findlist)

class FvNode:
  def __init__(self):
    self.Name = ''
    self.Header = None
    self.ExtHeader = None
    self.Data = b''
    self.Info = None
    self.IsValid = None
    self.Free_Space = 0

  def InitExtEntry(self, buffer, buffer_pointer):
    self.ExtEntryOffset = self.Header.ExtHeaderOffset + 20
    buffer.seek(buffer_pointer+self.ExtEntryOffset)
    if self.ExtHeader.ExtHeaderSize != 20:
      self.ExtEntryExist = 1
      self.ExtEntry = structure.EfiFirmwareVolumeExtEntry.read_from(buffer)
      self.ExtTypeExist = 1
      if self.ExtEntry.ExtEntryType == 0x01:
        nums = (self.ExtEntry.ExtEntrySize - 8) // 16
        self.ExtEntry = structure.Refine_FV_EXT_ENTRY_OEM_TYPE_Header(nums).read_from(buffer)
      elif self.ExtEntry.ExtEntryType == 0x02:
        nums = self.ExtEntry.ExtEntrySize - 20
        self.ExtEntry = structure.Refine_FV_EXT_ENTRY_GUID_TYPE_Header(nums).read_from(buffer)
      elif self.ExtEntry.ExtEntryType == 0x03:
        self.ExtEntry = structure.EfiFirmwareVolumeExtEntryUsedSizeType.read_from(buffer)
      else:
        self.ExtTypeExist = 0
    else:
      self.ExtEntryExist = 0

  def ModCheckSum(self):
    # Fv Header Sums to 0.
    Header = structure.struct2stream(self.Header)[::-1]
    Size = self.Header.HeaderLength // 2
    Sum = 0
    for i in range(Size):
      Sum += int(Header[i*2: i*2 + 2].hex(), 16)
    if Sum & 0xffff:
      self.Header.Checksum = 0x10000 - (Sum - self.Header.Checksum) % 0x10000

  def ModFvExt(self):
    # If used space changes and self.ExtEntry.UsedSize exists, self.ExtEntry.UsedSize need to be changed.
    if self.Header.ExtHeaderOffset and self.ExtEntryExist and self.ExtTypeExist and self.ExtEntry.Hdr.ExtEntryType == 0x03:
      self.ExtEntry.UsedSize = self.Header.FvLength - self.Free_Space

  def ModFvSize(self):
    # If Fv Size changed, self.Header.FvLength and self.Header.BlockMap[i].NumBlocks need to be changed.
    BlockMapNum = len(self.Header.BlockMap)
    for i in range(BlockMapNum):
      if self.Header.BlockMap[i].Length:
        self.Header.BlockMap[i].NumBlocks = self.Header.FvLength // self.Header.BlockMap[i].Length

  def ModExtHeaderData(self):
    if self.Header.ExtHeaderOffset:
      ExtHeaderData = structure.struct2stream(self.ExtHeader)
      ExtHeaderDataOffset = self.Header.ExtHeaderOffset - self.Header.HeaderLength
      self.Data = self.Data[:ExtHeaderDataOffset] + ExtHeaderData + self.Data[ExtHeaderDataOffset+20:]
    if self.Header.ExtHeaderOffset and self.ExtEntryExist:
      ExtHeaderEntryData = structure.struct2stream(self.ExtEntry)
      ExtHeaderEntryDataOffset = self.Header.ExtHeaderOffset + 20 - self.HeaderLength
      self.Data = self.Data[:ExtHeaderEntryDataOffset] + ExtHeaderEntryData + self.Data[ExtHeaderEntryDataOffset+len(ExtHeaderEntryData):]


class FfsNode:
  def __init__(self):
    self.Name = ''
    self.Header = None
    self.Data = b''
    self.PadData = b''
    self.Info = None
    self.FfsType = None
    
  def ModCheckSum(self) -> None:
    HeaderData = structure.struct2stream(self.Header)
    HeaderSum = 0
    for item in HeaderData:
      HeaderSum += item
    HeaderSum -= self.Header.State
    HeaderSum -= self.Header.IntegrityCheck.Checksum.File
    if HeaderSum & 0xff:
      Header = self.Header.IntegrityCheck.Checksum.Header + 0x100 - HeaderSum % 0x100
      self.Header.IntegrityCheck.Checksum.Header = Header % 0x100
