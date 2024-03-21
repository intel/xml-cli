function setCSRF(xhr, settings) {
    // xhr.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken)
    }
}

function value_setter(value, location) {
    if (localStorage.getItem(value)) {
        if (localStorage.getItem(value) !== "undefined") {
            $(location).val(localStorage.getItem(value));
        }
    }
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function CustomRequest(content) {
    console.log("Running Request for --- ");
    console.log(content);
    let status = $.ajax({
        url: content.url,
        method: content.method,
        data: JSON.stringify(content.data),
        contentType: "application/json;charset=utf-8",
        // beforeSend: setCSRF,
        success: function (responseObj) {
            sessionStorage.setItem("server_response", JSON.stringify(responseObj));
            console.log("CustomRequest success!");
            if (content.id_to_remove) {
                $('tr#' + content.data.id_to_remove).remove();
            }
            // location.reload(true);
            toastr.success('Please refresh the Page by clicking F5 or reload button to see the changes in effect!');
            return JSON.stringify(responseObj);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("some error " + String(errorThrown) + String(textStatus) + String(XMLHttpRequest.responseText));
            toastr.error("There has been error while executing the request!");
            return false;
        }
    });
    return status;
}

/**
 * @return {string}
 */
function IntToHex(element, id) {
    return parseInt(document.getElementById(id).value).toString(16);
}

function updateElement(attrib, value, text) {
    let select = "[" + attrib + "='" + value + "']";
    console.log(select);
    for (let i = 0; i < $(select).length; i++) {
        if ($("#" + value)[i].value) {
            $(select)[i].textContent = text + '(0x' + IntToHex('label', value) + ')';
        } else {
            $(select)[i].textContent = text;
        }
    }
}


function contentUpdater(key, inputId){
    console.log("updating key: " + key)
    content.data[key] = document.getElementById(inputId).value;
}

function add_common_error(error_messages, tag) {
}

function clear_errors() {
    let class_id = "invalid-feedback";
    $(".invalid-feedback").remove();
    $('.is-invalid').each(function () {
        $(this).removeClass('is-invalid');
    });

}
function add_inline_error(input_id, error_message) {
    remove_inline_error(input_id);
    let error = '<div class="invalid-feedback">' + error_message + '</div>';
    $("#" + input_id).addClass('is-invalid');
    $("#" + input_id).parent().append(error);
}

function remove_inline_error(input_id) {
    $("#" + input_id).removeClass('is-invalid');
    $("#" + input_id).parent().find('div.invalid-feedback').remove()
}

let oneOfValue = '<select type="text" class="custom-select" id="oneofForm-value" name="newValue" required></select>';

let numericValue = '<input class="form-control" id="numericForm-value" name="newValue" placeholder="" required="" type="number" value="">';

let stringValue = '<input class="form-control" id="stringForm-value" name="newValue" placeholder="Please enter valid string value" type="text" value="" required>';

let checkboxValue = '<select class="custom-select" id="checkboxForm-value" name="newValue" required="" type="text">\n' +
        '                                                <option value="0">Checked</option>\n' +
        '                                                <option value="1">Unchecked</option>\n' +
        '                                            </select>\n';

function enableValidInput(inputId, knobType) {
    console.log(inputId);
    console.log(knobType);
    let main_tag = $("#" + inputId);

    if (knobType === "oneof"){
        main_tag.html(oneOfValue);
        let choices = $("#disabled-options")[0].options;
        for (let i=0; i < choices.length; i++){
            let optionText = choices[i].text;
            let optionValue = choices[i].value;
            let option = document.createElement("option");
            option.text = optionValue + " - " + optionText;
            option.value = optionValue;
            document.getElementById("oneofForm-value").add(option);
        }
    }
    else if (knobType === "numeric"){
        main_tag.html(numericValue);
    }
    else if (knobType === "string"){
        main_tag.html(stringValue);
    }
    else if (knobType === "checkbox"){
        main_tag.html(checkboxValue)
    }
    $("#changeInput")[0].disabled = true;
    $("#saveData")[0].disabled = false;

}

function getOneOfForm() {
    let form = '<form id="oneofForm">\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="oneofForm-option">Option(s)</label>\n' +
        '                                        <div class="col-md-3 mb-1">\n' +
        '                                            <input class="form-control" id="oneofForm-option-value" name="oneofForm-option-value" placeholder="value" type="number" min="0" required>\n' +
        '                                        </div>\n' +
        '                                        <div class="col-md-3 mb-2">\n' +
        '                                            <input class="form-control" id="oneofForm-option-text" name="oneofForm-option-text" placeholder="option" type="text" required>\n' +
        '                                        </div>\n' +
        '                                        <div class="col-md-3 mb-3">\n' +
        '                                            <button type="button" class="btn btn-primary" id="oneofForm-optionAdder" name="oneofForm-optionAdder">Add Option</button>\n' +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="oneofForm-value">Value</label>\n' +
        '                                        <div class="col-md-6 mb-3">\n' +
        oneOfValue +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                </form>';
    return form
}

function getStringForm() {
    let form = '<form id="stringForm">\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="stringForm-min_characters">Minimum Characters</label>\n' +
        '                                        <div class="col-md-6 mb-3">\n' +
        '                                            <input class="form-control" id="stringForm-min_characters" name="stringForm-min_characters" placeholder="Minimum length of string" type="number" value="" required>\n' +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="stringForm-max_characters">Maximum Characters</label>\n' +
        '                                        <div class="col-md-6 mb-3">\n' +
        '                                            <input class="form-control" id="stringForm-max_characters" name="stringForm-max_characters" placeholder="Maximum length of string" type="number" value="" required>\n' +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="stringForm-value">Value</label>\n' +
        '                                        <div class="col-md-6 mb-3">\n' +
        stringValue +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                </form>';
    return form
}

function getNumericForm() {
    let form = '<form id="numericForm">\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="numericForm-min_value">Minimum Value</label>\n' +
        '                                        <div class="col-md-6 mb-3">\n' +
        '                                            <input class="form-control" id="numericForm-min_value" name="numericForm-min_value" placeholder="" required="" type="number" value="">\n' +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="numericForm-max_value">Maximum Value</label>\n' +
        '                                        <div class="col-md-6 mb-3">\n' +
        '                                            <input class="form-control" id="numericForm-max_value" name="numericForm-max_value" placeholder="" required="" type="number" value="">\n' +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="numericForm-value">Value</label>\n' +
        '                                        <div class="col-md-6 mb-3">\n' +
        numericValue +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                </form>';
    return form
}

function getCheckboxForm() {
    let form = '<form id="checkboxForm">\n' +
        '                                    <div class="form-group row">\n' +
        '                                        <label class="col-md-2 col-form-label" for="checkboxForm-value">Value</label>\n' +
        '                                        <div class="col-md-6 mb-3">\n' +
        checkboxValue +
        '                                        </div>\n' +
        '                                    </div>\n' +
        '                                </form>';
    return form
}
