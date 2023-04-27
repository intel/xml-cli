# Analysing JSON data from 2 different ROM images

## Pie chart and bar graph view of various parameters from 2 JSON files 

Following types of views can be seen - 

1. Pie chart view of both the images based on file type and section type
2. Bar graph view of each of the parameters of file type and section type to see the comparison in both ROM images

Installation of ```matplotlib``` is a prerequisite.

```python
python -m pip install matplotlib
```


## Seeing Pie charts from 2 different JSON files 

Taking 2 JSON files output_1.json and output_2.json as example, we can see the pie chart representation of each of the file types in the following way -

```python
python analytics.py output_1.json output_2.json filetype
```

Similarly, we can see pie chart representation of each of the section types in the following way -

```python
python analytics.py output_1.json output_2.json section
```
![Alt text](filetype_piechart.png?raw=true "pie chart showing file types")

## Seeing Bar graph of various parameters in 2 different JSON files

if we want to compare the count of FV_FILETYPE_DRIVER, we can do it in the following way -

```python
python analytics.py output_1.json output_2.json filetype FV_FILETYPE_DRIVER
```
In the same way, we can compare the count of any section or file type in the 2 JSON files.

We can compare the count of EFI_SECTION_COMPRESSION in the following way -

```python
python analytics.py output_1.json output_2.json section EFI_SECTION_COMPRESSION
```

Currently, the following file types and section types can be seen in the form of bar graph -

```python
	python analytics.py output_1.json output_2.json filetype FV_FILETYPE_DRIVER
    python analytics.py output_1.json output_2.json filetype FV_FILETYPE_APPLICATION
    python analytics.py output_1.json output_2.json filetype FV_FILETYPE_FREEFORM
    python analytics.py output_1.json output_2.json filetype FV_FILETYPE_PEIM
    python analytics.py output_1.json output_2.json filetype FV_FILETYPE_SMM
    python analytics.py output_1.json output_2.json filetype FV_FILETYPE_FIRMWARE_VOLUME_IMAGE
    python analytics.py output_1.json output_2.json filetype FV_FILETYPE_RAW
	
    python analytics.py output_1.json output_2.json section EFI_SECTION_COMPRESSION
    python analytics.py output_1.json output_2.json section EFI_SECTION_FIRMWARE_VOLUME_IMAGE
    python analytics.py output_1.json output_2.json section EFI_SECTION_PEI_DEPEX
    python analytics.py output_1.json output_2.json section EFI_SECTION_DXE_DEPEX 
    python analytics.py output_1.json output_2.json section EFI_SECTION_PE32
    python analytics.py output_1.json output_2.json section EFI_SECTION_RAW
```

![Alt text](bar_graph_raw_section.png?raw=true "bar graph showing raw section in 2 JSON files")