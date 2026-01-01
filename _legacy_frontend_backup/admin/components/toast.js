/**
 * Toast Notification System
 * Substitui alert() por notificações visuais elegantes.
 */

class Toast {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const colors = {
            success: { bg: 'rgba(34, 197, 94, 0.95)', icon: '✅' },
            error: { bg: 'rgba(239, 68, 68, 0.95)', icon: '❌' },
            warning: { bg: 'rgba(234, 179, 8, 0.95)', icon: '⚠️' },
            info: { bg: 'rgba(59, 130, 246, 0.95)', icon: 'ℹ️' }
        };

        const config = colors[type] || colors.info;

        toast.style.cssText = `
            background: ${config.bg};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            min-width: 250px;
            max-width: 400px;
            animation: slideIn 0.3s ease;
        `;

        toast.innerHTML = `
            <span style="font-size: 1.2rem;">${config.icon}</span>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" style="
                margin-left: auto;
                background: transparent;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 1.2rem;
                opacity: 0.7;
            " aria-label="Fechar notificação">×</button>
        `;

        this.container.appendChild(toast);

        // Auto-remove
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);

        return toast;
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// CSS Animations (injected once)
const toastStyles = document.createElement('style');
toastStyles.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(toastStyles);

// Global instance
window.toast = new Toast();
