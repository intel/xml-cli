#
#  Copyright 2024 Hkxs
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the “Software”), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import ctypes
import binascii
from pathlib import Path


class LinuxAccess:
    def __init__(self):
        port_lib_location = Path(__file__).resolve().with_name("libport.lso")
        mem_lib_location = Path(__file__).resolve().with_name("libmem.lso")
        self._setup_port_library(port_lib_location)
        self._setup_mem_library(mem_lib_location)

    def _setup_port_library(self, library_path: Path):
        # Read Port library
        self.port_library = ctypes.CDLL(str(library_path))
        # Read Port configuration
        self._read_port = self.port_library.read_port
        self._read_port.argtypes = (ctypes.c_uint16, ctypes.c_uint8)
        self._read_port.restype = ctypes.POINTER(ctypes.c_uint8)
        # Write port configuration
        self._write_port = self.port_library.write_port
        self._write_port.argtypes = (ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint32)

    def _setup_mem_library(self, library_path: Path):
        # external memory
        self.mem_library = ctypes.CDLL(str(library_path))
        # Read Memory configuration
        self._read_mem = self.mem_library.mem_read
        self._read_mem.argtypes = (ctypes.c_ulong, ctypes.c_void_p, ctypes.c_size_t)
        self._read_mem.restype = ctypes.c_int
        # Write Memory configuration
        self._write_mem = self.mem_library.mem_write
        self._write_mem.argtypes = (ctypes.c_ulong, ctypes.c_void_p, ctypes.c_size_t)
        self._write_mem.restype = ctypes.c_int

    def read_port(self, port, size):
        read_val = 0
        ret = self._read_port(port, size)
        if ret:
            for i in range(0, size):
                read_val += ret[i] << (8 * i)
        return read_val

    def io(self, port, size, val=None):
        if val is None:
            read_val = self.read_port(port, size)
            return int(read_val)
        else:
            ret = self._write_port(port, size, val)
            return ret

    def read_memory(self, address, size):
        dest = (ctypes.c_ubyte * size)()
        self._read_mem(address, ctypes.cast(dest, ctypes.c_void_p), size)
        result = 0
        ctypes.cast(dest, ctypes.c_char_p)
        for i in range(0, size):
            result += dest[i] << 8 * i
        return result

    def write_memory(self, address, data, size):
        if isinstance(data, int):
            data = ctypes.c_ulonglong(data)
            _data = ctypes.byref(data)
        else:
            _data = data
        bytes_written = self._write_mem(address, _data, size)
        return bytes_written

    def mem(self, address, size, val=None):
        if val is None:
            read_val = self.read_memory(address, size)
            return int(read_val)
        else:
            ret = self.write_memory(address, val, size)
            return ret

    def read_memory_block(self, address, size, val=None):
        if val is None:
            read_val = self.read_memory(address, size)
            return binascii.unhexlify(hex(read_val)[2:].strip("L").zfill(size * 2))[::-1]
        else:
            ret = self.write_memory(address, val, size)
            return ret

    def mem_block(self, address, size):
        end_address = address + size
        temp_address = address & 0xFFFFF000
        result1 = []
        if (end_address - temp_address) <= 0x1000:
            result = self.read_memory_block(address, size)
            result1.extend(result)
        else:
            first_end_page_address = (address + 0xFFF) & 0xFFFFF000
            if first_end_page_address > address:
                result = self.read_memory_block(address, (first_end_page_address - address))
                result1.extend(result)
            block_count = 0
            block_size = end_address - first_end_page_address
            block_number = int(block_size / 0x1000)
            for block_count in range(0, block_number):
                result = self.read_memory_block(first_end_page_address + (block_count * 0x1000), 0x1000)
                result1.extend(result)
            if block_number != 0:
                block_count = block_count + 1
            if block_size % 0x1000:
                result = self.read_memory_block(first_end_page_address + (block_count * 0x1000), (block_size % 0x1000))
                result1.extend(result)
        return bytearray(result1)

    def mem_save(self, filename, address, size):
        temp_buffer = self.mem_block(address, size)
        with open(filename, "wb") as out_file:  # opening for writing
            out_file.write(temp_buffer)

    def mem_read(self, address, size):
        return self.mem(address, size)  # list of size entries of 1 Byte

    def mem_write(self, address, size, value):
        self.mem(address, size, value)  # list of size entries of 1 Byte

    def read_io(self, address, size):
        return self.io(address, size)

    def write_io(self, address, size, value):
        self.io(address, size, value)

    def trigger_smi(self, smi_value):
        self.io(0xB2, 1, smi_value)
