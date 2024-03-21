function validate_non_empty_knob_input(){
    let has_empty_size = isNaN(parseInt(content.data.size));
    let has_empty_knob_type = content.data.knob_type === undefined;
    let has_empty_name = content.data.name === undefined || content.data.name.trim() === "";
    let has_empty_description = content.data.description === undefined || content.data.description.trim() === "";
    let has_error = has_empty_size || has_empty_name || has_empty_description || has_empty_knob_type;
    if (has_empty_size) {
        add_inline_error('size', 'Please enter valid Size for the Knob');
    } else {
        remove_inline_error('size');
    }
    if (has_empty_name) {
        add_inline_error('name', 'Please enter valid Name for the Knob');
    } else {
        remove_inline_error('name');
    }
    if (has_empty_description) {
        add_inline_error('description', 'Please enter valid Description for the Knob');
    } else {
        remove_inline_error('description');
    }
    if (has_empty_knob_type) {
        add_inline_error('knob_type', 'Please select valid Knob Type');
    } else {
        remove_inline_error('knob_type');
    }
    console.log("HAS Error: " + has_error);
    if (has_error){
        return false;
    } else {
        return true;
    }
}

function validate_knob_string(){
    let min_characters = parseInt(content.data.min_characters);
    let max_characters = parseInt(content.data.max_characters);
    let value = content.data.value;
    let has_error = isNaN(min_characters) || isNaN(max_characters) || (!value);
    if (isNaN(min_characters)) {
        add_inline_error('stringForm-min_characters', 'Please enter valid input');
    } else {
        remove_inline_error('stringForm-min_characters');
    }
    if (isNaN(max_characters)) {
        add_inline_error('stringForm-max_characters', 'Please enter valid input');
    } else {
        remove_inline_error('stringForm-max_characters');
    }
    if (!value) {
        add_inline_error('stringForm-value', 'Please enter valid input');
    } else {
        remove_inline_error('stringForm-value');
    }
    console.log("HAS Error: " + has_error);
    if (!has_error) {
        clear_errors();
        $("#otherDetailModal").modal('hide');
    }
}

function validate_knob_numeric(){
    let min_value = parseInt(content.data.min_value);
    let max_value = parseInt(content.data.max_value);
    let value = content.data.value;
    let has_error = isNaN(min_value) || isNaN(max_value) || (!value);
    if (isNaN(min_value)) {
        add_inline_error('numericForm-min_value', 'Please enter valid input');
    } else {
        remove_inline_error('numericForm-min_value');
    }
    if (isNaN(max_value)) {
        add_inline_error('numericForm-max_value', 'Please enter valid input');
    } else {
        remove_inline_error('numericForm-max_value');
    }
    if (!value) {
        add_inline_error('numericForm-value', 'Please enter valid input');
    } else {
        remove_inline_error('numericForm-value');
    }
    console.log("HAS Error: " + has_error);
    if (!has_error) {
        clear_errors();
        $("#otherDetailModal").modal('hide');
    }
}

function validate_knob_oneof(){
    let selected_value = $("#oneofForm-value")[0].selectedIndex;
    let has_error = selected_value === -1;
    if (selected_value === -1) {
        add_inline_error('oneofForm-value', 'Please enter valid option(s)');
    } else {
        remove_inline_error('oneofForm-value');
    }
    console.log("HAS Error: " + has_error);
    if (!has_error) {
        clear_errors();
        $("#otherDetailModal").modal('hide');
    }
}
function validate_knob_checkbox(){
    let selected_value = $("#checkboxForm-value")[0].selectedIndex;
    let has_error = selected_value === -1;
    if (selected_value === -1) {
        add_inline_error('checkboxForm-value', 'Please enter valid option');
    } else {
        remove_inline_error('checkboxForm-value');
    }
    console.log("HAS Error: " + has_error);
    if (!has_error) {
        clear_errors();
        $("#otherDetailModal").modal('hide');
    }
}

function discard_knob_changes() {
    clear_errors();
    delete content.data["min_characters"];
    delete content.data["max_characters"];
    delete content.data["min_value"];
    delete content.data["max_value"];
    delete content.data["options"];
    delete content.data["value"];
    delete content.data["knob_type"];
    delete content.data["name"];
    delete content.data["description"];
}

