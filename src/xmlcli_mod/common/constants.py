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

SHAREDMB_SIG1 = 0xBA5EBA11
SHAREDMB_SIG2 = 0xBA5EBA11
LEGACYMB_SIG = 0x5A7ECAFE
SHAREDMB_SIG1_OFF = 0x00
SHAREDMB_SIG2_OFF = 0x08
CLI_SPEC_VERSION_MINOR_OFF = 0x14
CLI_SPEC_VERSION_MAJOR_OFF = 0x15
CLI_SPEC_VERSION_RELEASE_OFF = 0x17
LEGACYMB_SIG_OFF = 0x20
LEGACYMB_OFF = 0x24
LEGACYMB_XML_OFF = 0x0C  # TODO check why this thing is being modified
ASCII = 0xA5
HEX = 0x16
