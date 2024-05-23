function checkMatch() {
    var currentPassword = document.getElementById("currentPassword").value;
    var password = document.getElementById("newPassword").value;
    var password2 = document.getElementById("confirmPassword").value;
    var score = display_pass_score();
    
    if (password === password2 && password !== "" && password2 !== "" && currentPassword !== ""&& score >= 60){
        toggleMessage('Las contraseñas coinciden', 'green');   
        return true;
    }
    if (password !== password2 && password !== "" && password2 !== "" && currentPassword !== ""){
        toggleMessage('Las contraseñas no coinciden', 'red');
        return false;
    }    
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
    var page = window.location.pathname;
    var code = document.getElementById("verificationCode").value;
    var submitButton = document.getElementById("submit");
    var errorMessage = document.getElementById("message");
    if (code !== "" && code.length === 8) {
        if (page === "/UI/user_settings") {
            var box_check = document.getElementById("check-aceptar");
            box_check.style.display = "block";
        }
        submitButton.disabled = false;
        submitButton.style.cursor = "pointer";
        submitButton.style.backgroundColor = "#45a049";
        errorMessage.style.display = "none";
    }
    if (code === "") {
        if (page === "/UI/user_settings") {
            var box_check = document.getElementById("check-aceptar");
            box_check.style.display = "none";
        }
        submitButton.disabled = true;
        submitButton.style.cursor = "not-allowed";
        submitButton.style.backgroundColor = "#cccccc";
        box_check.style.display = "none";
        errorMessage.style.display = "block";
        errorMessage.innerHTML = "El código no puede estar vacío";
    }
}