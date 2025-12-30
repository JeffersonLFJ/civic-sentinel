/**
 * Utility Functions for Button States
 */

function setButtonLoading(button, isLoading, originalText = null) {
    if (isLoading) {
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = `<span class="btn-spinner"></span> Aguarde...`;
    } else {
        button.disabled = false;
        button.innerHTML = originalText || button.dataset.originalText || 'OK';
    }
}

// Inject spinner CSS if not present
if (!document.getElementById('btn-spinner-style')) {
    const style = document.createElement('style');
    style.id = 'btn-spinner-style';
    style.textContent = `
        .btn-spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: btn-spin 0.8s linear infinite;
            vertical-align: middle;
            margin-right: 5px;
        }
        @keyframes btn-spin {
            to { transform: rotate(360deg); }
        }
        .btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);
}

window.setButtonLoading = setButtonLoading;
