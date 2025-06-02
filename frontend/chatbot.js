// filepath: c:\Users\ADMIN\Project-NLP\frontend\chatbot.js
// Biến toàn cục
let currentConversationId = null;
let conversations = [];
let messageCounter = 0; // Đảm bảo thứ tự tin nhắn
let pendingMessages = new Map(); // Theo dõi tin nhắn đang xử lý
let isProcessing = false; // Debouncing để tránh spam requests
let lastRequestTime = 0; // Tracking để rate limiting

// ====== INITIALIZATION & EVENT LISTENERS ======
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] Document loaded, initializing app...');
    
    // Xử lý lỗi toàn cục để ghi nhật ký
    window.onerror = function(message, source, lineno, colno, error) {
        console.error('[GLOBAL ERROR]', message, 'at', source, lineno, colno, error);
        showMessage('❌ Lỗi JavaScript: ' + message, 'error');
        return false;
    };
      // Khởi tạo ứng dụng
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    try {
        console.log('[DEBUG] Initializing app...');
        
        // Check for OAuth callback first
        handleOAuthCallback();
        
        // Reset trạng thái
        clearChatBox();
        messageCounter = 0;
        pendingMessages.clear();
        currentConversationId = null;
        
        // Luôn load danh sách và lịch sử chat của conv active (nếu có)
        await loadConversationsAndShowActive();
        
        // Check calendar status
        await checkCalendarStatus();
        
        console.log('[DEBUG] App initialized successfully');
    } catch (error) {
        console.error('[ERROR] Initialization error:', error);
        showMessage('❌ Có lỗi khi khởi tạo ứng dụng: ' + error.message, 'error');
    }
}

// Load and show a conversation (including messages)
async function loadAndShowConversation(conversationId) {
    try {
        const response = await fetch(`/conversations/${conversationId}`, { credentials: 'same-origin' });
        const data = await response.json();
        if (response.ok) {
            const conversation = data.conversation;
            currentConversationId = conversation.id;
            updateAIModeIndicator(conversation.ai_mode);
            clearChatBox();
            messageCounter = 0;
            pendingMessages.clear();
            (conversation.messages || []).forEach((message, index) => {
                const userMsgId = `user-loaded-${conversationId}-${index}`;
                const botMsgId = `bot-loaded-${conversationId}-${index}`;
                addMessage(message.question, 'user', false, userMsgId);
                addMessage(message.answer, 'bot', false, botMsgId);
            });
            messageCounter = (conversation.messages || []).length * 2 + 1000;
        } else {
            clearChatBox();
            showWelcomeMessage();
        }
    } catch (error) {
        clearChatBox();
        showWelcomeMessage();
    }
}

// Always load conversations and show the active one
async function loadConversationsAndShowActive() {
    try {
        console.log('[DEBUG] Loading conversations and showing active...');
        const response = await fetch('/conversations', { 
            credentials: 'same-origin',
            cache: 'no-cache' // Đảm bảo không cache kết quả
        });
        
        if (!response.ok) {
            console.error('[ERROR] Failed to load conversations:', response.status);
            clearChatBox();
            showWelcomeMessage();
            return;
        }
        
        const data = await response.json();
        console.log('[DEBUG] Received conversations data:', data);
        
        conversations = data.conversations || [];
        renderConversations();
        
        if (conversations.length === 0) {
            console.log('[DEBUG] No conversations found, clearing chatbox');
            clearChatBox();
            showWelcomeMessage();
            return;
        }        // Tìm hội thoại đang active - ưu tiên is_current, nếu không có thì lấy conversation đầu tiên
        const currentConv = conversations.find(c => c.is_current || c.is_active) || conversations[0];
        if (currentConv) {
            console.log('[DEBUG] Found active conversation:', currentConv.id);
            // Đồng bộ currentConversationId với conversation active từ server
            currentConversationId = currentConv.id;
            await loadAndShowConversation(currentConv.id);
        } else {
            console.log('[DEBUG] No active conversation found');
            currentConversationId = null;
            clearChatBox();
            showWelcomeMessage();
        }
    } catch (error) {
        console.error('[ERROR] Error in loadConversationsAndShowActive:', error);
        clearChatBox();
        showWelcomeMessage();
    }
}

