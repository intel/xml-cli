# -*- coding: utf-8 -*-
# Built-in imports
import sys
import matplotlib.pyplot as plt
import json


#Python tool to perform comparative analysis of 2 ROM images from their JSON data

# types of list based on the comparison being made
list_section_type=[]
list_file_type=[]


#count of various comparison parameters based on section

count_section_compression=[]
count_section_guid_defined=[]
count_section_disposable=[]
count_section_pe32=[]
count_section_pic=[]
count_section_te=[]
count_section_dxe_depex=[]
count_section_version=[]
count_section_user_interface=[]
count_section_compatibility16=[]
count_section_fv_image=[]
count_section_freeform_subtype_guid=[]
count_section_raw=[]
count_section_pei_depex=[]
count_section_mm_depex=[]
count_section_type=[]

#count of various comparison parameters based on file type

count_filetype_driver=[]
count_filetype_application=[]
count_filetype_freeform=[]
count_filetype_peim=[]
count_filetype_smm=[]
count_filetype_raw=[]
count_filetype_fv=[]
count_filetype_pad=[]
count_filetype=[]

if(len(sys.argv) < 4):
    print("\n")
    print("---------------Usage instruction---------------")
    print("analytics.py <json_file_1> <json_file_2> <type of comparison>")
    print("Currently supported types of comparison = filetype/section")
    print("\n")
    print("---------------Example to check pie chart view of various file types in both JSON files---------------")
    print("analytics.py output_1.json output_2.json filetype")
    print("---------------Example to check bar graph view of various file type parameters in both JSON files---------------")
    print("analytics.py output_1.json output_2.json filetype FV_FILETYPE_DRIVER")
    print("analytics.py output_1.json output_2.json filetype FV_FILETYPE_APPLICATION")
    print("analytics.py output_1.json output_2.json filetype FV_FILETYPE_FREEFORM")
    print("analytics.py output_1.json output_2.json filetype FV_FILETYPE_PEIM")
    print("analytics.py output_1.json output_2.json filetype FV_FILETYPE_SMM")
    print("analytics.py output_1.json output_2.json filetype FV_FILETYPE_FIRMWARE_VOLUME_IMAGE")
    print("analytics.py output_1.json output_2.json filetype FV_FILETYPE_RAW")
    print("---------------Example to check pie chart view of various section types in both JSON files---------------")
    print("analytics.py output_1.json output_2.json section")
    print("---------------Example to check bar graph view of various section type parameters in both JSON files---------------")
    print("analytics.py output_1.json output_2.json section EFI_SECTION_COMPRESSION")
    print("analytics.py output_1.json output_2.json section EFI_SECTION_FIRMWARE_VOLUME_IMAGE")
    print("analytics.py output_1.json output_2.json section EFI_SECTION_PEI_DEPEX")
    print("analytics.py output_1.json output_2.json section EFI_SECTION_DXE_DEPEX") 
    print("analytics.py output_1.json output_2.json section EFI_SECTION_PE32")
    print("analytics.py output_1.json output_2.json section EFI_SECTION_RAW")
    print("\n")
    exit()
    
# Opening 1st JSON file
first_file = open(sys.argv[1])
# Opening 2nd JSON file
second_file = open(sys.argv[2])
# returns JSON object as a dictionary
Json_data_first_file = json.load(first_file)
Json_data_second_file = json.load(second_file)

    

# search for SectionTypes parameters
search_key_compression = 'EFI_SECTION_COMPRESSION'
search_section_key_guid_defined = 'EFI_SECTION_GUID_DEFINED'
search_section_disposable= 'EFI_SECTION_DISPOSABLE'
search_section_pe32 = 'EFI_SECTION_PE32'
search_section_pic = 'EFI_SECTION_PIC'
search_section_te = 'EFI_SECTION_TE'
search_section_dxe_depex = 'EFI_SECTION_DXE_DEPEX'
search_section_version = 'EFI_SECTION_VERSION'
search_section_user_interface = 'EFI_SECTION_USER_INTERFACE'
search_section_compatibility16 = 'EFI_SECTION_COMPATIBILITY16'
search_section_fv_image = 'EFI_SECTION_FIRMWARE_VOLUME_IMAGE'
search_section_freeform_subtype_guid = 'EFI_SECTION_FREEFORM_SUBTYPE_GUID'
search_section_raw = 'EFI_SECTION_RAW'
search_section_pei_depex = 'EFI_SECTION_PEI_DEPEX'
search_section_mm_depex = 'EFI_SECTION_MM_DEPEX'

