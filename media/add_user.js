	var userNameInValid = false;
	var passwordInValid = false;
	
	function validateUserName(userNameId, okButtonId) {
        const userName = document.getElementById(userNameId);
        var valid = false;        
        
        if (userName.value.length < 6) {
            document.getElementById('userNameErrorText').innerHTML='User Names must be at least 6 characters';
            valid = false;
        } else if (userName.value.match('[a-zA-Z_0-9]+') == userName.value) {
            valid = true;
            document.getElementById('userNameErrorText').innerHTML='';
        } else {
            valid = false;
            document.getElementById('userNameErrorText').innerHTML='User Names must only contain letters, numbers, and underscores';
        }        
        
        userNameInValid = !valid;                
                
        document.getElementById(okButtonId).disabled=(userNameInValid || passwordInValid);
        
    }
	 
	function validatePassword(passwordId, verifyPasswordId, okButtonId) {
		const password = document.getElementById(passwordId);
		const verifyPassword = document.getElementById(verifyPasswordId);
		
        var valid = false;
        
        if (password.value.length < 6) {
            document.getElementById('pwErrorText').innerHTML='Passwords must be at least 6 characters';
            valid = false;
        } else if (password.value == verifyPassword.value) {
            valid = true;
            document.getElementById('pwErrorText').innerHTML='';
        } else {
            document.getElementById('pwErrorText').innerHTML='Passwords do not match';
            valid = false;
        }
        
        
        passwordInValid = !valid;
        document.getElementById(okButtonId).disabled=(userNameInValid || passwordInValid);
    }

    $(document).ready(function() {
        $('#submit-id-submit').attr('disabled', 'disabled');
    });
