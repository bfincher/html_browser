    function validatePassword(formName) {
        form = document.getElementById(formName);
        var valid = false;

        if (form.password.value.length == 0) {
                valid = false;
        }
        else if (form.password.value.length < 6) {
            document.getElementById('pwErrorText').innerHTML='Passwords must be at least 6 characters';
            valid = false;
        } else if (form.password.value == form.verifyPassword.value) {
            valid = true;
            document.getElementById('pwErrorText').innerHTML='';
        } else {
            document.getElementById('pwErrorText').innerHTML='Passwords do not match';
            valid = false;
        }


        form.Save.disabled = !valid;
    }

    function deleteUser(userName) {
        if (confirm('Are you sure you want to delete the user ' + userName + '?')) {
                var url = baseUrl + "userAdminAction/?action=deleteUser"
                        + "&userToDelete=" + encodeURI(userName)
                        + "&submit=Save";

                window.location = url;
        }
    }
