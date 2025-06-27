document.addEventListener('DOMContentLoaded', () => {
  // Verificar autenticación
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) {
    window.location.href = 'index.html';
    return;
  }

  // Mostrar datos del usuario
  document.getElementById('username').textContent = user.username;
  document.getElementById('balance').textContent = user.balance.toFixed(2);
  document.getElementById('referrals').textContent = user.referrals;

  // Configurar enlaces de referencia
  const baseLinks = [
    'https://ganadinerool.com/ref=',
    'https://ganadinerool.com/promo?ref=',
    'https://ganadinerool.com/offer?ref='
  ];

  const linkElements = document.querySelectorAll('.link-item');
  linkElements.forEach((element, index) => {
    const fullLink = baseLinks[index] + encodeURIComponent(user.username);
    element.querySelector('.link-text').textContent = fullLink;
    element.querySelector('button').addEventListener('click', () => {
      copyToClipboard(fullLink, element.querySelector('button'));
    });
  });
});

function copyToClipboard(text, button) {
  navigator.clipboard.writeText(text)
    .then(() => {
      const originalText = button.textContent;
      button.textContent = '¡Copiado!';
      setTimeout(() => {
        button.textContent = originalText;
      }, 2000);
    })
    .catch(err => {
      console.error('Error al copiar:', err);
      alert('No se pudo copiar. Inténtalo manualmente.');
    });
}