function renderConversations() {
    console.log('[DEBUG] Rendering conversations:', conversations.length);
    const listElement = document.getElementById('conversationList');
    
    if (!listElement) {
        console.error('[ERROR] Conversation list element not found');
        return;
    }
    
    if (conversations.length === 0) {
        listElement.innerHTML = '<p style="text-align: center; color: #666; font-style: italic;">Chưa có cuộc hội thoại nào</p>';
        // Disable export button if no conversation
        const exportBtn = document.getElementById('exportButton');
        if (exportBtn) exportBtn.disabled = true;
        return;
    }
    
    // Enable export button if conversations exist
    const exportBtn = document.getElementById('exportButton');
    if (exportBtn) exportBtn.disabled = false;
      // Render conversation items
    listElement.innerHTML = conversations.map(conv => {
        const date = new Date(conv.updated_at).toLocaleDateString('vi-VN');
        const time = new Date(conv.updated_at).toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'});
        // Logic xác định active: ưu tiên currentConversationId, sau đó is_current từ server
        const isActive = (currentConversationId && conv.id === currentConversationId) || 
                         (!currentConversationId && (conv.is_current || conv.is_active));
        return `
            <div class="conversation-item ${isActive ? 'active' : ''}" data-convid="${conv.id}">
                <div class="conversation-title">${conv.title}</div>
                <div class="conversation-meta">
                    ${conv.message_count} tin nhắn • ${date} ${time}
                    ${conv.ai_mode ? `• 🤖 ${getAIModeDisplay(conv.ai_mode)}` : ''}
                </div>
                <div class="conversation-actions">
                    <small>${isActive ? '• Đang active' : ''}</small>
                    <button class="delete-btn" data-deleteid="${conv.id}">Xóa</button>
                </div>
            </div>
        `;
    }).join('');
    
    // Attach event listeners to conversation items and delete buttons
    attachConversationEventListeners();
}

// Đảm bảo chỉ gắn event listener cho input và nút gửi một lần duy nhất
function setupEventListeners() {
    console.log('[DEBUG] Setting up event listeners');
    
    // Input field và nút gửi
    const questionInput = document.getElementById('questionInput');
    if (questionInput) {
        questionInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey && !questionInput.disabled) {
                e.preventDefault();
                sendQuestion();
            }
        });
    } else {
        console.error('[ERROR] Question input element not found');
    }
    
    const sendBtn = document.querySelector('.send-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendQuestion);
    } else {
        console.error('[ERROR] Send button not found');
    }
    
    // Nút tạo cuộc hội thoại mới
    const newChatBtn = document.getElementById('newChatButton');
    if (newChatBtn) {
        console.log('[DEBUG] Attaching event listener to newChatButton');
        newChatBtn.addEventListener('click', function() {
            console.log('[DEBUG] New chat button clicked');
            createNewConversation();
        });
    } else {
        console.error('[ERROR] New chat button not found');
    }
      // Nút export chat
    const exportBtn = document.getElementById('exportButton');
    if (exportBtn) {
        console.log('[DEBUG] Attaching event listener to exportButton');
        exportBtn.addEventListener('click', function() {
            console.log('[DEBUG] Export button clicked');
            exportChatHistory();
        });
    } else {
        console.error('[ERROR] Export button not found');
    }
    
    // Calendar authentication button
    const calendarAuthBtn = document.getElementById('calendarAuthBtn');
    if (calendarAuthBtn) {
        console.log('[DEBUG] Attaching event listener to calendarAuthBtn');
        calendarAuthBtn.addEventListener('click', function() {
            console.log('[DEBUG] Calendar auth button clicked');
            authenticateCalendar();
        });
    } else {
        console.error('[ERROR] Calendar auth button not found');
    }
}

// Attach event listeners to conversation items
function attachConversationEventListeners() {
    console.log('[DEBUG] Attaching event listeners to conversation items');
    // Đính kèm event listeners cho các mục hội thoại
    document.querySelectorAll('.conversation-item').forEach(item => {
        const convId = item.getAttribute('data-convid');
        
        // Add click event listener for switching conversations
        item.addEventListener('click', (e) => {
            // Avoid triggering switch when clicking delete button
            if (e.target.classList.contains('delete-btn')) return;
            console.log('[DEBUG] Conversation item clicked:', convId);
            switchConversation(convId);
        });
        
        // Add click event listener for delete buttons
        const delBtn = item.querySelector('.delete-btn');
        if (delBtn) {
            delBtn.addEventListener('click', (e) => {
                console.log('[DEBUG] Delete button clicked for:', convId);
                deleteConversation(convId, e);
            });
        }
    });
}

