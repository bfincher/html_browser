function deleteGroup() {
    var groupName = $('#id_name').val();
    if (confirm('Are you sure you want to delete the group ' + groupName + '?')) {
        post(Urls.deleteGroup(), {"group_name": groupName});
    }
}

$(document).ready(function() {
    $("#button-id-deletegroup").on("click", function() {
        deleteGroup();
    });
});
