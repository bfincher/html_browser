
    function addGroup() {
        var newGroup = prompt("Please enter the new group name");
	    if (newGroup != null) {
            post(Urls.addGroup(), {'group_name': newGroup});
	    }
    }