function showWelcomeMessage() {
    // Tạo tin nhắn chào mừng trong chatbox nếu chưa có
    const chatBox = document.getElementById('chatBox');
    if (!chatBox) return;
    
    // Nếu chatbox đã trống, thêm tin nhắn chào mừng
    if (chatBox.children.length === 0) {
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'bubble bot';
        welcomeMessage.innerHTML = `
            <strong class="bot">🤖 Copailit:</strong><br>
            Xin chào! Tôi là Copailit AI. Tôi có thể giúp bạn!
        `;
        chatBox.appendChild(welcomeMessage);
    }
}

// ====== CONVERSATION MANAGEMENT ======

async function loadConversations(loadMessages = false) {
    try {
        console.log('[DEBUG] Loading conversations...');
        const response = await fetch('/conversations', { credentials: 'same-origin' });
        const data = await response.json();
        console.log('[DEBUG] Conversations response:', data);        if (response.ok) {
            conversations = data.conversations || [];
            
            if (conversations.length === 0) {
                console.log('[DEBUG] No conversations found');
                currentConversationId = null;
                renderConversations();
                clearChatBox();
                showWelcomeMessage();
                return;
            }            // Luôn tìm conv đang active - ưu tiên is_current, nếu không có thì is_active
            const currentConv = conversations.find(c => c.is_current || c.is_active);
            if (currentConv) {
                currentConversationId = currentConv.id;
                console.log('[DEBUG] Synced currentConversationId:', currentConversationId);
                updateAIModeIndicator(currentConv.ai_mode);
                if (loadMessages) {
                    await loadAndShowConversation(currentConv.id);
                }
            } else {
                currentConversationId = null;
                clearChatBox();
                showWelcomeMessage();
            }
            
            // Re-render conversations với currentConversationId đã được sync
            renderConversations();
        } else {
            console.error('[ERROR] Failed to load conversations:', data);
            showMessage('❌ Không thể tải danh sách cuộc hội thoại: ' + (data.error || 'Lỗi không xác định'), 'error');
        }
    } catch (error) {
        console.error('Lỗi khi tải danh sách cuộc hội thoại:', error);
        showMessage('❌ Có lỗi xảy ra khi tải danh sách cuộc hội thoại', 'error');
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
        showMessage('🔄 Đang tạo cuộc hội thoại mới...', 'info');
        
        const response = await fetch('/conversations/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('[ERROR] Failed to create new conversation:', errorData);
            showMessage('❌ Không thể tạo cuộc hội thoại mới: ' + (errorData.error || 'Lỗi không xác định'), 'error');
            return;
        }
        
        const data = await response.json();
        console.log('[DEBUG] New conversation created:', data);
        
        // Explicitly clear chatbox
        clearChatBox();
          // Update conversation list and show active one
        conversations = data.conversations || [];
        
        // Find the newly created conversation (should be active)
        const newConv = data.conversation;
        if (newConv) {
            currentConversationId = newConv.id;
            console.log('[DEBUG] Set currentConversationId to new conversation:', currentConversationId);
            updateAIModeIndicator(newConv.ai_mode || null);
            showWelcomeMessage();
        }
        
        // Re-render conversations với currentConversationId đã được set
        renderConversations();
        
        showMessage('✅ Đã tạo cuộc hội thoại mới! Context đã được reset.', 'success');
    } catch (error) {
        console.error('Error creating new conversation:', error);
        showMessage('❌ Có lỗi xảy ra khi tạo cuộc hội thoại mới: ' + error.message, 'error');
    }
}

