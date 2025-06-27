// Configuración (REEMPLAZA ESTO)
const scriptURL = "https://script.google.com/macros/s/AKfycbzkjoPaxaOwwKcq5yYOYrGb8A7HwaozBWysKn0bUDn7ZUJbI4q0ON4fAyxeSFG-Dg0/exec";

async function register() {
  const username = document.getElementById('register-username').value;
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;

  try {
    const response = await fetch(scriptURL, {
      method: 'POST',
      body: JSON.stringify({
        action: 'register',
        username,
        email,
        password
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const result = await response.json();
    
    if (result.success) {
      alert("¡Registro exitoso! Ahora puedes iniciar sesión");
      toggleForms();
    } else {
      throw new Error(result.message || "Error en el registro");
    }
  } catch (error) {
    alert(error.message);
    console.error("Error:", error);
  }
}

async function login() {
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  try {
    const response = await fetch(scriptURL, {
      method: 'POST',
      body: JSON.stringify({
        action: 'login',
        email,
        password
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const result = await response.json();
    
    if (result.success) {
      localStorage.setItem('user', JSON.stringify(result.user));
      window.location.href = 'panel.html';
    } else {
      throw new Error(result.message || "Credenciales incorrectas");
    }
  } catch (error) {
    alert(error.message);
    console.error("Error:", error);
  }
}