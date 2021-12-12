var scrollEnabled = true;
var imageUrl = null;
var lastImage = false;

function setImageUrl(_imageUrl) {
    imageUrl = _imageUrl;
}

function isScrolledToBottom() {
    let old = $('body').scrollTop();
    $('body').scrollTop(old + 1);

    let result = $('body').scrollTop() == old;
    console.log("scrolledToBottom = " + result);
    return result;
}

function getNextImage() {
    //scrollEnabled = false;

    let body = $('body');
    body.scrollTop(body.scrollTop() - 2);
    let url = Urls.getNextImage(folderAndPathUrl, file_name);
    $("<img id='loading' src='" + imageUrl + "loading.gif' height='42' width='42' />").appendTo('#loadingDiv');
    $.ajax({url:url, 
    success:function(result) {
        $('#loading').remove();

        if (result['hasNextImage']) {
            file_name = result['file_name']
            let table = $('#imageTable');
            table.append($('<tr><td>&nbsp</td></tr>'));
            table.append($('<tr><td>&nbsp</td></tr>'));
            let row = $('<tr>');
            let cell = $('<td>');
            $("<a />", {
                "href" : "javascript:deleteImage('" + file_name + "');",
                "text" : "Delete File"
            }).appendTo(cell);
            row.append(cell);
            table.append(row);

            row = $('<tr>');
            cell = $('<td>');
            cell.html('<img src="' + result['image_url'] + '"/>');
            row.append(cell);
            table.append(row);

        }
        else {
            lastImage = true;
        }
    }
    });
}

function deleteImage(file_name) {
    "use strict";
    if (!userCanDelete) {
        alert("You do not have permission to delete from this folder");
        return;
    }

    let confirmMessage = "Are you sure you want to delete the selected entry?";
    if (confirm(confirmMessage)) {
        post(Urls.deleteImage(folderAndPathUrl), {"file_name": file_name});
    }
}

$(document).ready(function() {
    let debounced = $.debounce(250, function() {
        if (!scrollEnabled) {
            return;
       }
       scrollEnabled = false;

       console.log("lastImage = " + lastImage);
       if (!lastImage && isScrolledToBottom()) {
           getNextImage();
       }

       window.setTimeout(function() {
           scrollEnabled = true;
       }, 500);
    });
    $(window).on('scroll', debounced); 

    // necessary for pages where the initial image is amall enough
    // to not need a scroll bar
    if ($(document).height() == $(window).height()) {
        // has scrollbar
        getNextImage();
    }

});
