    function deleteGroup(groupName) {
        if (confirm('Are you sure you want to delete the group ' + groupName + '?')) {
                var url = baseUrl + "groupAdminAction/?action=deleteGroup"
                        + "&groupToDelete=" + encodeURI(groupName)
                        + "&submit=Save";

                window.location = url;
        }
    }