#search for FileType parameters
search_key_filetype_driver = 'FV_FILETYPE_DRIVER'
search_key_filetype_application = 'FV_FILETYPE_APPLICATION'
search_key_filetype_freeform = 'FV_FILETYPE_FREEFORM'
search_key_filetype_peim = 'FV_FILETYPE_PEIM'
search_key_filetype_smm = 'FV_FILETYPE_SMM'
search_key_filetype_raw = 'FV_FILETYPE_RAW'
search_key_filetype_fv = 'FV_FILETYPE_FIRMWARE_VOLUME_IMAGE'
search_key_filetype_pad = 'FV_FILETYPE_FFS_PAD'

def findkeys(node, kv):
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
               yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x

def plot_piechart_filetype():
    ''' 
    function to plot pie chart based on file type
    '''
    #fetch the key first
    list_file_type.append(list(findkeys(Json_data_first_file, 'Type')))

    #fetch the desired values now
    count_filetype_driver.append(list_file_type[0].count(search_key_filetype_driver))
    count_filetype_application.append(list_file_type[0].count(search_key_filetype_application))
    count_filetype_freeform.append(list_file_type[0].count(search_key_filetype_freeform))
    count_filetype_peim.append(list_file_type[0].count(search_key_filetype_peim))
    count_filetype_smm.append(list_file_type[0].count(search_key_filetype_smm))
    count_filetype_raw.append(list_file_type[0].count(search_key_filetype_raw))
    count_filetype_fv.append(list_file_type[0].count(search_key_filetype_fv))
 
    if count_filetype_driver[0] > 0:
        print(f'{count_filetype_driver[0]} occurences of {search_key_filetype_driver} in {sys.argv[1]}')

    if count_filetype_application[0] > 0:
        print(f'{count_filetype_application[0]} occurences of {search_key_filetype_application} in {sys.argv[1]}')

    if count_filetype_freeform[0] > 0:
        print(f'{count_filetype_freeform[0]} occurences of {search_key_filetype_freeform} in {sys.argv[1]}')

    if count_filetype_peim[0] > 0:
        print(f'{count_filetype_peim[0]} occurences of {search_key_filetype_peim} in {sys.argv[1]}')
        
    if count_filetype_smm[0] > 0:
        print(f'{count_filetype_smm[0]} occurences of {search_key_filetype_smm} in {sys.argv[1]}')
        
    if count_filetype_raw[0] > 0:
        print(f'{count_filetype_raw[0]} occurences of {search_key_filetype_raw} in {sys.argv[1]}')

    if count_filetype_fv[0] > 0:
        print(f'{count_filetype_fv[0]} occurences of {search_key_filetype_fv} in {sys.argv[1]}')

    #analysis of first JSON file ends here
    #
    #analysis of second JSON file starts now
    #
    #fetch the key first
    list_file_type.append(list(findkeys(Json_data_second_file, 'Type')))

    #fetch the desired values now
    count_filetype_driver.append(list_file_type[1].count(search_key_filetype_driver))
    count_filetype_application.append(list_file_type[1].count(search_key_filetype_application))
    count_filetype_freeform.append(list_file_type[1].count(search_key_filetype_freeform))
    count_filetype_peim.append(list_file_type[1].count(search_key_filetype_peim))
    count_filetype_smm.append(list_file_type[1].count(search_key_filetype_smm))
    count_filetype_raw.append(list_file_type[1].count(search_key_filetype_raw))
    count_filetype_fv.append(list_file_type[1].count(search_key_filetype_fv))
       
    if count_filetype_driver[1] > 0:
       print(f'{count_filetype_driver[1]} occurences of {search_key_filetype_driver} in {sys.argv[2]}')

    if count_filetype_application[1] > 0:
        print(f'{count_filetype_application[1]} occurences of {search_key_filetype_application} in {sys.argv[2]}')

    if count_filetype_freeform[1] > 0:
        print(f'{count_filetype_freeform[1]} occurences of {search_key_filetype_freeform} in {sys.argv[2]}')

    if count_filetype_peim[1] > 0:
        print(f'{count_filetype_peim[1]} occurences of {search_key_filetype_peim} in {sys.argv[2]}')
        
    if count_filetype_smm[1] > 0:
        print(f'{count_filetype_smm[1]} occurences of {search_key_filetype_smm} in {sys.argv[2]}')
        
    if count_filetype_raw[1] > 0:
        print(f'{count_filetype_raw[1]} occurences of {search_key_filetype_raw} in {sys.argv[2]}')

    if count_filetype_fv[1] > 0:
        print(f'{count_filetype_fv[1]} occurences of {search_key_filetype_fv} in {sys.argv[2]}')



    # for first JSON file

    plt.figure(0)
    filetypes =[search_key_filetype_driver,search_key_filetype_application,search_key_filetype_freeform,search_key_filetype_peim,search_key_filetype_smm,search_key_filetype_raw,search_key_filetype_fv]

    count = [count_filetype_driver[0],count_filetype_application[0],count_filetype_freeform[0],count_filetype_peim[0],count_filetype_smm[0],count_filetype_raw[0],count_filetype_fv[0]]

    colors = ['r', 'y', 'g', 'b' ,'violet', 'm', 'c']

    # plotting the pie chart
    plt.pie(count, labels = filetypes, colors=colors, 
            startangle=90, shadow = True,explode = (0, 0, 0, 0, 0, 0, 0),
            radius = 1.2, autopct = '%1.1f%%')
            
    # plotting legend
    #plt.legend(loc="lower right")
    plt.title(sys.argv[1], fontsize=10, fontweight='bold', color='black')

    plt.figure(1)
    filetypes =[search_key_filetype_driver,search_key_filetype_application,search_key_filetype_freeform,search_key_filetype_peim,search_key_filetype_smm,search_key_filetype_raw,search_key_filetype_fv]

    count = [count_filetype_driver[1],count_filetype_application[1],count_filetype_freeform[1],count_filetype_peim[1],count_filetype_smm[1],count_filetype_raw[1],count_filetype_fv[1]]

    colors = ['r', 'y', 'g', 'b' ,'violet', 'm', 'c']

    # plotting the pie chart
    plt.pie(count, labels = filetypes, colors=colors, 
            startangle=90, shadow = True,explode = (0, 0, 0, 0, 0, 0, 0),
            radius = 1.2, autopct = '%1.1f%%')

    plt.title(sys.argv[2], fontsize=10, fontweight='bold', color='black')

    # showing the plot
    plt.show()


