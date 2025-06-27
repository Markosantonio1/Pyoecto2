// Configuración
const scriptURL = 'https://script.google.com/macros/s/AKfycbzC05I9cCxhAfvLN7HUKZcZPmEgj23B_fayQLMgQVo7bmrULdS2L7ZFruotUC3vuVsS/exec'; // Reemplaza con tu ID

// Elementos del DOM
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const btnLogin = document.querySelector('#login-form button');
const btnRegister = document.querySelector('#register-form button');

// Función mejorada para peticiones
async function makeRequest(data) {
  try {
    // 1. URL con parámetros anti-cache
    const url = `${scriptURL}?callback=ctrlq&t=${Date.now()}`;
    
    // 2. Configuración especial para CORS
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain;charset=utf-8',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(data),
      redirect: 'follow',
      mode: 'no-cors'
    });

    // 3. Manejar respuesta opaca (no-cors)
    if (response.type === 'opaqueredirect') {
      return { success: true }; // Confiar en redirección
    }
    
    // 4. Procesar texto como JSON
    const text = await response.text();
    return JSON.parse(text.replace(/^.*?({.*}).*$/s, '$1'));
    
  } catch (error) {
    console.error("Detalles técnicos:", error);
    throw new Error("Problema de conexión. Intenta recargando (F5)");
  }
}

// Función de registro
async function register() {
  const username = document.getElementById('register-username').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value;

  if (!username || !email || !password) {
    alert("Todos los campos son obligatorios");
    return;
  }

  btnRegister.disabled = true;
  btnRegister.textContent = 'Registrando...';

  try {
    const result = await makeRequest({
      action: 'register',
      username,
      email,
      password
    });

    if (!result.success) throw new Error(result.message);
    
    alert("¡Registro exitoso! Por favor inicia sesión");
    toggleForms();
    
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    btnRegister.disabled = false;
    btnRegister.textContent = 'Crear cuenta';
  }
}

// Función de login
async function login() {
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  btnLogin.disabled = true;
  btnLogin.textContent = 'Iniciando...';

  try {
    const result = await makeRequest({
      action: 'login',
      email,
      password
    });

    if (!result.success) throw new Error(result.message);
    
    localStorage.setItem('user', JSON.stringify(result.user));
    window.location.href = 'panel.html';
    
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    btnLogin.disabled = false;
    btnLogin.textContent = 'Acceder';
  }
}

// Funciones auxiliares
function toggleForms() {
  loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
  registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
}

// Event listeners
document.querySelector('#register-form a').addEventListener('click', toggleForms);
document.querySelector('#login-form a').addEventListener('click', toggleForms);
btnLogin.addEventListener('click', login);
btnRegister.addEventListener('click', register);

// Verificar autenticación al cargar
if (window.location.pathname.includes('panel.html') && !localStorage.getItem('user')) {
  window.location.href = 'index.html';
}
