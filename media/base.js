function setCsrf(_csrf) {
    csrf = _csrf;
}

function post(path, params) {
    var form = $('<form></form>');

    form.attr("method", "post");
    form.attr("action", path);

    form.append(csrf);

    $.each(params, function(key, value) {
        var field = $('<input></input>');
        field.attr("type", "hidden");
        field.attr("name", key);
        field.attr("value", value);

        form.append(field);
    });

    $(document.body).append(form);
    
    console.log('calling form.submit');
    console.log(form);
    form.submit();
}
function setBaseUrl(_baseUrl) {
    baseUrl = _baseUrl;
}

function setMediaUrl(_mediaUrl) {
    mediaUrl = _mediaUrl;
}

function setImageUrl(_imageUrl) {
    imageUrl = _imageUrl;
}
