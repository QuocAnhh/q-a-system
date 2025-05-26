// filepath: c:\Users\ADMIN\Project-NLP\frontend\chatbot.js
// Biến toàn cục
let currentConversationId = null;
let conversations = [];

// Khởi tạo chatbot khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        await loadConversations();
        showWelcomeMessage();
        setupEventListeners();
    } catch (error) {
        console.error('Lỗi khởi tạo:', error);
        showMessage('Có lỗi khi khởi tạo ứng dụng.', 'error');
    }
}

function setupEventListeners() {
    const questionInput = document.getElementById('questionInput');
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendQuestion();
        }
    });
}

function showWelcomeMessage() {
    // Welcome message đã có sẵn trong HTML
}

// ====== CONVERSATION MANAGEMENT ======

async function loadConversations() {
    try {
        const response = await fetch('/conversations');
        const data = await response.json();
        
        if (response.ok) {
            conversations = data.conversations;
            renderConversations();
            
            // Nếu có cuộc hội thoại đang active, load nó
            const currentConv = conversations.find(c => c.is_current);
            if (currentConv) {
                currentConversationId = currentConv.id;
                await loadConversationMessages(currentConv.id);
                updateAIModeIndicator(currentConv.ai_mode);
            }
        }
    } catch (error) {
        console.error('Lỗi khi tải danh sách cuộc hội thoại:', error);
    }
}

function renderConversations() {
    const listElement = document.getElementById('conversationList');
    
    if (conversations.length === 0) {
        listElement.innerHTML = '<p style="text-align: center; color: #666; font-style: italic;">Chưa có cuộc hội thoại nào</p>';
        return;
    }
    
    listElement.innerHTML = conversations.map(conv => {
        const date = new Date(conv.updated_at).toLocaleDateString('vi-VN');
        const time = new Date(conv.updated_at).toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'});
        
        return `
            <div class="conversation-item ${conv.is_current ? 'active' : ''}" onclick="switchConversation('${conv.id}')">
                <div class="conversation-title">${conv.title}</div>
                <div class="conversation-meta">
                    ${conv.message_count} tin nhắn • ${date} ${time}
                    ${conv.ai_mode ? `• 🤖 ${getAIModeDisplay(conv.ai_mode)}` : ''}
                </div>
                <div class="conversation-actions">
                    <small>${conv.is_current ? '• Đang active' : ''}</small>
                    <button class="delete-btn" onclick="deleteConversation('${conv.id}', event)">Xóa</button>
                </div>
            </div>
        `;
    }).join('');
}

function getAIModeDisplay(mode) {
    const modes = {
        'math': 'Toán học',
        'physics': 'Vật lý', 
        'programming': 'Lập trình',
        'chemistry': 'Hóa học',
        'history': 'Lịch sử',
        'english': 'Tiếng Anh',
        'study': 'Học tập',
        'general': 'Chung'
    };
    return modes[mode] || mode;
}

