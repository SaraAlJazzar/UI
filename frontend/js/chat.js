/* ============================================
   Chat Page — page-specific JS
   ============================================ */

/* ===== DOM Elements ===== */
const messagesContainer = document.getElementById('chatMessages');
const chatEmpty = document.getElementById('chatEmpty');
const typingIndicator = document.getElementById('typingIndicator');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatForm = document.getElementById('chatForm');
const langSelect = document.getElementById('langSelect');
const langPicker = document.getElementById('langPicker');
const langPickerBtn = document.getElementById('langPickerBtn');
const langPickerLabel = document.getElementById('langPickerLabel');
const langPickerDropdown = document.getElementById('langPickerDropdown');

const sidebar = document.getElementById('sidebar');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');
const sessionList = document.getElementById('sessionList');
const sidebarEmpty = document.getElementById('sidebarEmpty');
const newChatBtn = document.getElementById('newChatBtn');
const historyToggle = document.getElementById('historyToggle');

let currentSessionId = null;
let chatHistory = [];

const LANG_LABELS = { ar: 'AR', en: 'EN', fr: 'FR', es: 'ES', tr: 'TR', de: 'DE' };

/* ===== Sidebar toggle ===== */
function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('open');
}

function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('open');
}

if (historyToggle) historyToggle.addEventListener('click', openSidebar);
if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeSidebar);

/* ===== Language picker ===== */
function syncLangPicker(lang) {
    if (langPickerLabel) langPickerLabel.textContent = LANG_LABELS[lang] || lang.toUpperCase();
    if (langPickerDropdown) {
        langPickerDropdown.querySelectorAll('.lang-option').forEach(function(opt) {
            opt.classList.toggle('active', opt.dataset.lang === lang);
        });
    }
}

function setLanguage(lang) {
    if (langSelect) langSelect.value = lang;
    syncLangPicker(lang);
    saveSettings({ language: lang });
}

function onSettingsLoaded(s) {
    if (s && s.language) {
        if (langSelect) langSelect.value = s.language;
        syncLangPicker(s.language);
    }
}

function beforeSaveSettings() {
    if (langSelect) cachedSettings.language = langSelect.value;
}

if (langSelect) {
    langSelect.addEventListener('change', function() {
        syncLangPicker(langSelect.value);
    });
}

if (langPickerBtn) {
    langPickerBtn.addEventListener('click', function() {
        if (langPicker) langPicker.classList.toggle('open');
    });
}

if (langPickerDropdown) {
    langPickerDropdown.querySelectorAll('.lang-option').forEach(function(opt) {
        opt.addEventListener('click', function() {
            setLanguage(opt.dataset.lang);
            if (langPicker) langPicker.classList.remove('open');
            showToast('لغة الرد: ' + opt.textContent);
        });
    });
}

document.addEventListener('click', function(e) {
    if (langPicker && !langPicker.contains(e.target)) {
        langPicker.classList.remove('open');
    }
});

/* ===== Session list ===== */
function formatTimeAgo(dateStr) {
    var diff = Date.now() - new Date(dateStr).getTime();
    var mins = Math.floor(diff / 60000);
    if (mins < 1) return 'الآن';
    if (mins < 60) return 'منذ ' + mins + ' دقيقة';
    var hrs = Math.floor(mins / 60);
    if (hrs < 24) return 'منذ ' + hrs + ' ساعة';
    var days = Math.floor(hrs / 24);
    if (days < 30) return 'منذ ' + days + ' يوم';
    return new Date(dateStr).toLocaleDateString('ar');
}

function loadSessions() {
    fetch('/sessions/')
        .then(function(res) {
            if (!res.ok) throw new Error('fail');
            return res.json();
        })
        .then(function(sessions) {
            renderSessionList(sessions);
        })
        .catch(function(e) {
            console.warn('Failed to load sessions', e);
        });
}

function renderSessionList(sessions) {
    if (!sessionList) return;
    var items = sessionList.querySelectorAll('.session-item');
    items.forEach(function(el) { el.remove(); });

    if (!sessions || !sessions.length) {
        if (sidebarEmpty) sidebarEmpty.style.display = '';
        return;
    }

    if (sidebarEmpty) sidebarEmpty.style.display = 'none';

    sessions.forEach(function(s) {
        var el = document.createElement('div');
        el.className = 'session-item' + (s.session_id === currentSessionId ? ' active' : '');
        el.dataset.id = s.session_id;
        el.innerHTML =
            '<div class="session-icon">' +
                '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>' +
            '</div>' +
            '<div class="session-info">' +
                '<div class="session-title">' + escapeHtml(s.title) + '</div>' +
                '<div class="session-time">' + formatTimeAgo(s.updated_at) + '</div>' +
            '</div>' +
            '<button class="session-delete" title="حذف">' +
                '<svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>' +
            '</button>';

        el.addEventListener('click', function(e) {
            if (e.target.closest('.session-delete')) return;
            openSession(s.session_id);
        });

        var delBtn = el.querySelector('.session-delete');
        if (delBtn) {
            delBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                deleteSession(s.session_id);
            });
        }

        sessionList.appendChild(el);
    });
}

