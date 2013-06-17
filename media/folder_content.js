
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
    	var url = "/hb/content/?action=copyToClipboard&entries="
			+ encodeURI(checkedContent)
			+ "&currentFolder=" + encodeURI(currentFolder)
			+ "&currentPath=" + encodeURI(currentPath);
			
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
	    	var url = "/hb/content/?action=rename"
				+ "&file=" + encodeURI(checkedBoxes[0].id)
				+ "&newName=" + encodeURI(newName)
				+ "&currentFolder=" + encodeURI(currentFolder)
				+ "&currentPath=" + encodeURI(currentPath);
    	
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
    	var url = "/hb/content/?action=cutToClipboard&entries="
			+ encodeURI(checkedContent)
			+ "&currentFolder=" + encodeURI(currentFolder)
			+ "&currentPath=" + encodeURI(currentPath);
			
		window.location = url;
    }
    
    function paste() {
    	if (!userCanWrite) {
    		alert("You don't have write permission on this folder");
    		return;
    	}
    	
    	var url = "/hb/content/?action=pasteFromClipboard"
			+ "&currentFolder=" + encodeURI(currentFolder)
			+ "&currentPath=" + encodeURI(currentPath);
    	
    	window.location = url;
    }
    
    function zip() {
    	var checkedBoxes = getCheckedBoxes();
    	
    	if (checkedBoxes.length == 0) {
    	    alert("No entries selected");
    	} else {
    	    window.location="/hb/download_zip?currentFolder="
    	    + encodeURI(currentFolder)
    	    + "&currentPath=" + encodeURI(currentPath)
    	    + "&files=" + encodeURI(getCheckedBoxContent());
    	}
    }
    
    function upload() {
    	window.location="/hb/upload/?currentFolder="
    		+ encodeURI(currentFolder)
    	    + "&currentPath=" + encodeURI(currentPath);
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
    			var confirmMessage = "Are you sure you want to delete " + checkedBoxes[0].id;
    		} else {
    			var confirmMessage = "Are you sure you want to delete the following entries: \n" + checkedContent;
    		}
    			
    		if (confirm(confirmMessage)) {
    			var url = "/hb/content/?action=deleteEntry&entries="
    				+ encodeURI(checkedContent)
    				+ "&currentFolder=" + encodeURI(currentFolder)
    				+ "&currentPath=" + encodeURI(currentPath);
    				
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
	    	var url = "/hb/content/?action=mkDir"
				+ "&dir=" + encodeURI(dir)
				+ "&currentFolder=" + encodeURI(currentFolder)
				+ "&currentPath=" + encodeURI(currentPath);
    	
    		window.location = url;
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
    		var url = "/hb/content/?action=setViewType"
    			+ "&viewType=" + box.options[selectedIndex].text
				+ "&currentFolder=" + encodeURI(currentFolder)
				+ "&currentPath=" + encodeURI(currentPath);
    		window.location = url;
    	}
    }