function knobHandler() {
    discard_knob_changes();
    contentUpdater("knob_type", "knob_type");
    let knobTypes = ['oneof', 'numeric', 'string', 'checkbox'];
    let knob_type = document.getElementById("knob_type").value;
    console.log("Knob Type value changed to: " + knob_type);

    // display modal when user selects knob type from drop down menu
    if (knobTypes.includes(knob_type)) {
        $("#otherDetailModal").modal('show');
    }
    // clear any existing element from the body
    if (knob_type === "reserved") {
        $("#modal-body").html("");
        let name = $("input#name")[0];
        let description = $("textarea#description")[0];
        name.value = "ReservedSpace";
        name.disabled = true;
        description.value = "Reserved Space within the Nvar";
        description.disabled = true;
        contentUpdater("name", "name");
        contentUpdater("description", "description");
        contentUpdater("value", "size");
        $("#size").parent().html('<input class="form-control" id="size" min="1" name="size" placeholder="Enter Size" required="" type="number" value="1">');
    }
    else{
        $("#modal-body").html("");
        let name = $("input#name")[0];
        let description = $("textarea#description")[0];
        name.value = "";
        name.disabled = false;
        description.value = "";
        description.disabled = false;

    }
    if (knob_type === "string") {
        $("#modal-body").html(getStringForm());
        $("#size").parent().html('<input class="form-control" id="size" min="1" name="size" placeholder="Enter Size" required="" type="number" value="1">');

        $("#stringForm-min_characters").on("change keyup paste click", function () {
            updateElement("for", "stringForm-min_characters", "Minimum Characters");
            contentUpdater("min_characters", "stringForm-min_characters")
        });

        $("#stringForm-max_characters").on("change keyup paste click", function () {
            updateElement("for", "stringForm-max_characters", "Minimum Characters");
            contentUpdater("max_characters", "stringForm-max_characters")
        });

        $("#stringForm-value").on("change keyup paste click", function () {
            contentUpdater("value", "stringForm-value")
        });

    } else if (knob_type === "numeric") {
        $("#modal-body").html(getNumericForm());
        $("#size").parent().html('<input class="form-control" id="size" max="8" min="1" name="size" pattern="[1-8]" placeholder="Enter Size" required="" type="number" value="1">');

        $("#numericForm-min_value").on("change keyup paste click", function () {
            updateElement("for", "min_value", "Minimum Value");
            contentUpdater("min_value", "numericForm-min_value")
        });

        $("#numericForm-max_value").on("change keyup paste click", function () {
            updateElement("for", "max_value", "Maximum Value");
            contentUpdater("max_value", "numericForm-max_value")
        });

        $("#numericForm-value").on("change keyup paste click", function () {
            updateElement("for", "value", "Value");
            contentUpdater("value", "numericForm-value")
        });

    } else if (knob_type === "checkbox") {
        $("#modal-body").html(getCheckboxForm());
        $("#size").parent().html('<input class="form-control" id="size" max="1" min="1" name="size" placeholder="Enter Size" required="" type="number" value="1" disabled>');
        contentUpdater("size", "size");
        contentUpdater("value", "checkboxForm-value");
        $("#checkboxForm-value").on("change keyup paste click", function () {
            contentUpdater("value", "checkboxForm-value")
        });

    } else if (knob_type === "oneof") {
        $("#modal-body").html(getOneOfForm());
        $("#size").parent().html('<input class="form-control" id="size" max="8" min="1" name="size" pattern="[1-8]" placeholder="Enter Size" required="" type="number" value="1">');
        content.data["options"] = [];
        // Handle Dynamic Dropdown loading to enter value
        $('#oneofForm-optionAdder').on("click", function () {
            let optionText = $('#oneofForm-option-text').val();
            let optionValue = $('#oneofForm-option-value').val();
            let option = document.createElement("option");
            option.text = optionValue + " - " + optionText;
            option.value = optionValue;
            document.getElementById("oneofForm-value").add(option);
            content.data["options"] = content.data["options"].concat({
                'value': optionValue,
                'text': optionText
            });
            contentUpdater("value", "oneofForm-value");
        });

        $("#oneofForm-value").on("change click", function () {
            contentUpdater("value", "oneofForm-value");
        });
    }

    // Save Changes
    $("#save_details").on("click", function () {
        if (document.getElementById("knob_type").value === "oneof"){
            console.log("Evaluating: " + knob_type);
            validate_knob_oneof();
        }
        else if (document.getElementById("knob_type").value === "numeric"){
            console.log("Evaluating: " + knob_type);
            validate_knob_numeric();
        }
        else if (document.getElementById("knob_type").value === "string"){
            console.log("Evaluating: " + knob_type);
            validate_knob_string();
        }
        else if (document.getElementById("knob_type").value === "checkbox"){
            console.log("Evaluating: " + knob_type);
            validate_knob_checkbox();
        }
    });

    // Discard changes
    $("#discard_details").on("click", function () {
        $("#knob_type")[0].selectedIndex = 0;
        discard_knob_changes()
    })

    $("#size").on("change keyup paste click", function () {
        updateElement("for", "size", "Size");
        contentUpdater("size", "size");
    });
}