function openSession(sessionId) {
    fetch('/sessions/' + sessionId)
        .then(function(res) {
            if (!res.ok) throw new Error('fail');
            return res.json();
        })
        .then(function(data) {
            currentSessionId = sessionId;
            chatHistory = data.messages.map(function(m) { return { role: m.role, text: m.text }; });

            clearMessages();
            data.messages.forEach(function(m) { addMessage(m.text, m.role); });

            highlightActiveSession();
            closeSidebar();
        })
        .catch(function() {
            showToast('فشل تحميل المحادثة');
        });
}

function deleteSession(sessionId) {
    fetch('/sessions/' + sessionId, { method: 'DELETE' })
        .then(function() {
            if (sessionId === currentSessionId) startNewChat();
            loadSessions();
            showToast('تم حذف المحادثة');
        })
        .catch(function() {
            showToast('فشل حذف المحادثة');
        });
}

function highlightActiveSession() {
    if (!sessionList) return;
    sessionList.querySelectorAll('.session-item').forEach(function(el) {
        el.classList.toggle('active', el.dataset.id === currentSessionId);
    });
}

/* ===== New chat ===== */
function startNewChat() {
    currentSessionId = null;
    chatHistory = [];
    clearMessages();
    if (chatEmpty) chatEmpty.style.display = '';
}

if (newChatBtn) {
    newChatBtn.addEventListener('click', function() {
        startNewChat();
        closeSidebar();
    });
}

/* ===== Messages ===== */
function clearMessages() {
    if (!messagesContainer) return;
    var msgs = messagesContainer.querySelectorAll('.msg');
    msgs.forEach(function(m) { m.remove(); });
    if (chatEmpty) chatEmpty.style.display = 'none';
}

function scrollToBottom() {
    if (messagesContainer) messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    var html = escapeHtml(text);
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/^#{3}\s+(.+)$/gm, '<div class="md-h3">$1</div>');
    html = html.replace(/^#{2}\s+(.+)$/gm, '<div class="md-h2">$1</div>');
    html = html.replace(/^#{1}\s+(.+)$/gm, '<div class="md-h1">$1</div>');
    html = html.replace(/^\s*[\-\*]\s+(.+)$/gm, '<div class="md-li">$1</div>');
    html = html.replace(/^\s*(\d+)\.\s+(.+)$/gm, '<div class="md-li"><span class="md-num">$1.</span> $2</div>');
    return html;
}

function addMessage(text, role) {
    if (chatEmpty) chatEmpty.style.display = 'none';
    if (!messagesContainer) return;

    var msg = document.createElement('div');
    msg.className = 'msg ' + role;

    var avatarSvg = role === 'user'
        ? '<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
        : '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>';

    var content = role === 'bot' ? formatMarkdown(text) : escapeHtml(text);

    msg.innerHTML =
        '<div class="msg-avatar">' + avatarSvg + '</div>' +
        '<div class="msg-bubble">' + content + '</div>';

    messagesContainer.insertBefore(msg, typingIndicator);
    scrollToBottom();
}

function showTyping() {
    if (typingIndicator) typingIndicator.classList.add('active');
    scrollToBottom();
}

function hideTyping() {
    if (typingIndicator) typingIndicator.classList.remove('active');
}

/* ===== Input ===== */
function autoResize() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
}

if (chatInput) {
    chatInput.addEventListener('input', autoResize);
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (chatForm) chatForm.dispatchEvent(new Event('submit'));
        }
    });
}

/* -------------------------------------- Chat structure ------------------------------------------- */
/* ===== Submit ===== */
if (chatForm) {
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();

        var message = chatInput ? chatInput.value.trim() : '';
        if (!message) return;

        chatInput.value = '';
        chatInput.style.height = 'auto';
        if (sendBtn) sendBtn.disabled = true;

        addMessage(message, 'user');
        chatHistory.push({ role: 'user', text: message });
        showTyping();

        var settings = (typeof getSettings === 'function') ? getSettings() : {};

        var body = { message: message, history: chatHistory };
        if (currentSessionId) body.session_id = currentSessionId;
        if (settings.apiKey) body.api_key = settings.apiKey;
        if (settings.model) body.model = settings.model;
        body.language = settings.language || 'ar';

        fetch('/gemini/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        })
        .then(function(res) {
            return res.json().then(function(data) {
                return { ok: res.ok, data: data };
            });
        })
        .then(function(result) {
            hideTyping();

            if (!result.ok) {
                throw new Error(result.data.detail || 'حدث خطأ غير متوقع');
            }

            addMessage(result.data.response, 'bot');
            chatHistory.push({ role: 'bot', text: result.data.response });

            if (result.data.session_id) {
                currentSessionId = result.data.session_id;
            }

            loadSessions();
            highlightActiveSession();
        })
        .catch(function(err) {
            hideTyping();
            addMessage('خطأ: ' + err.message, 'bot');
        })
        .finally(function() {
            if (sendBtn) sendBtn.disabled = false;
            if (chatInput) chatInput.focus();
        });
    });
}

/* ===== Init ===== */
loadSessions();
/*loadSessions is a function that loads the sessions from the server and renders them in the sidebar
Refresh the sidebar with the latest sessions*/

