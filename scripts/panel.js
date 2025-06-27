document.addEventListener('DOMContentLoaded', () => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        window.location.href = 'index.html';
        return;
    }

    document.getElementById('username').textContent = user.username;
    document.getElementById('balance').textContent = user.balance;
    document.getElementById('referrals').textContent = user.referrals;
    document.querySelectorAll('#user-ref').forEach(el => {
        el.textContent = user.username;
    });
});

function copyLink(linkNum) {
    const links = [
        `https://ganadinerool.com/ref=${document.getElementById('username').textContent}`,
        `https://ganadinerool.com/promo?ref=${document.getElementById('username').textContent}`,
        `https://ganadinerool.com/offer?ref=${document.getElementById('username').textContent}`
    ];
    
    navigator.clipboard.writeText(links[linkNum - 1]);
    alert('Enlace copiado!');
}