async function createNewConversation() {
    try {
        const response = await fetch('/conversations/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Clear chat box
            clearChatBox();
            
            // Update current conversation
            currentConversationId = data.conversation.id;
            
            // Reload conversations list
            await loadConversations();
            
            // Show welcome message
            showWelcomeMessage();
            
            // Clear AI mode
            updateAIModeIndicator(null);
            
            showMessage('✅ Đã tạo cuộc hội thoại mới!', 'success');
        } else {
            showMessage('❌ Không thể tạo cuộc hội thoại mới: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Lỗi khi tạo cuộc hội thoại mới:', error);
        showMessage('❌ Có lỗi xảy ra khi tạo cuộc hội thoại mới', 'error');
    }
}

async function switchConversation(conversationId) {
    try {
        const response = await fetch(`/conversations/${conversationId}/switch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentConversationId = conversationId;
            
            // Clear chat box and load messages
            clearChatBox();
            await loadConversationMessages(conversationId);
            
            // Update conversations list
            await loadConversations();
            
            // Update AI mode
            updateAIModeIndicator(data.conversation.ai_mode);
            
        } else {
            showMessage('❌ Không thể chuyển cuộc hội thoại: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Lỗi khi chuyển cuộc hội thoại:', error);
        showMessage('❌ Có lỗi xảy ra khi chuyển cuộc hội thoại', 'error');
    }
}

async function deleteConversation(conversationId, event) {
    event.stopPropagation(); // Prevent triggering switch conversation
    
    if (!confirm('Bạn có chắc chắn muốn xóa cuộc hội thoại này?')) {
        return;
    }
    
    try {
        const response = await fetch(`/conversations/${conversationId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // If deleting current conversation, clear chat box
            if (conversationId === currentConversationId) {
                clearChatBox();
                showWelcomeMessage();
                currentConversationId = null;
                updateAIModeIndicator(null);
            }
            
            // Reload conversations
            await loadConversations();
            
            showMessage('✅ Đã xóa cuộc hội thoại!', 'success');
        } else {
            showMessage('❌ Không thể xóa cuộc hội thoại: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Lỗi khi xóa cuộc hội thoại:', error);
        showMessage('❌ Có lỗi xảy ra khi xóa cuộc hội thoại', 'error');
    }
}

async function loadConversationMessages(conversationId) {
    try {
        const response = await fetch(`/conversations/${conversationId}`);
        const data = await response.json();
        
        if (response.ok) {
            const conversation = data.conversation;
            
            // Render messages
            conversation.messages.forEach(message => {
                addMessage(message.question, 'user');
                addMessage(message.answer, 'bot');
            });
            
            // Update AI mode
            updateAIModeIndicator(conversation.ai_mode);
            
        } else {
            showMessage('❌ Không thể tải tin nhắn: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Lỗi khi tải tin nhắn:', error);
        showMessage('❌ Có lỗi xảy ra khi tải tin nhắn', 'error');
    }
}

function clearChatBox() {
    const chatBox = document.getElementById('chatBox');
    chatBox.innerHTML = '';
}

// ====== CHAT FUNCTIONS ======

async function sendQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    
    if (!question) {
        showMessage('Vui lòng nhập câu hỏi!', 'error');
        return;
    }
    
    // Disable input while processing
    input.disabled = true;
    
    // Add user message
    addMessage(question, 'user');
    
    // Show typing indicator
    const typingId = addMessage('Đang trả lời...', 'bot', true);
    
    // Clear input
    input.value = '';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeMessage(typingId);
        
        if (response.ok) {
            // Add bot response
            addMessage(data.answer, 'bot');
            
            // Update suggestions
            updateSuggestions(data.suggestions || []);
            
            // Update AI mode indicator
            if (data.ai_mode) {
                updateAIModeIndicator(data.ai_mode);
            }
            
            // Reload conversations to update the list
            await loadConversations();
            
        } else {
            addMessage('❌ Lỗi: ' + data.error, 'bot');
        }
        
    } catch (error) {
        console.error('Lỗi khi gửi câu hỏi:', error);
        removeMessage(typingId);
        addMessage('❌ Có lỗi xảy ra khi gửi câu hỏi. Vui lòng thử lại.', 'bot');
    } finally {
        // Re-enable input
        input.disabled = false;
        input.focus();
    }
}

function addMessage(message, sender, isTyping = false) {
    const chatBox = document.getElementById('chatBox');
    const messageId = 'msg-' + Date.now() + '-' + Math.random();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `bubble ${sender} ${isTyping ? 'typing' : ''}`;
    messageDiv.id = messageId;
    
    const senderLabel = sender === 'user' ? '😺  Bạn' : '🤖 Copailit';
    
    if (isTyping) {
        messageDiv.innerHTML = `<strong class="${sender}">${senderLabel}:</strong><br>${message}`;
    } else {
        messageDiv.innerHTML = `<strong class="${sender}">${senderLabel}:</strong><br>${message}`;
    }
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    return messageId;
}

function removeMessage(messageId) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.remove();
    }
}

function updateSuggestions(suggestions) {
    const suggestionsContainer = document.getElementById('suggestions');
    
    if (suggestions.length === 0) {
        suggestionsContainer.innerHTML = '';
        return;
    }
    
    suggestionsContainer.innerHTML = suggestions.map(suggestion => 
        `<div class="suggestion" onclick="askQuestion('${suggestion.replace(/'/g, "\\'")}')">💡 ${suggestion}</div>`
    ).join('');
}

function updateAIModeIndicator(mode) {
    const indicator = document.getElementById('aiModeIndicator');
    const modeSpan = document.getElementById('currentMode');
    
    if (mode) {
        modeSpan.textContent = getAIModeDisplay(mode);
        indicator.style.display = 'block';
    } else {
        indicator.style.display = 'none';
    }
}

// ====== UTILITY FUNCTIONS ======

function askQuestion(question) {
    const input = document.getElementById('questionInput');
    input.value = question;
    sendQuestion();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendQuestion();
    }
}

function showMessage(message, type = 'info') {
    // Create a temporary message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type}`;
    messageDiv.style.cssText = `
        position: fixed; 
        top: 20px; 
        right: 20px; 
        padding: 15px 20px; 
        border-radius: 8px; 
        z-index: 1000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    // Set colors based on type
    switch(type) {
        case 'success':
            messageDiv.style.background = '#d4edda';
            messageDiv.style.color = '#155724';
            messageDiv.style.border = '1px solid #c3e6cb';
            break;
        case 'error':
            messageDiv.style.background = '#f8d7da';
            messageDiv.style.color = '#721c24';
            messageDiv.style.border = '1px solid #f5c6cb';
            break;
        default:
            messageDiv.style.background = '#d1ecf1';
            messageDiv.style.color = '#0c5460';
            messageDiv.style.border = '1px solid #bee5eb';
    }
    
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 300);
        }
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
