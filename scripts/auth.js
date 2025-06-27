const scriptURL = 'https://script.google.com/macros/s/AKfycbzkjoPaxaOwwKcq5yYOYrGb8A7HwaozBWysKn0bUDn7ZUJbI4q0ON4fAyxeSFG-Dg0/exec';

function toggleForms() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
    registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
}

async function register() {
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    const data = {
        action: 'register',
        username,
        email,
        password
    };

    try {
        const response = await fetch(scriptURL, {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Registro exitoso!');
            toggleForms();
        } else {
            throw new Error(result.message || 'Error en el registro');
        }
    } catch (error) {
        alert('Error: ' + error.message);
        console.error('Error:', error);
    }
}

async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    const data = {
        action: 'login',
        email,
        password
    };

    try {
        const response = await fetch(scriptURL, {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.success) {
            localStorage.setItem('user', JSON.stringify(result.user));
            window.location.href = 'panel.html';
        } else {
            throw new Error(result.message || 'Credenciales incorrectas');
        }
    } catch (error) {
        alert('Error: ' + error.message);
        console.error('Error:', error);
    }
}
