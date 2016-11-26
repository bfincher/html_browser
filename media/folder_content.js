var currentFolder = null;
var currentPath = null;
var userCanRead = null;
var userCanWrite = null;
var userCanDelete = null;
var contentActionUrl = null;

function setContentActionUrl(_contentActionUrl) {
    "use strict";
    contentActionUrl = _contentActionUrl;
}

function myEscape(str) {
    "use strict";
    str = str.replace(/,/g, "(comma)");
    str = encodeURIComponent(str);
    str = str.replace(/&/g, "(ampersand)");
    return str;
}

function setCurrentFolder(_currentFolder) {
    "use strict";
    currentFolder = _currentFolder;
}

function setCurrentPath(_currentPath) {
    "use strict";
    if (_currentPath == "") {
        currentPath = "/";
    } else {
        currentPath = _currentPath;
    }
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

function getNumCheckedBoxes() {
    return $(".content-checkbox:checkbox:checked").length;
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

    postForm($("#content-form"), contentActionUrl, {"action": "copyToClipboard",
        "currentFolder": currentFolder,
        "currentPath": currentPath});
}

function rename() {
    "use strict";
    if (!userCanWrite) {
        alert("You do not have permission to rename files in this folder");
        return;
    }

    var numChecked = getNumCheckedBoxes();

    if (numChecked == 0) {
        alert("No entry selected");
        return;
    } else if (numChecked > 1) {
        alert("Can only rename one file at a time");
        return;
    }

    var newName = prompt("Please enter new file name for " + checkedBoxes[0].id, "");

    if (newName != null) {
        postForm($("#content-form"), contentActionUrl, {"action": "rename",
            "file": checkedBoxes[0].id,
            "newName": newName,
            "currentFolder": currentFolder,
            "currentPath": currentPath});
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

    postForm($("#content-form"), contentActionUrl, {"action": "cutToClipboard",
        "currentFolder": currentFolder,
        "currentPath": currentPath});
}

function paste() {
    "use strict";
    if (!userCanWrite) {
        alert("You don't have write permission on this folder");
        return;
    }

    postForm($("#content-form"), contentActionUrl, {"action": "pasteFromClipboard",
        "currentFolder": currentFolder,
        "currentPath": currentPath});
}

function zip() {
    "use strict";
    if (!areBoxesChecked()) {
        alert("No entries selected");
    } else {
        postForm($("#content-form"), "/hb/download_zip",
            {"currentFolder": currentFolder,
             "currentPath": currentPath},
             "get");
    }
}

function upload() {
    "use strict";
    window.location="/hb/upload/?currentFolder="
    + myEscape(currentFolder)
    + "&currentPath=" + myEscape(currentPath);
}

function del() {
    "use strict";
    if (!userCanDelete) {
        alert("You do not have permission to delete from this folder");
        return;
    }
    var numChecked = getNumCheckedBoxes()

    if (numChecked == 0) {
        alert("No entries selected");
    } else {
        if (numChecked == 1) {
            var confirmMessage = "Are you sure you want to delete the selected entry?";
        } else {
            var confirmMessage = "Are you sure you want to delete the " + numChecked + " selected entries?";
        }

        if (confirm(confirmMessage)) {
            postForm($("#content-form"), contentActionUrl, {"action": "deleteEntry",
                "currentFolder": currentFolder,
                "currentPath": currentPath});
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
        postForm($("#content-form"), contentActionUrl, {"action": "mkDir",
            "dir": dir,
            "currentFolder": currentFolder,
            "currentPath": currentPath});
    }
}

function viewTypeBoxChanged(box) { 
    "use strict";
    var selectedIndex = box.selectedIndex;
    if (selectedIndex != -1) {
        postForm($("#content-form"), contentActionUrl, {"action": "setViewType",
            "viewType": box.options[selectedIndex].text,
            "currentFolder": myEscape(currentFolder),
            "currentPath": myEscape(currentPath)});
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
    $("#checkAll").click(function() {
        checkAll();
    });
});
