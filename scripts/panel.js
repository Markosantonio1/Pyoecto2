document.addEventListener('DOMContentLoaded', () => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        window.location.href = 'index.html';
        return;
    }

    // Mostrar datos del usuario
    document.getElementById('username').textContent = user.username;
    document.getElementById('balance').textContent = user.balance;
    document.getElementById('referrals').textContent = user.referrals;
    
    // Actualizar enlaces de referencia
    document.querySelectorAll('#user-ref').forEach(el => {
        el.textContent = user.username;
    });
});

function copyLink(button) {
    const linkText = button.previousElementSibling.textContent;
    navigator.clipboard.writeText(linkText.trim())
        .then(() => {
            button.textContent = 'Copiado!';
            setTimeout(() => {
                button.textContent = 'Copiar';
            }, 2000);
        })
        .catch(err => {
            console.error('Error al copiar:', err);
        });
}
