
    function setContentActionUrl(_contentActionUrl) {
        contentActionUrl = _contentActionUrl;
    }

    function myEscape(str) {
        str = str.replace(/,/g , "(comma)");
        str = encodeURIComponent(str);
        str = str.replace(/&/g , "(ampersand)");
        return str;
    }
    function setCurrentFolder(_currentFolder) {
    	currentFolder = _currentFolder;
    }
    
    function setCurrentPath(_currentPath) {
    	currentPath = _currentPath;
    }
    
    function setUserCanRead(_userCanRead) {
    	userCanRead = _userCanRead;
    }
    
    function setUserCanWrite(_userCanWrite) {
    	userCanWrite = _userCanWrite;
    }
    
    function setUserCanDelete(_userCanDelete) {
    	userCanDelete = _userCanDelete;
    }
    
    function copy() {    	
		var checkedBoxes = getCheckedBoxes();
    	
    	if (checkedBoxes.length == 0) {
    	    alert("No entries selected");
    	    return;
    	}
    	
    	var checkedContent = getCheckedBoxContent();

        post(contentActionUrl, {'action': 'copyToClipboard',
            'entries': checkedContent,
            'currentFolder': currentFolder,
            'currentPath': currentPath});

    }
    
    function rename() {
    	if (!userCanWrite) {
    		alert("You do not have permission to rename files in this folder");
    		return;
    	}
    	
    	var checkedBoxes = getCheckedBoxes();
    	
    	if (checkedBoxes.length == 0) {
    	    alert("No entry selected");
    	    return;
    	} else if (checkedBoxes.length > 1) {
    		alert("Can only rename one file at a time");
    		return;
    	}
    	
    	var newName = prompt("Please enter new file name for " + checkedBoxes[0].id, "");
    	
    	if (newName != null) {    	
            post(contentActionUrl, {'action': 'rename',
                'file': checkedBoxes[0].id,
                'newName': newName,
                'currentFolder': currentFolder,
                'currentPath': currentPath});
    	}
    	
    	
    	
  	}
    
    function cut() {
    	if (!userCanDelete) {
			alert("You do not have permission to delete from this folder");
			return;
		}
    	
		var checkedBoxes = getCheckedBoxes();
    	
    	if (checkedBoxes.length == 0) {
    	    alert("No entries selected");
    	    return;
    	}
    	
    	var checkedContent = getCheckedBoxContent();
        post(contentActionUrl, {'action': 'cutToClipboard',
            'entries': checkedContent,
            'currentFolder': currentFolder,
            'currentPath': currentPath});
    }
    
    function paste() {
    	if (!userCanWrite) {
    		alert("You don't have write permission on this folder");
    		return;
    	}
    	
        post(contentActionUrl, {'action': 'pasteFromClipboard',
            'currentFolder': currentFolder,
            'currentPath': currentPath});
    }
    
    function zip() {
    	var checkedBoxes = getCheckedBoxes();
    	
    	if (checkedBoxes.length == 0) {
    	    alert("No entries selected");
    	} else {
    	    window.location="/hb/download_zip?currentFolder="
    	    + myEscape(currentFolder)
    	    + "&currentPath=" + myEscape(currentPath)
    	    + "&files=" + getCheckedBoxContent();
    	}
    }
    
    function upload() {
    	window.location="/hb/upload/?currentFolder="
    		+ myEscape(currentFolder)
    	    + "&currentPath=" + myEscape(currentPath);
    }
    
    function deleteImage(fileName) {
    	if (!userCanDelete) {
    		alert("You do not have permission to delete from this folder");
    		return;
    	}

    	var confirmMessage = "Are you sure you want to delete the selected entry?";
	    if (confirm(confirmMessage)) {
            post(baseUrl + "deleteImage", {'action': 'deleteImage',
                'fileName': fileName,
                'currentFolder': currentFolder,
                'currentPath': currentPath});
	}
        
    }
    function del() {    	
    	
    	if (!userCanDelete) {
    		alert("You do not have permission to delete from this folder");
    		return;
    	}
    	var checkedBoxes = getCheckedBoxes();
    	
    	if (checkedBoxes.length == 0) {
    	    alert("No entries selected");
    	} else {
    	    var checkedContent = getCheckedBoxContent();
    	    
    		if (checkedBoxes.length == 1) {
    			var confirmMessage = "Are you sure you want to delete the selected entry?";
    		} else {
    			var confirmMessage = "Are you sure you want to delete the " + checkedBoxes.length + " selected entries?";
    		}
    			
    		if (confirm(confirmMessage)) {
                post(contentActionUrl, {'action': 'deleteEntry',
                    'entries': checkedContent,
                    'currentFolder': currentFolder,
                    'currentPath': currentPath});
    		}
    	}
    }
    
    function mkdir() {
    	if (!userCanWrite) {
    		alert("You don't have write permission on this folder");
    		return;
    	}
    	
    	var dir = prompt("Please enter the directory to create:", "");
    	
    	if (dir != null) {    	
            post(contentActionUrl, {'action': 'mkDir',
                'dir': dir,
                'currentFolder': currentFolder,
                'currentPath': currentPath});
    	}
    }
    
    function getCheckedBoxContent() {
    	var checkedBoxes = getCheckedBoxes();
    	var checkedContent = "";
    	
    	for (i = 0; i < checkedBoxes.length; i++) {
    		checkedContent = checkedContent + checkedBoxes[i].id;
    				
    		if (i != checkedBoxes.length - 1) {
    			checkedContent = checkedContent + ",";
    		}
    	}
    	
    	return checkedContent;
    	
    }
    
    function getCheckedBoxes() {
    	var boxes = document.getElementsByName("cb");
    	var checkedBoxes = new Array();
    	
    	for (i = 0; i < boxes.length; i++) {
	    	if (boxes[i].checked) {
	      	  checkedBoxes[checkedBoxes.length] = boxes[i];
	    	}
    	}
    	
    	return checkedBoxes;
    }
    
    function checkAll() {    	
    	var value = document.getElementById("checkAll").checked;
    	var boxes = document.getElementsByName("cb");
    	//alert("check all " + boxes.length);
    	for (i = 0; i < boxes.length; i++) {
    	    boxes[i].checked = value;
    	}
    }
    
    function viewTypeBoxChanged(box) {  
    	var selectedIndex = box.selectedIndex;
    	if (selectedIndex != -1) {
            post(contentActionUrl, {'action': 'setViewType',
                'viewType': box.options[selectedIndex].text,
                'currentFolder': myEscape(currentFolder),
                'currentPath': myEscape(currentPath)});
    	}
    }

    function diskUsageShowPopup() {
        var el = document.getElementById("disk_usage");
        el.style.visibility = "visible";
    }

    function diskUsageHidePopup() {
        var el = document.getElementById("disk_usage");
        el.style.visibility = "hidden";
    }


