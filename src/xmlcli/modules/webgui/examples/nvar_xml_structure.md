Nvar XML file Structure
=======================

Nvar XML file plays role of human interpretation of the values such that one can also be able to produce, reuse or modify this xml file. For producing the XML file initially, a GUI is also implemented to ease the process, and following the sample structure of XML one can scale the usage for bulk and automated behavior.

Below is the described typical syntax of the XML file which will be parsed and then transformed to byte structure to process as request to BIOS.

**Syntax**

```xml
<!--Global fixed tag <SYSTEM></SYSTEM>-->
<SYSTEM>
    <!--Child Tag Nvar containing one or more UEFI Variables enclosed within tag <Nvar></Nvar>-->
    <Nvar name="NvarName" guid="0x00000000-0x0000-0x0000-0x00-0x00-0x00-0x00-0x00-0x00-0x00-0x00" attributes="0x7" size="0x5" operation="0x0" status="0x00">
        <!--Number of knobs within the Nvar enclosed with the tag <knob></knob>-->
        <!--Knob is nothing but the value at given offset in hexadecimal which could be kind of number, string, Boolean or multiple choice-->
        <knob name="InterpretationOfBytes" setupType="numeric" default="0xfa" CurrentVal="0xfa000000" size="0x4" offset="0x1"
                description="Only the Current Value will matter from BIOS perspective for the specified size" min="0xc" max="0x1388"/>
    </Nvar>
</SYSTEM>
```

Let’s breakdown the syntax as below:
1. Typical Xml Structure will start with fixed global tag `<SYSTEM></SYSTEM>` within which it can have one or more Nvar details.
  - If there is no child tag Nvar exists, it will be interpreted as no Nvar data available to process
2. Information enclosed within `<Nvar></Nvar>` is the representation of data in bytes for the Nvar (EFI variable) which takes below attributes:

#### Meaning of Attributes for XML tag Nvar

| Attribute    | Meaning                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`       | Name of the EFI Variable to be entered without any space, it should follow all the rules of valid name defined in UEFI Specification.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `guid`       | Unique GUID, it should follow the representation format "0x00000000-0x0000-0x0000-0x00-0x00-0x00-0x00-0x00-0x00-0x00-0x00"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `attributes` | Defines the attribute of the variable, we recommend it to be kept as 0x7 which allows the variable to be Nonvolatile and be able to accessible at Boot Time as well as Run time (OS)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `size`	      | Size of the Nvar (EFI Variable) in bytes, Maximum size will be dependent on the space available at NVRAM Region, if any exception/error it can be caught with `EFI_STATUS` and will be available as response to attribute status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `status`     | `EFI_STATUS` Response which is received from BIOS                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `operation`  | attributes currently toggled to define which operation is to be performed. Below are the value and interpretation of the operation: <br> <table> <thead> <tr> <th> Value </th><th> Meaning </th> </tr> </thead>	<tbody> <tr><td> 0x0 </td><td> Calls the GetVariable UEFI method to validate/check whether the variable exists or not, if variable exists then `EFI_SUCCESS` (`0x0`) will be the updated value of the attribute status </td></tr> <tr><td> 0x1 </td><td> Calls the SetVariable UEFI method to create the variable. If variable created successfully, then `EFI_SUCCESS` (`0x0`) will be the updated value of the attribute status </td></tr>		<tr><td> 0x2 </td><td> This parameter is used to update the data values of existing variable. </td></tr>	</tbody> </table> |

3. Tag `<Nvar></Nvar>` can have zero or more knob which are used to represent the data in human readable format. It has the tag `<knob/>` or `<knob></knob>` which will not have any child knob, but it’s only representing particular offset within the Nvar, what does the byte value mean, or how it should get interpreted.
   Note that the valid format could specify any number of knob tag within the Nvar, but logically it’s restricted by the size of the Nvar itself.
   `<knob/>` tag can have below attributes:

#### Meaning of Attributes for XML tag knob

| Attribute     | Meaning                                                                                                                                                                      |
|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`        | Name of the setup option. Only for human interpretation                                                                                                                      |
| `setupType`   | Type of the setup, which could be number, checkbox or options. Only for human interpretation                                                                                 |
| `default`     | Default value for the setup option. Only for human interpretation, as long as the XML file retained specified value in this attribute field will be treated as default value |
| `CurrentVal`  | Current value for setup option. This value represents and synchronizes with the value stored in BIOS NVRAM Region.                                                           |
| `size`        | Size of the setup option in bytes which is always lesser than or equal to the Nvar Size.                                                                                     |
| `offset`      | Represents from which offset specified size in number of bytes to be interpreted within the Nvar data                                                                        |
| `description` | Description of the Setup option. Only for human interpretation                                                                                                               |

Based on the setupType, `<knob></knob>` Tag have some special attributes and child tag.

##### Meaning of Additional Attributes and child tag for knob

| setupType | Additional Attributes                                                                                                                                                                                                                                                              | Additional Child Tag                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| numeric   | <table> <thead> <tr> <th> Attribute </th><th> Meaning </th> </tr> </thead>	<tbody> <tr><td> min </td> <td> minimum value for input number (CurrentVal) </td> </tr><tr> <td>max </td><td> maximum value for input number (CurrentVal) </td></tr></tbody></table>                    | N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| string    | <table> <thead> <tr> <th> Attribute </th><th> Meaning </th> </tr> </thead>	<tbody> <tr><td> minsize </td> <td> minimum length for input string (CurrentVal) </td> </tr><tr> <td> maxsize </td><td> maxsize	maximum length for input string (CurrentVal) </td></tr></tbody></table> | 	N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| oneof     | N/A	                                                                                                                                                                                                                                                                               | Options/available choices, **only for human interpretation** enclosed within the tag: `<options> <options/>`. This tag will contain the available choices enclosed within tag: `<option> <option/>` which will have below attributes: <br> <table> <thead> <tr> <th> Attribute </th><th> Meaning </th> </tr> </thead>	<tbody> <tr><td> text </td> <td> human readable text corresponding to the value </td> </tr><tr> <td> value	</td><td> Value which can be taken for the setup option </td></tr></tbody></table> |
| checkbox  | N/A                                                                                                                                                                                                                                                                                | N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |



***

Following above syntax for XML, one can either use GUI to update or modify the XML or use any feasible mechanism such as manual modification or automating through scripts. Described below is one of the sample XML containing one Nvar and 2 setup option of type multiple choice (oneof) and number (numeric).

**Example:**

```xml
<SYSTEM>
    <!--Generated by XmlCli-->
    <Nvar name="NameOfNvar" guid="0x12345678-0x0000-0x0000-0x00-0x00-0x00-0x00-0x00-0x00-0x00-0x00" attributes="0x7"
          size="0x5" operation="0x0" status="0x00">
        <knob name="InterpretationOfBytes" setupType="oneof" default="0xc" CurrentVal="0xc" size="0x1" offset="0x0"
              description="Only the Current Value will matter from BIOS perspective for the specified size">
            <options>
                <option text="one" value="1"/>
                <option text="two" value="12"/>
                <option text="three" value="123"/>
            </options>
        </knob>
        <knob name="InterpretationOfBytes" setupType="numeric" default="0xfa" CurrentVal="0xfa000000" size="0x4" offset="0x1"
              description="Only the Current Value will matter from BIOS perspective for the specified size" min="0xc" max="0x1388"/>
    </Nvar>
</SYSTEM>
```
