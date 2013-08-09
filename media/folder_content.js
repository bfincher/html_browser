
    function myEscape(str) {
        str = str.replace(",", "(comma)");
        return encodeURI(str);
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
    	var url = baseUrl + "content/?action=copyToClipboard&entries="
			+ checkedContent
			+ "&currentFolder=" + myEscape(currentFolder)
			+ "&currentPath=" + myEscape(currentPath);
			
		window.location = url;
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
	    	var url = baseUrl + "content/?action=rename"
				+ "&file=" + myEscape(checkedBoxes[0].id)
				+ "&newName=" + myEscape(newName)
				+ "&currentFolder=" + myEscape(currentFolder)
				+ "&currentPath=" + myEscape(currentPath);
    	
    		window.location = url;
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
    	var url = baseUrl + "content/?action=cutToClipboard&entries="
			+ checkedContent
			+ "&currentFolder=" + myEscape(currentFolder)
			+ "&currentPath=" + myEscape(currentPath);
			
		window.location = url;
    }
    
    function paste() {
    	if (!userCanWrite) {
    		alert("You don't have write permission on this folder");
    		return;
    	}
    	
    	var url = baseUrl + "content/?action=pasteFromClipboard"
			+ "&currentFolder=" + myEscape(currentFolder)
			+ "&currentPath=" + myEscape(currentPath);
    	
    	window.location = url;
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
    	    var url = baseUrl + "deleteImage?currentFolder=" + myEscape(currentFolder)
    		+ "&currentPath=" + myEscape(currentPath)
		+ "&fileName=" + myEscape(fileName);

    	    window.location = url;
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
    			var url = baseUrl + "content/?action=deleteEntry&entries="
    				+ checkedContent
    				+ "&currentFolder=" + myEscape(currentFolder)
    				+ "&currentPath=" + myEscape(currentPath);
    				
    			window.location = url;
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
	    	var url = baseUrl + "content/?action=mkDir"
				+ "&dir=" + myEscape(dir)
				+ "&currentFolder=" + myEscape(currentFolder)
				+ "&currentPath=" + myEscape(currentPath);
    	
    		window.location = url;
    	}
    }
    
    function getCheckedBoxContent() {
    	var checkedBoxes = getCheckedBoxes();
    	var checkedContent = "";
    	
    	for (i = 0; i < checkedBoxes.length; i++) {
    		checkedContent = checkedContent + myEscape(checkedBoxes[i].id);
    				
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
    		var url = baseUrl + "content/?action=setViewType"
    			+ "&viewType=" + box.options[selectedIndex].text
				+ "&currentFolder=" + myEscape(currentFolder)
				+ "&currentPath=" + myEscape(currentPath);
    		window.location = url;
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

