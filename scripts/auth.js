const scriptURL = 'https://script.google.com/macros/s/AKfycby0W_4zgRb-DUSNCSxVrI_kAF5QuHrBGzMpqYOYbX9T-VJ2xgPX_WztZ3nrcqmGjp3C/exec';

// Función para alternar entre login/registro
function toggleForms() {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
  registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
}

// Función para registrar usuario
async function register() {
  const username = document.getElementById('register-username').value;
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;

  // Validación básica
  if (!username || !email || !password) {
    alert("Por favor completa todos los campos");
    return;
  }

  try {
    const response = await fetch(scriptURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: 'register',
        username,
        email,
        password
      })
    });

    if (!response.ok) throw new Error("Error en la conexión");

    const result = await response.json();
    
    if (result.success) {
      alert(result.message || "¡Registro exitoso!");
      toggleForms();
    } else {
      throw new Error(result.message || "Error en el registro");
    }
  } catch (error) {
    console.error("Error completo:", error);
    alert("Error: " + error.message);
  }
}

// Función para login
async function login() {
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  try {
    const response = await fetch(scriptURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: 'login',
        email,
        password
      })
    });

    if (!response.ok) throw new Error("Error en la conexión");

    const result = await response.json();
    
    if (result.success) {
      // Guardar datos del usuario en localStorage
      localStorage.setItem('user', JSON.stringify(result.user));
      // Redirigir al panel
      window.location.href = 'panel.html';
    } else {
      throw new Error(result.message || "Credenciales incorrectas");
    }
  } catch (error) {
    console.error("Error completo:", error);
    alert("Error: " + error.message);
  }
}
