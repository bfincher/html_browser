    function deleteGroup() {
        var groupName = $('#id_groupName').val();
        if (confirm('Are you sure you want to delete the group ' + groupName + '?')) {
                post(baseUrl + "deleteGroup/", {'groupToDelete': groupName});
        }
    }

    $(document).ready(function() {
        $("#button-id-deletegroup").click(function() {
            deleteGroup();
        });
    });