def plot_piechart_section():
    ''' 
    function to plot pie chart based on section type
    '''
    #fetch the key first
    list_section_type.append(list(findkeys(Json_data_first_file, 'SectionType')))
    
    #fetch the desired values now
    count_section_compression.append(list_section_type[0].count(search_key_compression))
    count_section_guid_defined.append(list_section_type[0].count(search_section_key_guid_defined))
    count_section_disposable.append(list_section_type[0].count(search_section_disposable))
    count_section_pe32.append(list_section_type[0].count(search_section_pe32))
    count_section_pic.append(list_section_type[0].count(search_section_pic))
    count_section_te.append(list_section_type[0].count(search_section_te))
    count_section_dxe_depex.append(list_section_type[0].count(search_section_dxe_depex))
    count_section_version.append(list_section_type[0].count(search_section_version))
    count_section_user_interface.append(list_section_type[0].count(search_section_user_interface))
    count_section_compatibility16.append(list_section_type[0].count(search_section_compatibility16))
    count_section_fv_image.append(list_section_type[0].count(search_section_fv_image))
    count_section_freeform_subtype_guid.append(list_section_type[0].count(search_section_freeform_subtype_guid))
    count_section_raw.append(list_section_type[0].count(search_section_raw))
    count_section_pei_depex.append(list_section_type[0].count(search_section_pei_depex))
    count_section_mm_depex.append(list_section_type[0].count(search_section_mm_depex))


    if count_section_compression[0] > 0:
        print(f'{count_section_compression[0]} occurences of {search_key_compression} in {sys.argv[1]}')
        
    if count_section_guid_defined[0] > 0:
        print(f'{count_section_guid_defined[0]} occurences of {search_section_key_guid_defined} in {sys.argv[1]}')

    if count_section_disposable[0] > 0:
        print(f'{count_filetype_application[0]} occurences of {search_section_disposable} in {sys.argv[1]}')

    if count_section_pe32[0] > 0:
        print(f'{count_section_pe32[0]} occurences of {search_section_pe32} in {sys.argv[1]}')

    if count_section_pic[0] > 0:
        print(f'{count_section_pic[0]} occurences of {search_section_pic} in {sys.argv[1]}')
        
    if count_section_te[0] > 0:
        print(f'{count_section_te[0]} occurences of {search_section_te} in {sys.argv[1]}')
        
    if count_section_dxe_depex[0] > 0:
        print(f'{count_section_dxe_depex[0]} occurences of {search_section_dxe_depex} in {sys.argv[1]}')

    if count_section_version[0] > 0:
        print(f'{count_section_version[0]} occurences of {search_section_version} in {sys.argv[1]}')
            
    if count_section_user_interface[0] > 0:
        print(f'{count_section_user_interface[0]} occurences of {search_section_user_interface} in {sys.argv[1]}')

    if count_section_compatibility16[0] > 0:
        print(f'{count_section_compatibility16[0]} occurences of {search_section_compatibility16} in {sys.argv[1]}')

    if count_section_fv_image[0] > 0:
        print(f'{count_section_fv_image[0]} occurences of {search_section_fv_image} in {sys.argv[1]}')

    if count_section_freeform_subtype_guid[0] > 0:
        print(f'{count_section_freeform_subtype_guid[0]} occurences of {search_section_freeform_subtype_guid} in {sys.argv[1]}')
        
    if count_section_raw[0] > 0:
        print(f'{count_section_raw[0]} occurences of {search_section_raw} in {sys.argv[1]}')
        
    if count_section_pei_depex[0] > 0:
        print(f'{count_section_pei_depex[0]} occurences of {search_section_pei_depex} in {sys.argv[1]}')

    if count_section_mm_depex[0] > 0:
        print(f'{count_section_mm_depex[0]} occurences of {search_section_mm_depex} in {sys.argv[1]}')

    #analysis of first JSON file ends here
    #
    #analysis of second JSON file starts now
    #
    #fetch the key first
    list_section_type.append(list(findkeys(Json_data_second_file, 'SectionType')))
    
    #fetch the desired values now
    count_section_compression.append(list_section_type[1].count(search_key_compression))
    count_section_guid_defined.append(list_section_type[1].count(search_section_key_guid_defined))
    count_section_disposable.append(list_section_type[1].count(search_section_disposable))
    count_section_pe32.append(list_section_type[1].count(search_section_pe32))
    count_section_pic.append(list_section_type[1].count(search_section_pic))
    count_section_te.append(list_section_type[1].count(search_section_te))
    count_section_dxe_depex.append(list_section_type[1].count(search_section_dxe_depex))
    count_section_version.append(list_section_type[1].count(search_section_version))
    count_section_user_interface.append(list_section_type[1].count(search_section_user_interface))
    count_section_compatibility16.append(list_section_type[1].count(search_section_compatibility16))
    count_section_fv_image.append(list_section_type[1].count(search_section_fv_image))
    count_section_freeform_subtype_guid.append(list_section_type[1].count(search_section_freeform_subtype_guid))
    count_section_raw.append(list_section_type[1].count(search_section_raw))
    count_section_pei_depex.append(list_section_type[1].count(search_section_pei_depex))
    count_section_mm_depex.append(list_section_type[1].count(search_section_mm_depex))


    if count_section_compression[1] > 0:
        print(f'{count_section_compression[1]} occurences of {search_key_compression} in {sys.argv[2]}')
        
    if count_section_guid_defined[1] > 0:
        print(f'{count_section_guid_defined[1]} occurences of {search_section_key_guid_defined} in {sys.argv[2]}')

    if count_section_disposable[1] > 0:
        print(f'{count_filetype_application[1]} occurences of {search_section_disposable} in {sys.argv[2]}')

    if count_section_pe32[1] > 0:
        print(f'{count_section_pe32[1]} occurences of {search_section_pe32} in {sys.argv[2]}')

    if count_section_pic[1] > 0:
        print(f'{count_section_pic[1]} occurences of {search_section_pic} in {sys.argv[2]}')
        
    if count_section_te[1] > 0:
        print(f'{count_section_te[1]} occurences of {search_section_te} in {sys.argv[2]}')
        
    if count_section_dxe_depex[1] > 0:
        print(f'{count_section_dxe_depex[1]} occurences of {search_section_dxe_depex} in {sys.argv[2]}')

    if count_section_version[1] > 0:
        print(f'{count_section_version[1]} occurences of {search_section_version} in {sys.argv[2]}')
            
    if count_section_user_interface[1] > 0:
        print(f'{count_section_user_interface[0]} occurences of {search_section_user_interface} in {sys.argv[2]}')

    if count_section_compatibility16[1] > 0:
        print(f'{count_section_compatibility16[1]} occurences of {search_section_compatibility16} in {sys.argv[2]}')

    if count_section_fv_image[1] > 0:
        print(f'{count_section_fv_image[1]} occurences of {search_section_fv_image} in {sys.argv[2]}')

    if count_section_freeform_subtype_guid[1] > 0:
        print(f'{count_section_freeform_subtype_guid[1]} occurences of {search_section_freeform_subtype_guid} in {sys.argv[2]}')
        
    if count_section_raw[1] > 0:
        print(f'{count_section_raw[1]} occurences of {search_section_raw} in {sys.argv[2]}')
        
    if count_section_pei_depex[1] > 0:
        print(f'{count_section_pei_depex[1]} occurences of {search_section_pei_depex} in {sys.argv[2]}')

    if count_section_mm_depex[1] > 0:
        print(f'{count_section_mm_depex[1]} occurences of {search_section_mm_depex} in {sys.argv[2]}')



    # for first JSON file

    plt.figure(0)
    section_type =[search_key_compression,search_section_key_guid_defined,search_section_disposable,search_section_pe32,search_section_pic,search_section_te,search_section_dxe_depex,search_section_version,
                   search_section_user_interface,search_section_compatibility16,search_section_fv_image,search_section_freeform_subtype_guid,search_section_raw,search_section_pei_depex,search_section_mm_depex]

    count = [count_section_compression[0],count_section_guid_defined[0],count_section_disposable[0],count_section_pe32[0],count_section_pic[0],count_section_te[0],count_section_dxe_depex[0],count_section_version[0],
             count_section_user_interface[0],count_section_compatibility16[0],count_section_fv_image[0],count_section_freeform_subtype_guid[0],count_section_raw[0],count_section_pei_depex[0],count_section_mm_depex[0]]

    colors = ['red', 'yellow', 'green', 'blue' ,'violet', 'magenta', 'cyan','gold', 'lightskyblue', 'purple', 'orange' ,'violet', 'crimson', 'maroon','pink']

    # plotting the pie chart
    plt.pie(count, labels = section_type, colors=colors, 
            startangle=90, shadow = True,explode = (0.1, 0, 0, 0, 0, 0, 0,0,0,0,0,0,0,0,0),
            radius = 1.2, autopct = '%1.1f%%')
            
    # plotting legend
    #plt.legend(loc="lower right")
    plt.title(sys.argv[1], fontsize=10, fontweight='bold', color='black')

    # for second JSON file
    plt.figure(1)
   

    count = [count_section_compression[1],count_section_guid_defined[1],count_section_disposable[1],count_section_pe32[1],count_section_pic[1],count_section_te[1],count_section_dxe_depex[1],count_section_version[1],
             count_section_user_interface[1],count_section_compatibility16[1],count_section_fv_image[1],count_section_freeform_subtype_guid[1],count_section_raw[1],count_section_pei_depex[1],count_section_mm_depex[1]]


    # plotting the pie chart
    plt.pie(count, labels = section_type, colors=colors, 
            startangle=90, shadow = True,explode = (0.1, 0, 0, 0, 0, 0, 0,0,0,0,0,0,0,0,0),
            radius = 1.2, autopct = '%1.1f%%')

    plt.title(sys.argv[2], fontsize=10, fontweight='bold', color='black')
    
    # showing the plot
    plt.show()
    
