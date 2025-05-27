// filepath: c:\Users\ADMIN\Project-NLP\frontend\chatbot.js
// Biến toàn cục
let currentConversationId = null;
let conversations = [];
let messageCounter = 0; // Đảm bảo thứ tự tin nhắn
let pendingMessages = new Map(); // Theo dõi tin nhắn đang xử lý
let isProcessing = false; // Debouncing để tránh spam requests
let lastRequestTime = 0; // Tracking để rate limiting

// Khởi tạo chatbot khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Clear everything first
        clearChatBox();
        messageCounter = 0;
        pendingMessages.clear();
        currentConversationId = null;
        
        // Load conversations
        await loadConversations();
        
        // Show welcome message chỉ khi không có conversation nào active
        const currentConv = conversations.find(c => c.is_current);
        if (!currentConv) {
            showWelcomeMessage();
        } else {
            // Load messages của conversation hiện tại
            currentConversationId = currentConv.id;
            await loadConversationMessages(currentConv.id);
            updateAIModeIndicator(currentConv.ai_mode);
        }
        
        setupEventListeners();
    } catch (error) {
        console.error('Lỗi khởi tạo:', error);
        showMessage('Có lỗi khi khởi tạo ứng dụng.', 'error');
    }
}

function setupEventListeners() {
    console.log('[DEBUG] Setting up event listeners');
    const questionInput = document.getElementById('questionInput');
    if (!questionInput) {
        console.error('[ERROR] Question input element not found!');
        return;
    }
    
    // Remove any existing event listeners first (to avoid duplicates)
    const newInput = questionInput.cloneNode(true);
    questionInput.parentNode.replaceChild(newInput, questionInput);
    
    // Add event listener to the new input
    newInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            console.log('[DEBUG] Enter key pressed');
            e.preventDefault(); // Prevent default form submission
            sendQuestion();
        }
    });
    
    console.log('[DEBUG] Event listener for Enter key added');
}

function showWelcomeMessage() {
    // Welcome message đã có sẵn trong HTML
}

// ====== SESSION MANAGEMENT ======

function getOrCreateSessionId() {
    let sessionId = localStorage.getItem('chatbot_session_id');
    if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('chatbot_session_id', sessionId);
        console.log('[DEBUG] Created new session ID:', sessionId);
    } else {
        console.log('[DEBUG] Using existing session ID:', sessionId);
    }
    return sessionId;
}

// Gửi session ID với mỗi request
function fetchWithSession(url, options = {}) {
    const sessionId = getOrCreateSessionId();
    
    // Thêm session ID vào headers
    if (!options.headers) {
        options.headers = {};
    }
    options.headers['X-Session-ID'] = sessionId;
    
    // Đảm bảo credentials được gửi
    options.credentials = 'include';
    
    return fetch(url, options);
}

// ====== CONVERSATION MANAGEMENT ======

async function loadConversations() {
    try {
        console.log('[DEBUG] Loading conversations...');
        const response = await fetchWithSession('/conversations');
        const data = await response.json();
        
        console.log('[DEBUG] Conversations response:', data);
        
        if (response.ok) {
            conversations = data.conversations || [];
            console.log('[DEBUG] Total conversations loaded:', conversations.length);
            
            // Luôn render conversations (kể cả khi rỗng)
            renderConversations();
            
            // Tìm và set current conversation
            const currentConv = conversations.find(c => c.is_current);
            console.log('[DEBUG] Current conversation:', currentConv);
            
            if (currentConv) {
                // Chỉ set currentConversationId nếu chưa có hoặc khác
                if (currentConversationId !== currentConv.id) {
                    currentConversationId = currentConv.id;
                    updateAIModeIndicator(currentConv.ai_mode);
                    console.log('[DEBUG] Set current conversation ID:', currentConversationId);
                }
            } else {
                // Không có conversation nào active
                currentConversationId = null;
                updateAIModeIndicator(null);
                console.log('[DEBUG] No active conversation found');
            }
        } else {
            console.error('[DEBUG] Failed to load conversations:', data);
        }
    } catch (error) {
        console.error('Lỗi khi tải danh sách cuộc hội thoại:', error);
    }
}

