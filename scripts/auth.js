const scriptURL = 'https://script.google.com/macros/s/AKfycbxXieBVWKgfq4QztWRggtfR1dSsOYdcI2Tl3rXn1OYQsDnNcqwjfa5yD7z8kzT50AGk/exec';

// Función mejorada para hacer peticiones
async function makeRequest(data) {
  try {
    // URL con parámetro para evitar CORS
    const url = `${scriptURL}?callback=ctrlq&action=${data.action}`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain;charset=utf-8',
      },
      body: JSON.stringify(data),
      redirect: 'follow'
    });

    if (!response.ok) throw new Error(`Error HTTP! estado: ${response.status}`);
    
    // Procesar respuesta
    const text = await response.text();
    try {
      return JSON.parse(text);
    } catch {
      throw new Error("Respuesta no válida del servidor");
    }
  } catch (error) {
    console.error("Error completo:", error);
    throw error;
  }
}

// Función de registro
async function register() {
  const btn = document.querySelector('#register-form button');
  btn.disabled = true;
  btn.textContent = 'Registrando...';

  try {
    const result = await makeRequest({
      action: 'register',
      username: document.getElementById('register-username').value.trim(),
      email: document.getElementById('register-email').value.trim(),
      password: document.getElementById('register-password').value
    });

    if (!result.success) throw new Error(result.message);
    
    alert("¡Registro exitoso! Por favor inicia sesión");
    toggleForms();
    
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Crear cuenta';
  }
}

// Función de login
async function login() {
  const btn = document.querySelector('#login-form button');
  btn.disabled = true;
  btn.textContent = 'Iniciando...';

  try {
    const result = await makeRequest({
      action: 'login',
      email: document.getElementById('login-email').value.trim(),
      password: document.getElementById('login-password').value
    });

    if (!result.success) throw new Error(result.message);
    
    // Guardar datos del usuario
    localStorage.setItem('user', JSON.stringify(result.user));
    window.location.href = 'panel.html';
    
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Acceder';
  }
}

// Alternar entre formularios
function toggleForms() {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
  registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
}
