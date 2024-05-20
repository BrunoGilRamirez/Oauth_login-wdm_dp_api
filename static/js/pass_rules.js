cached_time = new Date();
code_sended = false;
function togglePasswordChange() {
    const passwordChangeContainer = document.getElementById('passwordChangeContainer');
    passwordChangeContainer.classList.toggle('active');
}

function disable_password(disable){
    var currentPassword = document.getElementById("currentPassword");
    var newPassword = document.getElementById("newPassword");
    var confirmPassword = document.getElementById("confirmPassword");
    if (disable){
        //currentPassword.disabled = true;
        //newPassword.disabled = true;
        //confirmPassword.disabled = true;
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
        disable_password(true);
        if (code_sended && new Date().getTime() < cached_time.getTime()){
            dt = deltaTime();
            toggleVerificationCode(dt);
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
                code_sended = true;
            })
            .catch(error => console.log('error', error));
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

function checkMatch() {
    var currentPassword = document.getElementById("currentPassword").value;
    var password = document.getElementById("newPassword").value;
    var password2 = document.getElementById("confirmPassword").value;
    var box_check = document.getElementById("check-aceptar");
    var score = display_pass_score();
    
    if (password === password2 && password !== "" && password2 !== "" && currentPassword !== ""&& score >= 60){
        box_check.style.display = "block";
        toggleMessage('Las contraseñas coinciden', 'green');   
    }
    if (password !== password2 && password !== "" && password2 !== "" && currentPassword !== ""){
        box_check.style.display = "none";
        toggleMessage('Las contraseñas no coinciden', 'red');
    }    
}

function toggleMessage(msg, color) {
    var errorMessage = document.getElementById("message");
    var input_password = document.getElementById("newPassword");
    var input_confirm_password = document.getElementById("confirmPassword");
    errorMessage.innerHTML = JSON.stringify(msg, null, 4);
    errorMessage.style.color = color;
    errorMessage.style.display = "block";
    input_password.style.borderWidth = "2px";
    input_confirm_password.style.borderWidth = "2px";
    input_password.style.borderColor = color;
    input_confirm_password.style.borderColor = color;
}
function checkVer() {
    var code = document.getElementById("verificationCode").value;
    var submitButton = document.getElementById("submit");
    var box_check = document.getElementById("check-aceptar");
    var errorMessage = document.getElementById("message");
    if (code !== "" && code.length === 8) {
        submitButton.disabled = false;
        submitButton.style.cursor = "pointer";
        submitButton.style.backgroundColor = "#45a049";
        box_check.style.display = "block";
        errorMessage.style.display = "none";
    }
    if (code === "") {
        submitButton.disabled = true;
        submitButton.style.cursor = "not-allowed";
        submitButton.style.backgroundColor = "#cccccc";
        box_check.style.display = "none";
        errorMessage.style.display = "block";
        errorMessage.innerHTML = "El código no puede estar vacío";
    }
}

function checkPassStrength(pass){
    let passwordVariations = {
        digits: /\d/.test(pass),//1
        lower: /[a-z]/.test(pass),//2
        upper: /[A-Z]/.test(pass),//3
        special: /[!@#\$%\^&\*-.+?<>_:]/.test(pass),//4 simbolos: !@#$%^&*-.+?<>
        nonWordswithDigits: /\W/.test(pass),//5
        strength: 'Inaceptable',
        progress: 0
    }

    let variationCount = 0;
    for (var check in passwordVariations) {
        variationCount += (passwordVariations[check] === true) ? 1 : 0;
    }
    if (variationCount === 5) {
        passwordVariations.progress = variationCount * 20   
        passwordVariations.strength = "Excelente"
    }
    if (variationCount === 4) {
        passwordVariations.progress = variationCount * 20   
        passwordVariations.strength = "Buena"
    }
    if (variationCount === 3) {
        passwordVariations.progress = variationCount * 20   
        passwordVariations.strength = "Aceptable"
    }else if (variationCount < 3) {
        passwordVariations.progress = variationCount * 20
    }
    
    return passwordVariations;
}

function display_pass_score(){
    var password = document.getElementById("newPassword").value;
    var scorebar = document.getElementById("bar");
    var rules = document.getElementById("rules");
    var barSegments = document.querySelectorAll('.bar-segment');
    var score_points = checkPassStrength(password);
    var messagequality = document.getElementById("Quality");
    
        // for each segment of score_points
        Object.keys(score_points).forEach((key, index) => {
            if (score_points[key] === true) {
                barSegments[index].style.backgroundColor = 'green';
            }
            if (score_points[key] === false) {
                barSegments[index].style.backgroundColor = 'red';
            }
        }
        );
        char_left = 8 - password.length;
    if (password.length < 8 && password!=="") {
        messagequality.innerHTML = "La contraseña es demasiado corta: Faltan " + char_left + " caracteres para ser admisible."+"<br> Calidad de la contraseña:"+ score_points.strength + "(" + score_points.progress + "%)";
        messagequality.style.color = "red";
    }else if (password!==""){
        messagequality.innerHTML = "Calidad de la contraseña: " + score_points.strength + " (" + score_points.progress + "%)";
        messagequality.style.color = "green";
    }
    messagequality.style.display = "block";
    rules.style.display = "block";
    scorebar.style.display = "flex";
    return score_points.progress;

}