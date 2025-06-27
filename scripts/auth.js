const scriptURL = 'https://script.google.com/macros/s/AKfycbxH_yr6YpIRtO6urW6dlPsCGmKO8a-AkrMVKhRl-gDSMVKFyyb_N3nskIGtlAy497Lo/exec';

// Función para alternar entre formularios
function toggleForms() {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
  registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
}

// Función mejorada para registrar usuarios
async function register() {
  const btnRegister = document.querySelector('#register-form button');
  btnRegister.disabled = true;
  btnRegister.textContent = 'Registrando...';

  try {
    const data = {
      action: 'register',
      username: document.getElementById('register-username').value.trim(),
      email: document.getElementById('register-email').value.trim(),
      password: document.getElementById('register-password').value
    };

    // Validación básica
    if (!data.username || !data.email || !data.password) {
      throw new Error('Todos los campos son obligatorios');
    }

    const response = await fetchWithTimeout(scriptURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    }, 10000); // 10 segundos de timeout

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.message || 'Error en el registro');
    }

    alert('¡Registro exitoso! Por favor inicia sesión');
    toggleForms();
    
  } catch (error) {
    console.error('Error en registro:', error);
    alert(`Error: ${error.message}`);
  } finally {
    btnRegister.disabled = false;
    btnRegister.textContent = 'Crear cuenta';
  }
}

// Función mejorada para login
async function login() {
  const btnLogin = document.querySelector('#login-form button');
  btnLogin.disabled = true;
  btnLogin.textContent = 'Iniciando...';

  try {
    const data = {
      action: 'login',
      email: document.getElementById('login-email').value.trim(),
      password: document.getElementById('login-password').value
    };

    const response = await fetchWithTimeout(scriptURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    }, 10000); // 10 segundos de timeout

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.message || 'Credenciales incorrectas');
    }

    // Guardar datos del usuario
    localStorage.setItem('user', JSON.stringify(result.user));
    window.location.href = 'panel.html';
    
  } catch (error) {
    console.error('Error en login:', error);
    alert(`Error: ${error.message}`);
  } finally {
    btnLogin.disabled = false;
    btnLogin.textContent = 'Acceder';
  }
}

// Función fetch con timeout
function fetchWithTimeout(url, options, timeout) {
  return new Promise((resolve, reject) => {
    const controller = new AbortController();
    const { signal } = controller;

    options.signal = signal;

    const timeoutId = setTimeout(() => {
      controller.abort();
      reject(new Error('Tiempo de espera agotado'));
    }, timeout);

    fetch(url, options)
      .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        resolve(response);
      })
      .catch(error => {
        clearTimeout(timeoutId);
        reject(error);
      });
  });
}
