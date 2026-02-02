setTimeout(function () {
    var successMessage = document.querySelector('.success');
    var errorMessages = document.querySelectorAll('.error');
    var queryMessages = document.querySelectorAll('.query');

    if (successMessage) {
        successMessage.style.display = 'none';
    }

    errorMessages.forEach(function (error) {
        error.style.display = 'none';
    });

    queryMessages.forEach(function (query) {
        query.style.display = 'none';
    });
}, 3000);
function togglePassword() {
    var passwordField = document.getElementById("password");
    if (passwordField.type === "password") {
        passwordField.type = "text";
    } else {
        passwordField.type = "password";
    }
}
