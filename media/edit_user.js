    function deleteUser() {
        var userName = $('#id_userName').val();
        if (confirm('Are you sure you want to delete the user ' + userName + '?')) {
                post(baseUrl + "deleteUser/", {'userToDelete': userName});
        }
    }

    $(document).ready(function() {
        $("#button-id-deleteuser").click(function() {
            deleteUser();
        });
    });