function renderConversations() {
    console.log('[DEBUG] Rendering conversations, count:', conversations.length);
    const listElement = document.getElementById('conversationList');
    
    if (conversations.length === 0) {
        console.log('[DEBUG] No conversations to render');
        listElement.innerHTML = '<p style="text-align: center; color: #666; font-style: italic;">Chưa có cuộc hội thoại nào</p>';
        return;
    }
    
    console.log('[DEBUG] Rendering', conversations.length, 'conversations');
    listElement.innerHTML = conversations.map(conv => {
        const date = new Date(conv.updated_at).toLocaleDateString('vi-VN');
        const time = new Date(conv.updated_at).toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'});
        
        // Check if this is the current conversation
        const isActive = conv.is_current || conv.id === currentConversationId;
        
        return `
            <div class="conversation-item ${isActive ? 'active' : ''}" onclick="switchConversation('${conv.id}')">
                <div class="conversation-title">${conv.title}</div>
                <div class="conversation-meta">
                    ${conv.message_count} tin nhắn • ${date} ${time}
                    ${conv.ai_mode ? `• 🤖 ${getAIModeDisplay(conv.ai_mode)}` : ''}
                </div>
                <div class="conversation-actions">
                    <small>${isActive ? '• Đang active' : ''}</small>
                    <button class="delete-btn" onclick="deleteConversation('${conv.id}', event)">Xóa</button>
                </div>
            </div>
        `;
    }).join('');
}

async function updateConversationMetadata() {
    try {
        const response = await fetch('/conversations');
        const data = await response.json();
        
        if (response.ok) {
            // Chỉ cập nhật conversations array mà KHÔNG thay đổi currentConversationId
            // hoặc reload messages
            conversations = data.conversations;
            renderConversations();
        }
    } catch (error) {
        console.error('Lỗi khi cập nhật metadata cuộc hội thoại:', error);
    }
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
        console.log('[DEBUG] Creating new conversation...');
        
        const response = await fetchWithSession('/conversations/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('[DEBUG] New conversation created:', data.conversation);
            
            // Update current conversation ID
            currentConversationId = data.conversation.id;
            
            // Reset chat state
            clearChatBox();
            messageCounter = 0;
            pendingMessages.clear();
            
            // Update UI
            showWelcomeMessage();
            updateAIModeIndicator(data.conversation.ai_mode);
            
            // Reload conversations list để hiển thị conversation mới
            await loadConversations();
            
            // Update active UI ngay lập tức
            updateActiveConversationUI(currentConversationId);
            
            showMessage('✅ Đã tạo cuộc hội thoại mới!', 'success');
        } else {
            console.error('[DEBUG] Failed to create conversation:', data);
            showMessage('❌ Không thể tạo cuộc hội thoại mới: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Lỗi khi tạo cuộc hội thoại mới:', error);
        showMessage('❌ Có lỗi xảy ra khi tạo cuộc hội thoại mới', 'error');
    }
}

