// 工具函数
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// UI 组件
const UI = {
    chatBox: document.getElementById('chatBox'),
    userInput: document.getElementById('userInput'),
    sendButton: document.getElementById('sendButton'),
    statusMessage: document.getElementById('statusMessage'),
    typingIndicator: document.getElementById('typingIndicator'),

    setLoading(isLoading) {
        this.sendButton.disabled = isLoading;
        this.userInput.disabled = isLoading;
        this.sendButton.querySelector('.button-text').classList.toggle('hidden', isLoading);
        this.sendButton.querySelector('.button-loading').classList.toggle('hidden', !isLoading);
    },

    showTyping(show) {
        this.typingIndicator.classList.toggle('hidden', !show);
    },

    showStatus(message, isError = false) {
        this.statusMessage.textContent = message;
        this.statusMessage.className = isError ? 'error' : '';
        setTimeout(() => {
            this.statusMessage.textContent = '';
            this.statusMessage.className = '';
        }, 3000);
    }
};

// 消息处理
function appendMessage(message, isUser, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'} ${isError ? 'error-message' : ''}`;
    messageDiv.innerHTML = message.replace(/\n/g, '<br>');
    UI.chatBox.appendChild(messageDiv);
    UI.chatBox.scrollTop = UI.chatBox.scrollHeight;
    return messageDiv;
}

// 发送消息
async function sendMessage() {
    const message = UI.userInput.value.trim();
    if (!message) return;

    UI.setLoading(true);
    UI.userInput.value = '';
    appendMessage(message, true);

    try {
        const response = await fetch('/get_response/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'message=' + encodeURIComponent(message)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '服务器错误');
        }

        if (data.response) {
            appendMessage(data.response, false);
        } else if (data.error) {
            appendMessage('错误：' + data.error, false, true);
        }
    } catch (error) {
        appendMessage('系统错误：' + error.message, false, true);
        console.error('Error:', error);
    } finally {
        UI.setLoading(false);
        UI.userInput.focus();
    }
}

// 自动调整文本框高度
const adjustTextareaHeight = debounce(() => {
    UI.userInput.style.height = 'auto';
    UI.userInput.style.height = (UI.userInput.scrollHeight) + 'px';
}, 100);

// 事件监听器
document.addEventListener('DOMContentLoaded', () => {
    // 文本框事件
    UI.userInput.addEventListener('input', adjustTextareaHeight);
    UI.userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 发送按钮事件
    UI.sendButton.addEventListener('click', sendMessage);

    // 初始化
    UI.userInput.focus();
});