async function switchConversation(conversationId) {
    try {
        if (currentConversationId === conversationId) {
            console.log('[DEBUG] Already on this conversation:', conversationId);
            return;
        }
        
        console.log('[DEBUG] Switching to conversation:', conversationId);
        const response = await fetch(`/conversations/${conversationId}/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin'
        });
        const data = await response.json();
        if (response.ok) {
            // Cập nhật currentConversationId ngay lập tức
            currentConversationId = conversationId;
            console.log('[DEBUG] Updated currentConversationId to:', currentConversationId);
            
            // Re-render conversation list để hiển thị màu đúng
            renderConversations();
            
            // Load conversation content
            await loadAndShowConversation(conversationId);
            updateAIModeIndicator(data.conversation.ai_mode);
        } else {
            showMessage('❌ Không thể chuyển cuộc hội thoại: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error switching conversation:', error);
        showMessage('❌ Có lỗi xảy ra khi chuyển cuộc hội thoại', 'error');
    }
}

async function deleteConversation(conversationId, event) {
    try {
        console.log('[DEBUG] Deleting conversation:', conversationId);
        
        // Ngăn chặn sự kiện click lan truyền lên thẻ cha
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        
        if (!confirm('Bạn có chắc muốn xóa cuộc hội thoại này không?')) {
            return;
        }
        
        showMessage('🔄 Đang xóa cuộc hội thoại...', 'info');
        const response = await fetch(`/conversations/${conversationId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('[ERROR] Failed to delete conversation:', errorData);
            showMessage('❌ Không thể xóa cuộc hội thoại: ' + (errorData.error || 'Lỗi không xác định'), 'error');
            return;
        }
        
        const data = await response.json();
        console.log('[DEBUG] Conversation deleted successfully:', data);
        
        // Nếu xóa conversation hiện tại, clear chatbox
        if (conversationId === currentConversationId) {
            clearChatBox();
            currentConversationId = null;
            showWelcomeMessage();
        }
        
        // Cập nhật lại danh sách và hiển thị conversation active (nếu còn)
        conversations = data.conversations || [];
        renderConversations();
        
        showMessage('✅ Đã xóa cuộc hội thoại!', 'success');
    } catch (error) {
        console.error('[ERROR] Error deleting conversation:', error);
        showMessage('❌ Có lỗi xảy ra khi xóa cuộc hội thoại: ' + error.message, 'error');
    }
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
        // Check if this is a calendar request and calendar is available
        const isCalendarRequest = hasCalendarIntent(question);
        let endpoint = '/chat';
          if (isCalendarRequest && calendarStatus.authenticated && calendarStatus.status === 'ready') {
            console.log('[DEBUG] Detected calendar request, using calendar endpoint');
            endpoint = '/calendar/process';
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                question: question,
                user_id: getCurrentUserId()
            }),
            credentials: 'same-origin'
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
            replaceMessage(botMessageId, data.answer || data.response || data.message, 'bot');
            
            // Update suggestions
            updateSuggestions(data.suggestions || []);
            
            // Update AI mode indicator
            if (data.ai_mode) {
                updateAIModeIndicator(data.ai_mode);
            }
            
            // Handle calendar-specific responses
            if (data.calendar_action) {
                console.log('[DEBUG] Calendar action performed:', data.calendar_action);
                if (data.calendar_action === 'event_created') {
                    showMessage('✅ Sự kiện đã được tạo thành công trong Google Calendar!', 'success');
                }
            }
            
            // If calendar request but not authenticated, show auth prompt
            if (isCalendarRequest && (!calendarStatus.authenticated || calendarStatus.status !== 'ready')) {
                setTimeout(() => {
                    showMessage('📅 Để sử dụng tính năng lịch, vui lòng kết nối Google Calendar trước.', 'info');
                }, 1000);
            }
            
            // Chỉ cập nhật conversation list mà KHÔNG reload messages
            // để cập nhật metadata như message count
            setTimeout(() => {
                updateConversationMetadata();
            }, 500);
            
        } else {
            replaceMessage(botMessageId, '❌ Lỗi: ' + (data.error || data.message || 'Unknown error'), 'bot');
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
    
    const senderIcon = sender === 'user' ? '😺' : '🤖';
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
        
        const senderIcon = sender === 'user' ? '😺' : '🤖';
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
    
    if (!indicator || !modeSpan) {
        console.warn('[WARNING] AI mode indicator elements not found in the DOM');
        return;
    }
    
    if (mode) {
        modeSpan.textContent = getAIModeDisplay(mode);
        indicator.style.display = 'block';
    } else {
        indicator.style.display = 'none';
    }
}

// ====== DEBUG FUNCTIONS ======

async function exportChatHistory() {
    try {
        console.log('[DEBUG] Starting chat export...');
        showMessage('📥 Đang xuất lịch sử chat...', 'info');
        
        // Kiểm tra nếu không có hội thoại
        if (!conversations || conversations.length === 0) {
            showMessage('❌ Không có cuộc hội thoại nào để xuất', 'error');
            return;
        }
        
        const response = await fetch('/export-chat', {
            credentials: 'same-origin'
        });
        console.log('[DEBUG] Export response status:', response.status);
        
        if (!response.ok) {
            let errorMessage = 'Lỗi không xác định';
            try {
                const errorData = await response.json();
                console.error('[ERROR] Export failed:', errorData);
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                console.error('Could not parse error response:', e);
            }
            
            showMessage('❌ Không thể export chat: ' + errorMessage, 'error');
            return;
        }
        
        // Tạo file download HTML
        const blob = await response.blob();
        console.log('[DEBUG] Export blob size:', blob.size);
        
        if (blob.size === 0) {
            showMessage('❌ Xuất file thất bại: file trống', 'error');
            return;
        }
        
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
    } catch (error) {
        console.error('Error exporting chat:', error);
        showMessage('❌ Có lỗi xảy ra khi export chat: ' + error.message, 'error');
    }
}

