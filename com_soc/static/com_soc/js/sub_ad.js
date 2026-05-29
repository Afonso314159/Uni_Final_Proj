// com_soc/static/com_soc/js/sub_ad.js

async function selectPlan(plano) {
  const buttons = document.querySelectorAll('.sub-plan-btn');
  buttons.forEach(btn => btn.disabled = true);

  try {
    const response = await fetch('/com_soc/subscricao/checkout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ plano }),
    });

    const data = await response.json();

    if (data.checkout_url) {
      window.location.href = data.checkout_url;
    } else {
      alert(data.error || 'Erro ao iniciar pagamento. Tenta novamente.');
      buttons.forEach(btn => btn.disabled = false);
    }
  } catch (error) {
    console.error('Erro Stripe:', error);
    alert('Erro ao iniciar pagamento. Tenta novamente.');
    buttons.forEach(btn => btn.disabled = false);
  }
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function showToast(message, type = 'info') {
    const toast        = document.getElementById('toast');
    const toastMsg     = toast.querySelector('.toast-message');
    const toastIcon    = toast.querySelector('.toast-icon');
 
    toastMsg.textContent = message;
 
    if (type === 'error') {
        toastIcon.textContent        = '✕';
        toastIcon.style.background   = 'linear-gradient(135deg, #ef4444, #dc2626)';
        toastIcon.style.boxShadow    = '0 4px 12px rgba(220, 38, 38, 0.25)';
    } else {
        toastIcon.textContent        = 'i';
        toastIcon.style.background   = 'linear-gradient(135deg, #3b82f6, #2563eb)';
        toastIcon.style.boxShadow    = '0 4px 12px rgba(37, 99, 235, 0.25)';
    }
 
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}