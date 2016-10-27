    function deleteGroup(groupName) {
        if (confirm('Are you sure you want to delete the group ' + groupName + '?')) {
                post(baseUrl + "groupAdminAction/", {'action': 'deleteGroup',
                    'groupToDelete': groupName});
        }
    }
