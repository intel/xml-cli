Modify **Value** of Existing Nvar
=============================
1. Click on the `Display created Nvar` to view the NVAR created as per [this](creating_nvar.md) document.

![](../images/display_created_nvar.png)

2. click on `View` to view the Knobs inside the NVAR.

![](../images/Click_on_view.png)

3. Click on `Edit` to edit the values of the Knob.

![](../images/Edit_knob.png)

4. in `Current_value` add the value you wish to change and click on `Save`.
you can view the Change in Current value in the GUI

![](../images/Change_current_value.png)


5. Click on `Save XML` to save the contents into XML file permanently.

![](../images/save_xml_after_changes.png)

6. XML before changing the value of knobs in the Existing Nvar.

![](../images/xml_before_changing_knob_value.png)

7. XML after changing the value of knobs in the Existing Nvar.

![](../images/xml_after_modification.png)

8. To update Nvar values to the SUT click on `Save to SUT`.

![](../images/save_to_sut.png)

9. Select the XML file and Click on `Submit`. It will save the Nvar to SUT.

![](../images/save_nvar.png)

10. To validate the value in the BIOS you can use [dmpstore](https://techlibrary.hpe.com/docs/iss/proliant-gen10-uefi/GUID-BB84420D-33A4-48A8-BEFD-21C2079FC863.html).
    `dmpstore` syntax and usage available at page number 129 in [this](https://uefi.org/sites/default/files/resources/UEFI_Shell_2_2.pdf) document.


Modify **Structure** of created Nvar
================================
1. Click on the `Display created Nvar` to view the NVAR created as per [this](creating_nvar.md) document.

![](../images/display_created_nvar.png)

2. Click on `View` to view the Knobs inside the NVAR

![](../images/Click_on_view.png)

3. Click on `Add Knob` to add the new knobs to the NVAR

![](../images/Add_knob.png)

4. Select the `Knob Type` (in this example we have used Numeric) and provide the corresponding values

![](../images/Adding_Knob_paramters.png)

5. Provide Name, Description and Size and other details for the Knob.Then Refresh the page to view the Knobs created.

![](../images/Knob_Structure_modified.png)

6. Click on `Save XML` to save the contents into XML file permanently.

![](../images/save_xml_structure_modified.png)


7. XML before Modifying the Structure of created the Nvar

![](../images/xml_before_structure_modification.png)


8. XML after Modifying the Structure of created the Nvar

![](../images/xml_after_structure_modification.png)

9. To update Nvar values to the SUT click on `Save to SUT`.

![](../images/save_to_sut_structure.png)

10. Select the XML file and Click on `Submit`. It will save the Nvar to SUT.

![](../images/save_nvar.png)

11. To validate the value in the BIOS you can use [dmpstore](https://techlibrary.hpe.com/docs/iss/proliant-gen10-uefi/GUID-BB84420D-33A4-48A8-BEFD-21C2079FC863.html).
    `dmpstore` syntax and usage available at page number 129 in [this](https://uefi.org/sites/default/files/resources/UEFI_Shell_2_2.pdf) document.
