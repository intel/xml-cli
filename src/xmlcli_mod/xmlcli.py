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

import defusedxml.ElementTree as ET
import logging

from pathlib import Path
from xml.etree.ElementTree import ElementTree

from xmlcli_mod import xmlclilib
from xmlcli_mod.common.utils import is_root
from xmlcli_mod.common.errors import RootError
from xmlcli_mod.dataclasses.knobs import Knob


log = logging.getLogger(__name__)


class XmlCli:
    """
    A class for reading XML-based BIOS knobs through CLI access.

    Attributes
    ----------
    xml_data : xml.etree.ElementTree.Element
        The XML data parsed from the BIOS XML configuration.
    bios_knobs : dict[str, Knob]
        A dictionary mapping knob names to their corresponding Knob objects.
        This property is lazily loaded and parsed from the XML data the first
        time it is accessed.
    _knobs : dict[str, Knob] | None
        A dictionary of BIOS knobs, lazy-loaded when accessed.

    Methods
    -------
    save_xml_knobs(filename: str) -> None
        Saves the current XML data to the specified file.
    get_knob(knob_name: str) -> Knob
        Retrieves a specific knob by name.
    compare_knob(knob_name: str, value: str | int) -> bool
        Compares the value of a specific knob to the provided value.
    """
    def __init__(self) -> None:
        """
        Initializes the XmlCli instance.

        Raises
        ------
        RootError
            If the current user is not a root user.
        """
        if not is_root():
            raise RootError()

        self._xml_string = ""
        self.xml_data = None
        self._knobs = None
        xmlclilib.set_cli_access()
        xmlclilib.verify_xmlcli_support()
        self._get_xml_knobs()

    def _get_xml_knobs(self) -> None:
        """
        Retrieves the XML data and initializes the XML data attribute.

        This method fetches the XML configuration and assigns it to the
        `xml_data` attribute.
        """
        self._xml_string = xmlclilib.get_xml()
        defused_xml = ET.fromstring(self._xml_string)

        # we're converting an element to a tree, we can safely use built-in xml
        # module because, at this point, it's already being parsed by defusedxml
        self.xml_data = ElementTree(defused_xml)

    def save_xml_knobs(self, filename: str | Path) -> None:
        """
        Saves the current XML data to the specified file.

        Parameters
        ----------
        filename : str
            The path to the file where XML data will be saved.
        """
        with open(filename, "w") as f:
            f.write(self._xml_string)

    @property
    def bios_knobs(self):
        """
        Returns the dictionary of BIOS knobs.

        The knobs are lazily loaded and parsed from the XML data the first time
        this property is accessed.

        Returns
        -------
        dict[str, Knob]
            A dictionary mapping knob names to their corresponding Knob objects.
        """
        if not self._knobs:
            self._knobs = self._extract_knobs()
        return self._knobs

    def _extract_knobs(self) -> dict[str, Knob]:
        """
        Parses the XML data to extract BIOS knobs.

        This method traverses the XML tree to build a dictionary of Knob objects,
        indexed by their names.

        Returns
        -------
        dict[str, Knob]
            A dictionary where the keys are knob names and the values are Knob objects.
        """
        knobs_dict = {}
        bios_knobs = self.xml_data.getroot().find("biosknobs")
        for knob in bios_knobs.findall("knob"):
            knob_name = knob.attrib["name"]
            knob_attributes = {
                "name": knob_name,
                "type": knob.attrib.get("type", ""),
                "description": knob.attrib.get("description", ""),
                "value": knob.attrib.get("CurrentVal", ""),
                "default": knob.attrib.get("default", ""),
                "_size": knob.attrib["size"],
                "_offset": knob.attrib["offset"],
            }
            if knob_attributes["type"] == "scalar":
                knob_attributes["default"] = int(knob_attributes.get("default", 0), 16)
                knob_attributes["value"] = int(knob_attributes.get("value", 0), 16)

            knobs_dict[knob_name] = Knob(**knob_attributes)
        return knobs_dict

    def get_knob(self, knob_name: str) -> Knob:
        """
        Retrieves a specific knob by name.

        Parameters
        ----------
        knob_name : str
            The name of the knob to retrieve.

        Returns
        -------
        Knob
            The Knob object corresponding to the provided name.

        Raises
        ------
        KeyError
            If no knob with the given name exists.
        """
        return self.bios_knobs[knob_name]

    def compare_knob(self, knob_name: str, value: str | int) -> bool:
        """
        Compares the value of a specific knob to the provided value.

        Parameters
        ----------
        knob_name : str
            The name of the knob to compare.
        value : str | int
            The value to compare against the knob's current value.

        Returns
        -------
        bool
            True if the knob's value matches the provided value, False otherwise.
        """
        return self.bios_knobs[knob_name].value == value