async function switchConversation(conversationId) {
    try {
        // Tránh multiple clicks
        if (currentConversationId === conversationId) {
            return;
        }
        
        console.log('[DEBUG] Switching to conversation:', conversationId);
          const response = await fetchWithSession(`/conversations/${conversationId}/switch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update current conversation ID NGAY LẬP TỨC
            currentConversationId = conversationId;
            
            // Update UI ngay để user thấy selection
            updateActiveConversationUI(conversationId);
            
            // Clear và load messages
            clearChatBox();
            await loadConversationMessages(conversationId);
            
            // Update AI mode
            updateAIModeIndicator(data.conversation.ai_mode);
            
            console.log('[DEBUG] Successfully switched to conversation:', conversationId);
            
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
        console.log('[DEBUG] Deleting conversation:', conversationId);
        
        // Immediately remove the conversation from UI for better UX
        const conversationElement = event.target.closest('.conversation-item');
        if (conversationElement) {
            // Thêm hiệu ứng mờ dần trước khi xóa
            conversationElement.style.opacity = '0.5';
            conversationElement.style.pointerEvents = 'none'; // Prevent clicks during deletion
        }
        
        // Send delete request to API
        const response = await fetchWithSession(`/conversations/${conversationId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('[DEBUG] Conversation deleted successfully');
            
            // Remove from local array immediately
            conversations = conversations.filter(conv => conv.id !== conversationId);
            
            // If the deleted conversation was the current one, reset UI
            if (conversationId === currentConversationId) {
                clearChatBox();
                showWelcomeMessage();
                currentConversationId = null;
                updateAIModeIndicator(null);
            }
            
            // Remove element from DOM completely if it still exists
            if (conversationElement && conversationElement.parentNode) {
                conversationElement.parentNode.removeChild(conversationElement);
            }
            
            // Reload conversations from API to ensure sync
            await loadConversations();
            
            showMessage('✅ Đã xóa cuộc hội thoại!', 'success');
        } else {
            // Restore UI if deletion failed
            if (conversationElement) {
                conversationElement.style.opacity = '1';
                conversationElement.style.pointerEvents = 'auto';
            }
            
            showMessage('❌ Không thể xóa cuộc hội thoại: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Lỗi khi xóa cuộc hội thoại:', error);
        showMessage('❌ Có lỗi xảy ra khi xóa cuộc hội thoại', 'error');
    }
}

async function loadConversationMessages(conversationId) {
    try {
        const response = await fetchWithSession(`/conversations/${conversationId}`);
        const data = await response.json();
        
        if (response.ok) {
            const conversation = data.conversation;
            
            // QUAN TRỌNG: Clear chatbox hoàn toàn trước khi load
            clearChatBox();
            
            // Reset message counter và pending messages
            messageCounter = 0;
            pendingMessages.clear();
            
            // Render messages theo đúng thứ tự
            conversation.messages.forEach((message, index) => {
                const userMsgId = `user-loaded-${conversationId}-${index}`;
                const botMsgId = `bot-loaded-${conversationId}-${index}`;
                
                addMessage(message.question, 'user', false, userMsgId);
                addMessage(message.answer, 'bot', false, botMsgId);
            });
            
            // Set counter for new messages (tránh conflict với loaded messages)
            messageCounter = conversation.messages.length * 2 + 1000;
            
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
    
    // Clear hoàn toàn innerHTML
    chatBox.innerHTML = '';
    
    // Reset các state variables
    messageCounter = 0;
    pendingMessages.clear();
    
    // Force DOM to re-render
    chatBox.offsetHeight;
}

// ====== CHAT FUNCTIONS ======

async function sendQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    
    if (!question) {
        showMessage('Vui lòng nhập câu hỏi!', 'error');
        return;
    }
    
    // Debouncing - tránh spam requests
    if (isProcessing) {
        showMessage('Vui lòng đợi câu trả lời trước khi gửi câu hỏi mới!', 'warning');
        return;
    }
    
    // Rate limiting - tối thiểu 1 giây giữa các requests
    const currentTime = Date.now();
    if (currentTime - lastRequestTime < 1000) {
        showMessage('Vui lòng đợi ít nhất 1 giây giữa các câu hỏi!', 'warning');
        return;
    }
    
    isProcessing = true;
    lastRequestTime = currentTime;
    
    // Tạo unique message ID để đảm bảo thứ tự
    const messageId = ++messageCounter;
    const userMessageId = `user-${messageId}`;
    const botMessageId = `bot-${messageId}`;
    
    // Disable input while processing
    input.disabled = true;
    
    // Add user message với ID cố định
    addMessage(question, 'user', false, userMessageId);
    
    // Show typing indicator với ID cố định
    addMessage('🤖 Đang trả lời...', 'bot', true, botMessageId);
    
    // Clear input
    input.value = '';
    
    // Đánh dấu tin nhắn đang xử lý
    pendingMessages.set(messageId, { question, userMessageId, botMessageId });
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        // Kiểm tra xem tin nhắn này có còn pending không (tránh race condition)
        if (!pendingMessages.has(messageId)) {
            console.warn(`Message ${messageId} was already processed`);
            return;
        }
        
        // Remove từ pending
        pendingMessages.delete(messageId);
        
        if (response.ok) {
            // Replace typing indicator với response thực tế
            replaceMessage(botMessageId, data.answer, 'bot');
              // Update suggestions
            updateSuggestions(data.suggestions || []);
            
            // Update AI mode indicator
            if (data.ai_mode) {
                updateAIModeIndicator(data.ai_mode);
            }
            
            // Chỉ cập nhật conversation list mà KHÔNG reload messages
            // để cập nhật metadata như message count
            setTimeout(() => {
                updateConversationMetadata();
            }, 500);
            
        } else {
            replaceMessage(botMessageId, '❌ Lỗi: ' + data.error, 'bot');
        }
        
    } catch (error) {
        console.error('Lỗi khi gửi câu hỏi:', error);
        
        // Kiểm tra xem tin nhắn có còn pending không
        if (pendingMessages.has(messageId)) {
            pendingMessages.delete(messageId);
            replaceMessage(botMessageId, '❌ Có lỗi xảy ra khi gửi câu hỏi. Vui lòng thử lại.', 'bot');
        }
    } finally {
        // Re-enable input and reset processing state
        input.disabled = false;
        input.focus();
        isProcessing = false;
    }
}

function addMessage(message, sender, isTyping = false, customId = null) {
    const chatBox = document.getElementById('chatBox');
    const messageId = customId || `${sender}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Process HTML content nếu là bot message
    const processedMessage = sender === 'bot' ? processHTMLContent(message) : message;
    
    const bubble = document.createElement('div');
    bubble.className = `bubble ${sender} ${isTyping ? 'typing' : ''}`;
    bubble.id = messageId;
    
    const senderIcon = sender === 'user' ? '👤' : '🤖';
    const senderName = sender === 'user' ? 'Bạn' : 'Copailit';
    
    bubble.innerHTML = `<strong class="${sender}">${senderIcon} ${senderName}:</strong><br>${processedMessage}`;
    
    // Smooth animation
    bubble.style.opacity = '0';
    bubble.style.transform = 'translateY(20px)';
    
    chatBox.appendChild(bubble);
    
    // Trigger animation
    setTimeout(() => {
        bubble.style.opacity = '1';
        bubble.style.transform = 'translateY(0)';
    }, 50);
    
    // Auto scroll
    chatBox.scrollTop = chatBox.scrollHeight;
    
    return messageId;
}

function replaceMessage(messageId, newContent, sender) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        // Process HTML content nếu là bot message
        const processedContent = sender === 'bot' ? processHTMLContent(newContent) : newContent;
        
        const senderIcon = sender === 'user' ? '👤' : '🤖';
        const senderName = sender === 'user' ? 'Bạn' : 'Copailit';
        
        messageElement.className = `bubble ${sender}`; // Remove typing class
        messageElement.innerHTML = `<strong class="${sender}">${senderIcon} ${senderName}:</strong><br>${processedContent}`;
        
        // Scroll to bottom
        const chatBox = document.getElementById('chatBox');
        chatBox.scrollTop = chatBox.scrollHeight;
    }
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

// Cập nhật UI cho conversation active
function updateActiveConversationUI(activeId) {
    console.log('[DEBUG] Updating active conversation UI:', activeId);
    const items = document.querySelectorAll('.conversation-item');
    
    items.forEach(item => {
        if (item.getAttribute('onclick').includes(activeId)) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// ====== DEBUG FUNCTIONS ======

async function exportChatHistory() {
    try {
        console.log('[DEBUG] Starting export chat history...');
        showMessage('📥 Đang xuất lịch sử chat...', 'info');
        
        const response = await fetch('/export-chat');
        console.log('[DEBUG] Export response status:', response.status);
          if (response.ok) {
            console.log('[DEBUG] Export successful, creating download...');
            // Tạo file download HTML
            const blob = await response.blob();
            console.log('[DEBUG] Blob created, size:', blob.size);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `chat_export_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.html`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showMessage('✅ Đã tải xuống lịch sử chat thành công (định dạng HTML)!', 'success');
        } else {
            console.log('[DEBUG] Export failed with status:', response.status);
            const errorData = await response.json();
            console.log('[DEBUG] Error data:', errorData);
            showMessage('❌ Không thể export chat: ' + (errorData.error || 'Lỗi không xác định'), 'error');
        }
    } catch (error) {
        console.error('[DEBUG] Error exporting chat:', error);
        showMessage('❌ Có lỗi xảy ra khi export chat', 'error');
    }
}

// ====== HELPER FUNCTIONS ======

function askQuestion(question) {
    // Automatically fill input and send a question - used by suggestion buttons
    const input = document.getElementById('questionInput');
    input.value = question;
    sendQuestion();
}

// ====== HTML CONTENT PROCESSING ======

function processHTMLContent(htmlContent) {
    // Post-process HTML content để đảm bảo format đúng
    let processed = htmlContent;
    
    // Fix common markdown leakage
    processed = processed.replace(/```(\w+)?\n?([\s\S]*?)```/g, function(match, lang, code) {
        const language = lang || 'text';
        const escapedCode = escapeHtml(code.trim());
        return `<div class="code-block">
            <div class="code-header">${language}</div>
            <div class="code-content">${escapedCode}</div>
        </div>`;
    });
    
    // Fix inline code với backticks
    processed = processed.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Đảm bảo HTML entities được escape đúng trong code blocks
    processed = processed.replace(/<div class="code-content">([\s\S]*?)<\/div>/g, function(match, content) {
        const safeContent = content
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
        return `<div class="code-content">${safeContent}</div>`;
    });
    
    // Fix line breaks in formulas
    processed = processed.replace(/<div class="formula-block">([\s\S]*?)<\/div>/g, function(match, content) {
        const formattedContent = content.replace(/\n/g, '<br>');
        return `<div class="formula-block">${formattedContent}</div>`;
    });
    
    return processed;
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
