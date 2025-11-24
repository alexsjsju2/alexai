document.addEventListener('DOMContentLoaded', () => {
    const themeToggleButton = document.getElementById('theme-toggle-button');
    const sendButton = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');

    // 1. Gestione Tema
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', currentTheme);

    themeToggleButton.addEventListener('click', () => {
        let newTheme = document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // 2. Caricamento Cronologia Messaggi
    const loadMessages = () => {
        const messages = JSON.parse(localStorage.getItem('chatHistory')) || [];
        messages.forEach(msg => {
            addMessageToDOM(msg.sender, msg.text);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // 3. Salvataggio Messaggi
    const saveMessage = (sender, text) => {
        const messages = JSON.parse(localStorage.getItem('chatHistory')) || [];
        messages.push({ sender, text });
        localStorage.setItem('chatHistory', JSON.stringify(messages));
    };

    // 4. Aggiunta Messaggio al DOM
    const addMessageToDOM = (sender, text) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'lorel-message');
        messageElement.textContent = text;
        // Inserisce il messaggio prima dell'indicatore di digitazione
        chatMessages.insertBefore(messageElement, typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // 5. Logica di invio e risposta
    const handleSendMessage = () => {
        const messageText = userInput.value.trim();
        if (messageText === '') return;

        // Aggiungi e salva il messaggio dell'utente
        addMessageToDOM('user', messageText);
        saveMessage('user', messageText);
        userInput.value = '';

        // Mostra l'indicatore di digitazione
        typingIndicator.classList.add('visible');
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Simula la risposta di Lorel
        setTimeout(() => {
            // Nascondi l'indicatore
            typingIndicator.classList.remove('visible');

            // Crea e aggiungi la risposta di Lorel
            const lorelResponse = "Questa è una risposta simulata. La mia vera logica è nel backend.";
            addMessageToDOM('lorel', lorelResponse);
            saveMessage('lorel', lorelResponse);
        }, 1500 + Math.random() * 1000); // Ritardo realistico
    };

    // Event Listeners
    sendButton.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            handleSendMessage();
        }
    });

    // Caricamento iniziale
    loadMessages();
});