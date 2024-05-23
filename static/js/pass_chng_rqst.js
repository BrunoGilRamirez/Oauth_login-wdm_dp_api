cached_time = new Date();
code_sended = false;
function showLoader() {
    console.log('showing loader');
    document.getElementById('backgroundloader').style.display = 'inline-block';
}

function hideLoader() {
    console.log('hiding loader');
    document.getElementById('backgroundloader').style.display = 'none';
}
function togglePasswordChange() {
    const passwordChangeContainer = document.getElementById('passwordChangeContainer');
    passwordChangeContainer.classList.toggle('active');
}
function disable_password(disable){
    var currentPassword = document.getElementById("currentPassword");
    var newPassword = document.getElementById("newPassword");
    var confirmPassword = document.getElementById("confirmPassword");
    if (disable){
        currentPassword.contentEditable = false;
        newPassword.contentEditable = false;
        confirmPassword.contentEditable = false;
        currentPassword.style.backgroundColor = "#f2f2f2";
        newPassword.style.backgroundColor = "#f2f2f2";
        confirmPassword.style.backgroundColor = "#f2f2f2";
        currentPassword.style.cursor = "not-allowed";
        newPassword.style.cursor = "not-allowed";
        confirmPassword.style.cursor = "not-allowed";
    } else {
        currentPassword.disabled = false;
        newPassword.disabled = false;
        confirmPassword.disabled = false;
        currentPassword.style.backgroundColor = "white";
        newPassword.style.backgroundColor = "white";
        confirmPassword.style.backgroundColor = "white";
        currentPassword.style.cursor = "auto";
        newPassword.style.cursor = "auto";
        confirmPassword.style.cursor = "auto";
    }
}
function deltaTime(){
    delta= cached_time.getTime() - new Date().getTime();
    delta = delta / 1000;
    return delta;
}

function triggerCodeVerification(token) {
    // Enviar solicitud GET al endpoint /code-pass para enviar un codigo de verificación
    var myHeaders = new Headers();
    var check_box = document.getElementById("check");
    var verifCode = document.getElementById("verifCode");

    myHeaders.append("Authorization", "Bearer " + token);
    var requestOptions = {
        method: 'GET',
        headers: myHeaders,
        redirect: 'follow'
    };
    string_time = new Date(cached_time).toLocaleTimeString();
    if (check_box.checked) {
        showLoader();
        //waits a second to show the loader
        setTimeout(() => {}, 500);
        disable_password(true);
        if (code_sended && new Date().getTime() < cached_time.getTime()){//if the code was already sended and the time is not expired
            dt = deltaTime();
            toggleVerificationCode(dt);
            hideLoader();
            return;
        }
        fetch("/UI/code-pass", requestOptions)
            .then(response => {
                if (response.ok) {
                    code_sended = true;
                    json_r = response.json();
                    return json_r;
                } else {
                    throw new Error('Error al enviar el código de verificación');
                }
            })
            .then(result => {
                toggleVerificationCode(result.Expires);
                hideLoader();
                code_sended = true;
            })
            .catch(error => {
                hideLoader();
                console.error('Error:', error);
                disable_password(false);
                toggleMessage('Error al enviar el código de verificación', 'red');
                verifCode.style.display = "none";
            }
            );
        } else {
            verifCode.style.display = "none";
            disable_password(false);
        }
}

function toggleVerificationCode(expires) {
    var verifCode = document.getElementById("verifCode");
    var feedback_space = document.getElementById("feedback");
    feedback_space.style.display = "block";
    //suma el tiempo de expiración a la hora actual para mostrarla
    var date = new Date();
    var time = date.getTime();
    var expires_time = time + (expires * 1000); // Convertir segundos a milisegundos
    var expirationDate = new Date(expires_time);
    //save the expiration time on cached_time
    cached_time = expirationDate;
    feedback_space.innerHTML = "Se ha enviado un código de verificación a su correo electrónico y expirará a las: " + expirationDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    verifCode.style.display = "block";//check here

}