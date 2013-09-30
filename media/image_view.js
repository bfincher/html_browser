scrollEnabled = true;

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
    var url = baseUrl + "getNextImage?currentFolder=" + currentFolder + "&currentPath=" + currentPath + "&fileName=" + fileName;
    $("<img id='loading' src='" + imageUrl + "loading.gif' height='42' width='42' />").appendTo('#loadingDiv');
    $.ajax({url:url, 
//    done:function() {
//        scrollEnabled = true;
//    },
    success:function(result) {
        $('#loading').remove();

        if (result['hasNextImage']) {
            fileName = result['fileName']
            var table = $('#imageTable');
            table.append($('<tr><td>&nbsp</td></tr>'));
            table.append($('<tr><td>&nbsp</td></tr>'));
            var row = $('<tr>');
            var cell = $('<td>');
            cell.html("<a href='javascript:deleteImage('" + fileName + "');>Delete File</a>");
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
});
