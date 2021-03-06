var userCanRead = null;
var userCanWrite = null;
var userCanDelete = null;
var folderAndPathUrl = null;

function setFolderAndPathUrl(url) {
    folderAndPathUrl = url;
}

function myEscape(str) {
    "use strict";
    str = str.replace(/,/g, "(comma)");
    str = encodeURIComponent(str);
    str = str.replace(/&/g, "(ampersand)");
    return str;
}


function setUserCanRead(_userCanRead) {
    "use strict";
    userCanRead = _userCanRead;
}

function setUserCanWrite(_userCanWrite) {
    "use strict";
    userCanWrite = _userCanWrite;
}

function setUserCanDelete(_userCanDelete) {
    "use strict";
    userCanDelete = _userCanDelete;
}

function getCheckedBoxes() {
    return $(".content-checkbox:checkbox:checked");
}

function getNumCheckedBoxes() {
    return getCheckedBoxes().length;
}

function areBoxesChecked() {
    return getNumCheckedBoxes() > 0;
}

function copy() {
    "use strict";
    if (!areBoxesChecked()) {
        alert("No entries selected");
        return;
    }

    postForm($("#content-form"), Urls.content(folderAndPathUrl),
              {"action": "copyToClipboard"});
}

function rename() {
    "use strict";
    if (!userCanWrite) {
        alert("You do not have permission to rename files in this folder");
        return;
    }

    let numChecked = getNumCheckedBoxes();

    if (numChecked == 0) {
        alert("No entry selected");
        return;
    } else if (numChecked > 1) {
        alert("Can only rename one file at a time");
        return;
    }

    let checkedBoxes = getCheckedBoxes()
    let newName = prompt("Please enter new file name for " + checkedBoxes[0].id, "");

    if (newName != null) {
        postForm($("#content-form"), Urls.content(folderAndPathUrl), 
           {"action": "rename",
            "file": checkedBoxes[0].id,
            "newName": newName});
    }
}

function cut() {
    "use strict";
    if (!userCanDelete) {
        alert("You do not have permission to delete from this folder");
        return;
    }

    if (!areBoxesChecked()) {
        alert("No entries selected");
        return;
    }

    postForm($("#content-form"), Urls.content(folderAndPathUrl),
        {"action": "cutToClipboard"});
}

function paste() {
    "use strict";
    if (!userCanWrite) {
        alert("You don't have write permission on this folder");
        return;
    }

    postForm($("#content-form"), Urls.content(folderAndPathUrl), 
        {"action": "pasteFromClipboard"});
}

function zip() {
    "use strict";
    if (!areBoxesChecked()) {
        alert("No entries selected");
    } else {
        postForm($("#content-form"), Urls.downloadZip(folderAndPathUrl), {}, "get");
    }
}

function upload() {
    "use strict";
    window.location=Urls.upload(folderAndPathUrl);
}

function del() {
    "use strict";
    if (!userCanDelete) {
        alert("You do not have permission to delete from this folder");
        return;
    }
    let numChecked = getNumCheckedBoxes()

    if (numChecked == 0) {
        alert("No entries selected");
    } else {
        let confirmMessage = "";
        if (numChecked == 1) {
            confirmMessage = "Are you sure you want to delete the selected entry?";
        } else {
            confirmMessage = "Are you sure you want to delete the " + numChecked + " selected entries?";
        }

        if (confirm(confirmMessage)) {
            postForm($("#content-form"), Urls.content(folderAndPathUrl), 
                {"action": "deleteEntry"});
        }
    } 
}
    
function mkdir() {
    "use strict";
    if (!userCanWrite) {
        alert("You don't have write permission on this folder");
        return;
    }

    var dir = prompt("Please enter the directory to create:", "");

    if (dir != null) {
        postForm($("#content-form"), Urls.content(folderAndPathUrl), 
           {"action": "mkDir",
            "dir": dir});
    }
}

function viewTypeBoxChanged(box) { 
    "use strict";
    var selectedIndex = box.selectedIndex;
    if (selectedIndex != -1) {
        postForm($("#content-form"), Urls.content(folderAndPathUrl), 
           {"action": "setViewType",
            "view_type": box.options[selectedIndex].text});
    }
}

function diskUsageShowPopup() {
    "use strict";
    var el = document.getElementById("disk_usage");
    el.style.visibility = "visible";
}

function diskUsageHidePopup() {
    "use strict";
    var el = document.getElementById("disk_usage");
    el.style.visibility = "hidden";
}

function checkAll() {
    "use strict";
    var value = $("#checkAll").is(":checked");
    $(".content-checkbox").prop("checked", value);
}

$(document).ready(function() {
    $("#checkAll").on("click", function() {
        checkAll();
    });
});
