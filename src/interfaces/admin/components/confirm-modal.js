/**
 * Modal de Confirmação Customizado
 * Substitui confirm() nativo por modal elegante.
 */

class ConfirmModal {
    constructor() {
        this.modal = this.createModal();
        this.resolveCallback = null;
    }

    createModal() {
        const modal = document.createElement('div');
        modal.id = 'confirm-modal';
        modal.className = 'modal hidden';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 400px;">
                <h3 id="confirm-title" style="margin-bottom: 1rem;">Confirmar Ação</h3>
                <p id="confirm-message" style="color: #94a3b8; margin-bottom: 1.5rem;"></p>
                <div class="modal-actions">
                    <button id="confirm-cancel" class="btn secondary" aria-label="Cancelar">Cancelar</button>
                    <button id="confirm-ok" class="btn danger" aria-label="Confirmar">Confirmar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector('#confirm-cancel').addEventListener('click', () => this.resolve(false));
        modal.querySelector('#confirm-ok').addEventListener('click', () => this.resolve(true));

        return modal;
    }

    async show(message, title = 'Confirmar Ação', okText = 'Confirmar', okClass = 'danger') {
        document.getElementById('confirm-title').textContent = title;
        document.getElementById('confirm-message').textContent = message;

        const okBtn = document.getElementById('confirm-ok');
        okBtn.textContent = okText;
        okBtn.className = `btn ${okClass}`;

        this.modal.classList.remove('hidden');
        this.modal.style.display = 'flex';

        return new Promise(resolve => {
            this.resolveCallback = resolve;
        });
    }

    resolve(value) {
        this.modal.classList.add('hidden');
        this.modal.style.display = 'none';
        if (this.resolveCallback) {
            this.resolveCallback(value);
            this.resolveCallback = null;
        }
    }
}

// Global instance
window.confirmModal = new ConfirmModal();

// Helper function to replace confirm()
window.showConfirm = async (message, title, okText, okClass) => {
    return await window.confirmModal.show(message, title, okText, okClass);
};