def plot_bargraph_file_type(file_section_type, parameter):
    ''' 
    function to plot bar graph of a file type parameter
    : param file_section_type: Type
    : param parameter: type of the file to analyse such as
    :                   FV_FILETYPE_DRIVER, FV_FILETYPE_APPLICATION, FV_FILETYPE_FREEFORM, etc.
    '''
    #first JSON file
    #fetch the key first
    list_file_type.append(list(findkeys(Json_data_first_file, file_section_type)))
    #fetch the desired values now
    count_filetype.append(list_file_type[0].count(parameter))
    if count_filetype[0] > 0:
      print(f'{count_filetype[0]} occurences of {parameter} in {sys.argv[1]}')
    #second JSON file
    #fetch the key first
    list_file_type.append(list(findkeys(Json_data_second_file, file_section_type)))

    #fetch the desired values now
    count_filetype.append(list_file_type[1].count(parameter))
    if count_filetype[1] > 0:
       print(f'{count_filetype[1]} occurences of {parameter} in {sys.argv[2]}')
    
    filetype_count = {sys.argv[1]:count_filetype[0], sys.argv[2]:count_filetype[1]}
    
    xAxis = [key for key, value in filetype_count.items()]
    yAxis = [value for key, value in filetype_count.items()]
    plt.grid(False)
    ## BAR GRAPH ##
    plt.bar(xAxis,yAxis, color='blue')
    plt.xlabel('FileName')
    plt.ylabel(parameter)
    plt.show()
    

