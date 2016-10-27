
    function addGroup() {
        var newGroup = prompt("Please enter the new group name");
	    if (newGroup != null) {
            post(baseUrl + "groupAdminAction/", {'action': 'addGroup',
                'groupName': newGroup});
	    }
    }
