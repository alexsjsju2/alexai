document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        
        const p = document.createElement('p');
        p.textContent = text;
        messageDiv.appendChild(p);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function handleSend() {
        const text = userInput.value.trim();
        if (text) {
            addMessage(text, 'user');
            userInput.value = '';
            
            // Risposta automatica di Lorel (placeholder)
            setTimeout(() => {
                addMessage('Sto elaborando la tua richiesta di evoluzione...', 'ai');
            }, 1000);
        }
    }

    sendButton.addEventListener('click', handleSend);

    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            handleSend();
        }
    });
});