def plot_bargraph_section_type(file_section_type, parameter):
    ''' 
    function to plot bar graph of a section type parameter
    : param file_section_type: SectionType
    : param parameter: type of the section to analyse such as
    :                   EFI_SECTION_COMPRESSION, EFI_SECTION_FIRMWARE_VOLUME_IMAGE, EFI_SECTION_PE32, etc.
    '''
    #first JSON file
    #fetch the key first
    list_file_type.append(list(findkeys(Json_data_first_file, file_section_type)))
    #fetch the desired values now
    count_section_type.append(list_file_type[0].count(parameter))
    if count_section_type[0] > 0:
      print(f'{count_section_type[0]} occurences of {parameter} in {sys.argv[1]}')
    #second JSON file
    #fetch the key first
    list_file_type.append(list(findkeys(Json_data_second_file, file_section_type)))

    #fetch the desired values now
    count_section_type.append(list_file_type[1].count(parameter))
    if count_section_type[1] > 0:
       print(f'{count_section_type[1]} occurences of {parameter} in {sys.argv[2]}')
    
    section_count = {sys.argv[1]:count_section_type[0], sys.argv[2]:count_section_type[1]}
    
    xAxis = [key for key, value in section_count.items()]
    yAxis = [value for key, value in section_count.items()]
    plt.grid(False)
    ## BAR GRAPH ##
    plt.bar(xAxis,yAxis, color='maroon')
    plt.xlabel('FileName')
    plt.ylabel(parameter)
    plt.show()



if __name__ == "__main__":
    print(len(sys.argv))
    if(sys.argv[3] == "filetype" and len(sys.argv) == 4):
        plot_piechart_filetype()
    elif(sys.argv[3] == "section" and len(sys.argv) == 4):
        plot_piechart_section()
    elif(sys.argv[3] == "filetype" and len(sys.argv) == 5): 
        plot_bargraph_file_type('Type',sys.argv[4])
    elif(sys.argv[3] == "section" and  len(sys.argv) == 5):
        plot_bargraph_section_type('SectionType',sys.argv[4])

# Closing files
first_file.close()
second_file.close()
