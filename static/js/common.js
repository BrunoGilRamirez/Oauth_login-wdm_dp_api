cached_time = new Date();
code_sended = false;
//access keys
function copyToClipboard(elementId) {
    const text = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(text)
        .then(() => {
            console.log('Texto copiado al portapapeles:', text);
            showCopyToast();
        })
        .catch(err => {
            console.error('Error al copiar texto al portapapeles:', err);
        });
}

function showCopyToast() {
    const toast = document.getElementById('copyToast');
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000); // Mostrar la notificación durante 3 segundos
}

function deleteKey(keyId) {
    // Aquí se debe hacer la solicitud POST al servidor para eliminar la clave con el ID proporcionado
    // Puedes usar Fetch API o Axios para hacer la solicitud
    // Por ejemplo, utilizando Fetch API:
    fetch('/UI/access_keys', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Delete': keyId,
        },
        body: JSON.stringify({ keyId: keyId }),
    })
    .then(response => {
        if (response.ok) {
            // Recargar la página después de eliminar la clave
            window.location.reload();
        } else {
            console.error('Error al eliminar la clave');
        }
    })
    .catch(error => {
        console.error('Error al eliminar la clave:', error);
    });
}

function generateNewKey() {
    // Aquí se debe hacer la solicitud POST al servidor para generar una nueva clave
    // Puedes usar Fetch API o Axios para hacer la solicitud
    // Por ejemplo, utilizando Fetch API:
    fetch('/UI/access_keys', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Create': 'True',
        },
        body: JSON.stringify({}),
    })
    .then(response => {
        if (response.ok) {
            // Recargar la página después de generar la nueva clave
            window.location.reload();
        } else {
            console.error('Error al generar una nueva clave');
        }
    })
    .catch(error => {
        console.error('Error al generar una nueva clave:', error);
    });
}