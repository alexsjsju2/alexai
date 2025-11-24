document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const themeToggleButton = document.getElementById('theme-toggle-button');

    // --- Funzioni Chat ---

    // Carica la cronologia della chat dal localStorage
    const loadChatHistory = () => {
        const history = JSON.parse(localStorage.getItem('chatHistory')) || [];
        history.forEach(msg => addMessage(msg.sender, msg.text));
    };

    // Salva un nuovo messaggio nel localStorage
    const saveMessage = (sender, text) => {
        const history = JSON.parse(localStorage.getItem('chatHistory')) || [];
        history.push({ sender, text });
        localStorage.setItem('chatHistory', JSON.stringify(history));
    };

    // Aggiunge un messaggio all'interfaccia
    const addMessage = (sender, text) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        if (sender === 'user') {
            messageElement.classList.add('user');
        }
        messageElement.textContent = text;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scrolla fino in fondo
    };

    // Gestisce l'invio di un messaggio
    const handleSendMessage = () => {
        const text = userInput.value.trim();
        if (text) {
            addMessage('user', text);
            saveMessage('user', text);
            userInput.value = '';
            // Qui andrebbe la logica per la risposta dell'IA
            setTimeout(() => {
                const aiResponse = "Questa è una risposta automatica.";
                addMessage('ai', aiResponse);
                saveMessage('ai', aiResponse);
            }, 1000);
        }
    };

    // --- Funzioni Tema ---
    
    // Applica il tema salvato
    const applySavedTheme = () => {
        const savedTheme = localStorage.getItem('theme') || 'light';
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-mode');
        }
    };

    // Cambia il tema e lo salva
    const toggleTheme = () => {
        document.body.classList.toggle('dark-mode');
        const currentTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
        localStorage.setItem('theme', currentTheme);
    };

    // --- Event Listeners ---
    sendButton.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });
    themeToggleButton.addEventListener('click', toggleTheme);

    // --- Inizializzazione ---
    loadChatHistory();
    applySavedTheme();
});