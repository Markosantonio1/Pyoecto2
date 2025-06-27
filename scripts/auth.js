// Configuración
const scriptURL = 'https://script.google.com/macros/s/AKfycbxeoWtutKl8p3a4FBlTTMdFfJptDfUan8FWZY91qe_AT0SBx6AhNGBGemflAsnTIM8v/exec'; // Reemplaza TU_SCRIPT_ID

// Elementos del DOM
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const btnLogin = document.querySelector('#login-form button');
const btnRegister = document.querySelector('#register-form button');

// Función para hacer peticiones (optimizada para CORS)
async function makeRequest(data) {
  // URL con parámetro anti-cache y callback
  const url = `${scriptURL}?callback=ctrlq&t=${Date.now()}`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain;charset=utf-8', // ¡Formato clave!
        'X-Requested-With': 'XMLHttpRequest' // Ayuda con CORS
      },
      body: JSON.stringify(data),
      redirect: 'follow',
      mode: 'cors',
      credentials: 'omit'
    });

    // Manejo especial de respuestas de Google Apps Script
    if (response.redirected) {
      return await handleRedirect(response);
    }

    const text = await response.text();
    
    // Extraer JSON de posibles wrappers (para GAS)
    try {
      const json = JSON.parse(text.replace(/^.*?({.*}).*$/s, '$1'));
      if (!json.success && !json.status) {
        throw new Error("Respuesta no válida del servidor");
      }
      return json;
    } catch (e) {
      console.error("Error parseando respuesta:", e);
      throw new Error("El servidor respondió con un formato inválido");
    }
    
  } catch (error) {
    console.error("Error en la petición:", error);
    throw new Error(error.message || "Error de conexión. Intenta recargando la página (F5)");
  }
}

// Manejo de redirecciones (para respuestas de GAS)
async function handleRedirect(response) {
  try {
    const redirectURL = response.url;
    const redirectedResponse = await fetch(redirectURL, {
      method: 'GET',
      mode: 'no-cors'
    });
    return await redirectedResponse.json();
  } catch (e) {
    throw new Error("Error procesando respuesta del servidor");
  }
}

// Función de registro mejorada
async function register() {
  const username = document.getElementById('register-username').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value;

  // Validación básica
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

    if (!result.success) {
      throw new Error(result.message || "Error en el registro");
    }

    alert("¡Registro exitoso! Por favor inicia sesión");
    toggleForms();
    
  } catch (error) {
    console.error("Error en registro:", error);
    alert(`Error: ${error.message}`);
  } finally {
    btnRegister.disabled = false;
    btnRegister.textContent = 'Crear cuenta';
  }
}

// Función de login mejorada
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

    if (!result.success) {
      throw new Error(result.message || "Credenciales incorrectas");
    }

    // Guardar datos del usuario
    localStorage.setItem('user', JSON.stringify(result.user));
    window.location.href = 'panel.html';
    
  } catch (error) {
    console.error("Error en login:", error);
    alert(`Error: ${error.message}`);
  } finally {
    btnLogin.disabled = false;
    btnLogin.textContent = 'Acceder';
  }
}

// Alternar entre formularios
function toggleForms() {
  loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
  registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
}

// Event Listeners
document.querySelector('#register-form a').addEventListener('click', toggleForms);
document.querySelector('#login-form a').addEventListener('click', toggleForms);
btnLogin.addEventListener('click', login);
btnRegister.addEventListener('click', register);

// Inicialización
if (window.location.pathname.includes('panel.html') && !localStorage.getItem('user')) {
  window.location.href = 'index.html';
}
