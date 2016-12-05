var scrollEnabled = true;
var imageUrl = null;

function setImageUrl(_imageUrl) {
    imageUrl = _imageUrl;
}

function isScrolledToBottom() {
    var old = $('body').scrollTop();
    $('body').scrollTop(old + 1);

    var result = $('body').scrollTop() == old;
    console.log("scrolledToBottom = " + result);
    return result;
}

function getNextImage() {
    //scrollEnabled = false;

    var body = $('body');
    body.scrollTop(body.scrollTop() - 2);
    var url = Urls.getNextImage(folderAndPathUrl, fileName);
    $("<img id='loading' src='" + imageUrl + "loading.gif' height='42' width='42' />").appendTo('#loadingDiv');
    $.ajax({url:url, 
    success:function(result) {
        $('#loading').remove();

        if (result['hasNextImage']) {
            fileName = result['fileName']
            var table = $('#imageTable');
            table.append($('<tr><td>&nbsp</td></tr>'));
            table.append($('<tr><td>&nbsp</td></tr>'));
            var row = $('<tr>');
            var cell = $('<td>');
            $("<a />", {
                "href" : "javascript:deleteImage('" + fileName + "');",
                "text" : "Delete File"
            }).appendTo(cell);
            row.append(cell);
            table.append(row);

            var row = $('<tr>');
            var cell = $('<td>');
            cell.html('<img src="' + result['imageUrl'] + '"/>');
            row.append(cell);
            table.append(row);

        }
        else {
            lastImage = true;
        }
    }
    });
}

function deleteImage(fileName) {
    "use strict";
    if (!userCanDelete) {
        alert("You do not have permission to delete from this folder");
        return;
    }

    var confirmMessage = "Are you sure you want to delete the selected entry?";
    if (confirm(confirmMessage)) {
        post(Urls.deleteImage(folderAndPathUrl), {"fileName": fileName});
    }
}

$(document).ready(function() {
    var debounced = $.debounce(250, function() {
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
