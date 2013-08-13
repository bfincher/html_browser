
    function deleteGroup(groupName) {
        if (confirm('Are you sure you want to delete the group ' + groupName + '?')) {
                var url = baseUrl + "groupAdminAction/?action=deleteGroup"
                        + "&groupToDelete=" + encodeURI(groupName);

                window.location = url;
        }
    }

    function addGroup() {
        var newGroup = prompt("Please enter the new group name");
	if (newGroup != null) {
	    var url = baseUrl + "groupAdminAction/?action=addGroup"
	        + "&groupName=" + encodeURI(newGroup)
                + "&submit=Save";

            window.location = url;
	}
    }
