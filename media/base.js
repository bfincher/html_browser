function setCsrf(_csrf) {
    csrf = _csrf;
}

function postForm(form, path, params, method="post", appendToDoc=false) {
    form.attr("method", method);
    form.attr("action", path);

    form.append(csrf);

    $.each(params, function(key, value) {
        var field = $('<input></input>');
        field.attr("type", "hidden");
        field.attr("name", key);
        field.attr("value", value);

        form.append(field);
    });

    if (appendToDoc) {
        $(document.body).append(form);
    }
    
    console.log('calling form.submit');
    console.log(form);
    form.submit();
}

function post(path, params, method="post") {
    var form = $('<form></form>');
    postForm(form, path, params, method, true);
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
