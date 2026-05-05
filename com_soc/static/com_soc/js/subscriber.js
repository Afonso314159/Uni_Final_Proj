/* ==========================================
   Subscriber Page JavaScript
   ========================================== */

document.addEventListener('DOMContentLoaded', function () {
    const chatFab = document.getElementById('chat-fab');
    const chatModal = document.getElementById('chat-modal');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const chatOnlineCount = document.getElementById('chat-online-count');

    if (!chatFab || !chatModal) return;

    const username = chatModal.dataset.username;
    let socket = null;

    // Open chat
    chatFab.addEventListener('click', () => {
        openModal(chatModal);
        if (!socket || socket.readyState === WebSocket.CLOSED) {
            chatMessages.innerHTML = '';
            connectWebSocket();
        }
        chatInput.focus();
    });

    // Close chat — disconnect WebSocket
    chatModal.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(chatModal);
            if (socket) socket.close();
        });
    });

    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/`);

        socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'message') {
                appendMessage(data.username, data.message, data.username === username, data.timestamp);
            } else if (data.type === 'online_count') {
                chatOnlineCount.textContent = `${data.count} online`;
            }
        };

        socket.onclose = () => {
            if (chatOnlineCount) chatOnlineCount.textContent = '';
        };
    }

    function sendMessage() {
        const msg = chatInput.value.trim();
        if (!msg || !socket || socket.readyState !== WebSocket.OPEN) return;
        socket.send(JSON.stringify({ message: msg }));
        chatInput.value = '';
    }

    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    function appendMessage(user, text, isMine, timestamp) {
        const wrap = document.createElement('div');
        wrap.className = `chat-msg ${isMine ? 'chat-msg--mine' : 'chat-msg--theirs'}`;

        if (!isMine) {
            const name = document.createElement('span');
            name.className = 'chat-msg-user';
            name.textContent = user;
            wrap.appendChild(name);
        }

        const bubble = document.createElement('div');
        bubble.className = 'chat-msg-bubble';
        bubble.textContent = text;
        wrap.appendChild(bubble);

        if (timestamp) {
            const time = document.createElement('span');
            time.className = 'chat-msg-time';
            time.textContent = timestamp;
            wrap.appendChild(time);
        }

        chatMessages.appendChild(wrap);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});