// ====== HELPER FUNCTIONS ======

function askQuestion(question) {
    // Automatically fill input and send a question - used by suggestion buttons
    const input = document.getElementById('questionInput');
    input.value = question;
    sendQuestion();
}

function clearChatBox() {
    const chatBox = document.getElementById('chatBox');
    if (chatBox) {
        chatBox.innerHTML = '';
    }
    
    // Clear suggestions
    const suggestionsContainer = document.getElementById('suggestions');
    if (suggestionsContainer) {
        suggestionsContainer.innerHTML = '';
    }
    
    // Reset AI mode indicator
    updateAIModeIndicator(null);
}

function showMessage(message, type = 'info') {
    const messageArea = document.getElementById('messageArea');
    if (!messageArea) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message-alert ${type}`;
    messageElement.textContent = message;
    
    messageArea.appendChild(messageElement);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        messageElement.classList.add('fade-out');
        setTimeout(() => messageElement.remove(), 500);
    }, 5000);
}

// Hàm cập nhật metadata của conversation list mà không reload messages
async function updateConversationMetadata() {
    try {
        const response = await fetch('/conversations', { credentials: 'same-origin' });
        const data = await response.json();
        if (response.ok) {
            conversations = data.conversations || [];
            renderConversations();
        }
    } catch (error) {
        console.error('Error updating conversation metadata:', error);
    }
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

// ====== CALENDAR INTEGRATION ======
let calendarStatus = {
    authenticated: false,
    status: 'checking',
    message: 'Đang kiểm tra kết nối...'
};

// Check calendar authentication status
async function checkCalendarStatus() {
    try {
        console.log('[DEBUG] Checking calendar status...');
        const userId = getCurrentUserId();
        const response = await fetch(`/calendar/auth/status?user_id=${encodeURIComponent(userId)}`, {
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.json();
            calendarStatus = data;
            updateCalendarUI();
            console.log('[DEBUG] Calendar status:', data);
        } else {
            calendarStatus = {
                authenticated: false,
                status: 'error',
                message: 'Lỗi kiểm tra trạng thái lịch'
            };
            updateCalendarUI();
        }
    } catch (error) {
        console.error('[ERROR] Calendar status check failed:', error);
        calendarStatus = {
            authenticated: false,
            status: 'error',
            message: 'Không thể kết nối với dịch vụ lịch'
        };
        updateCalendarUI();
    }
}

// Update calendar UI based on status
function updateCalendarUI() {
    const statusElement = document.getElementById('calendarStatus');
    const statusText = document.getElementById('calendarStatusText');
    const authBtn = document.getElementById('calendarAuthBtn');
    
    if (!statusElement || !statusText || !authBtn) return;
    
    // Remove all status classes
    statusElement.classList.remove('connected', 'disconnected', 'checking');
    
    if (calendarStatus.authenticated && calendarStatus.status === 'ready') {
        statusElement.classList.add('connected');
        statusText.textContent = '📅 Lịch đã kết nối';
        authBtn.style.display = 'none';
    } else if (calendarStatus.status === 'need_auth') {
        statusElement.classList.add('disconnected');
        statusText.textContent = '📅 Chưa kết nối lịch';
        authBtn.style.display = 'inline-block';
        authBtn.textContent = 'Kết nối Google Calendar';
        authBtn.disabled = false;
    } else if (calendarStatus.status === 'need_refresh') {
        statusElement.classList.add('disconnected');
        statusText.textContent = '📅 Cần làm mới kết nối';
        authBtn.style.display = 'inline-block';
        authBtn.textContent = 'Làm mới kết nối';
        authBtn.disabled = false;
    } else if (calendarStatus.status === 'checking') {
        statusElement.classList.add('checking');
        statusText.textContent = '📅 Đang kiểm tra...';
        authBtn.style.display = 'none';
    } else {
        statusElement.classList.add('disconnected');
        statusText.textContent = '📅 Lỗi kết nối lịch';
        authBtn.style.display = 'inline-block';
        authBtn.textContent = 'Thử lại';
        authBtn.disabled = false;
    }
    
    // Update calendar suggestions
    updateCalendarSuggestions();
}

// Handle calendar authentication
async function authenticateCalendar() {
    try {
        console.log('[DEBUG] Starting calendar authentication...');
        const authBtn = document.getElementById('calendarAuthBtn');
        if (authBtn) {
            authBtn.disabled = true;
            authBtn.textContent = 'Đang xử lý...';
        }
        
        const response = await fetch('/calendar/auth/url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                user_id: getCurrentUserId()
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.auth_url) {
                // Open auth URL in new tab
                window.open(data.auth_url, '_blank');
                
                // Show message to user
                showMessage('🔗 Đã mở tab mới để xác thực Google Calendar. Sau khi hoàn tất, hãy quay lại đây.', 'info');
                
                // Start polling for auth completion
                startAuthPolling();
            } else {
                showMessage('❌ ' + (data.message || 'Không thể tạo link xác thực'), 'error');
            }
        } else {
            showMessage('❌ Lỗi kết nối với server', 'error');
        }
    } catch (error) {
        console.error('[ERROR] Calendar authentication failed:', error);
        showMessage('❌ Lỗi xác thực: ' + error.message, 'error');
    } finally {
        const authBtn = document.getElementById('calendarAuthBtn');
        if (authBtn) {
            authBtn.disabled = false;
            updateCalendarUI();
        }
    }
}

// Poll for authentication completion
function startAuthPolling() {
    const pollInterval = setInterval(async () => {
        await checkCalendarStatus();
        
        if (calendarStatus.authenticated && calendarStatus.status === 'ready') {
            clearInterval(pollInterval);
            showMessage('✅ Google Calendar đã được kết nối thành công!', 'success');
        }
    }, 3000); // Check every 3 seconds
    
    // Stop polling after 5 minutes
    setTimeout(() => {
        clearInterval(pollInterval);
    }, 300000);
}

// Get current user ID (simple implementation)
function getCurrentUserId() {
    let userId = localStorage.getItem('chatbot_user_id');
    if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('chatbot_user_id', userId);
    }
    return userId;
}

// Check if message contains calendar intent
function hasCalendarIntent(message) {
    const calendarKeywords = [
        'lịch', 'calendar', 'hẹn', 'cuộc họp', 'meeting', 'deadline',
        'nhắc nhở', 'remind', 'thời gian biểu', 'schedule', 'kế hoạch',
        'plan', 'sự kiện', 'event', 'tạo lịch', 'đặt lịch', 'book',
        'ngày mai', 'tuần sau', 'tháng sau', 'tomorrow', 'next week',
        'next month', 'hôm nay', 'today', 'ngày', 'giờ', 'phút'
    ];
    
    const lowerMessage = message.toLowerCase();
    return calendarKeywords.some(keyword => lowerMessage.includes(keyword));
}

// Update calendar suggestions based on authentication status
function updateCalendarSuggestions() {
    const calendarSuggestions = document.querySelectorAll('.calendar-suggestion');
    
    calendarSuggestions.forEach(suggestion => {
        if (calendarStatus.authenticated && calendarStatus.status === 'ready') {
            suggestion.classList.remove('disabled');
            suggestion.style.pointerEvents = 'auto';
            suggestion.setAttribute('title', 'Click để thử tính năng lịch');
        } else {
            suggestion.classList.add('disabled');
            suggestion.style.pointerEvents = 'none';
            suggestion.setAttribute('title', 'Cần kết nối Google Calendar để sử dụng');
        }
    });
}

// Handle OAuth callback (if opened in same window)
function handleOAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    
    if (code && state) {
        console.log('[DEBUG] OAuth callback detected');
        
        // Send the authorization code to backend
        fetch('/calendar/auth/callback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                code: code,
                user_id: state
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('✅ Google Calendar đã được kết nối thành công!', 'success');
                checkCalendarStatus();
                // Clean up URL
                window.history.replaceState({}, document.title, window.location.pathname);
            } else {
                showMessage('❌ Lỗi kết nối: ' + (data.message || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('[ERROR] OAuth callback failed:', error);
            showMessage('❌ Lỗi xử lý callback: ' + error.message, 'error');
        });
    }
}
