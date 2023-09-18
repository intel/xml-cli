If you have two different Xml from `cli.savexml()` command you could use below method:


Syntax:
```python
from xmlcli import XmlCli as cli

cli.helpers.generate_knobs_delta(
  ref_xml="path/to/reference.xml",
  new_xml="path/to/new.xml",
  out_file="path/to/difference-delta.txt",
  compare_tag="default"  # xml attribute to be compared against (default|CurrentVal|size|prompt|depex|...)
)
```


If you have BIOS/IFWI image, instead of doing `cli.savexml` for both image, you could directly use below command syntax:
```python
from xmlcli import XmlCli as cli

cli.helpers.compare_bios_knobs("<path-to-reference-bios-or-ifwi>", "<path-to-bios-or-ifwi>", result_log_file="<path-to-difference-delta>")
```
