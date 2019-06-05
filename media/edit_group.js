function deleteGroup() {
    var groupName = $('#id_groupName').val();
    if (confirm('Are you sure you want to delete the group ' + groupName + '?')) {
        post(Urls.deleteGroup(groupName));
    }
}

$(document).ready(function() {
    $("#button-id-deletegroup").on("click", function() {
        deleteGroup();
    });
});
