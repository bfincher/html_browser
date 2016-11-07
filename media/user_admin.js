    function deleteUser() {
        var userName = $('#id_userName').val();
        if (confirm('Are you sure you want to delete the user ' + userName + '?')) {
                post(baseUrl + "deleteUser/", {'userToDelete': userName});
        }
    }

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


        if (valid) {
            $('#submit-id-submit').removeAttr('disabled');
        } else {
            $('#submit-id-submit').attr('disabled', 'disabled');
        }
    }

    $(document).ready(function() {
        $("#id_password").keyup(function() {
            validatePassword('form');
        });

        $("#id_verifyPassword").keyup(function() {
            validatePassword('form');
        });

        $("#button-id-deleteuser").click(function() {
            deleteUser();
        });
    });
