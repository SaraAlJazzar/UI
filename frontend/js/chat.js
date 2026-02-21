/* ============================================
   Chat Page — page-specific JS
   ============================================ */

/* ===== DOM Elements ===== */
var messagesContainer = document.getElementById('chatMessages');
var chatEmpty = document.getElementById('chatEmpty');
var typingIndicator = document.getElementById('typingIndicator');
var chatInput = document.getElementById('chatInput');
var sendBtn = document.getElementById('sendBtn');
var chatForm = document.getElementById('chatForm');
var langSelect = document.getElementById('langSelect');
var langPicker = document.getElementById('langPicker');
var langPickerBtn = document.getElementById('langPickerBtn');
var langPickerLabel = document.getElementById('langPickerLabel');
var langPickerDropdown = document.getElementById('langPickerDropdown');

var sidebar = document.getElementById('sidebar');
var sidebarBackdrop = document.getElementById('sidebarBackdrop');
var sessionList = document.getElementById('sessionList');
var sidebarEmpty = document.getElementById('sidebarEmpty');
var newChatBtn = document.getElementById('newChatBtn');
var historyToggle = document.getElementById('historyToggle');

var uploadBtn = document.getElementById('uploadBtn');
var imageInput = document.getElementById('imageInput');
var imagePreviewStrip = document.getElementById('imagePreviewStrip');
var imagePreviewList = document.getElementById('imagePreviewList');
var imageLightbox = document.getElementById('imageLightbox');
var lightboxImg = document.getElementById('lightboxImg');

var summaryBtn = document.getElementById('summaryBtn');
var summaryOverlay = document.getElementById('summaryOverlay');
var summaryPopup = document.getElementById('summaryPopup');
var summaryClose = document.getElementById('summaryClose');
var summaryBody = document.getElementById('summaryBody');
var summaryLoading = document.getElementById('summaryLoading');
var summaryContent = document.getElementById('summaryContent');

var currentSessionId = null;
var chatHistory = [];
var pendingFiles = [];

var LANG_LABELS = { ar: 'AR', en: 'EN', fr: 'FR', es: 'ES', tr: 'TR', de: 'DE' };

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

/* ===== Multi-image upload handling ===== */
if (uploadBtn) {
    uploadBtn.addEventListener('click', function() {
        if (imageInput) imageInput.click();
    });
}

if (imageInput) {
    imageInput.addEventListener('change', function() {
        var files = imageInput.files;
        if (!files || !files.length) return;
        for (var i = 0; i < files.length; i++) {
            pendingFiles.push(files[i]);
        }
        imageInput.value = '';
        renderImagePreviews();
    });
}

function renderImagePreviews() {
    if (!imagePreviewList || !imagePreviewStrip) return;
    imagePreviewList.innerHTML = '';

    if (!pendingFiles.length) {
        imagePreviewStrip.style.display = 'none';
        if (uploadBtn) uploadBtn.classList.remove('has-image');
        return;
    }

    imagePreviewStrip.style.display = '';
    if (uploadBtn) uploadBtn.classList.add('has-image');

    pendingFiles.forEach(function(file, idx) {
        var item = document.createElement('div');
        item.className = 'image-preview-item';

        var img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.alt = file.name;
        item.appendChild(img);

        var removeBtn = document.createElement('button');
        removeBtn.className = 'image-preview-remove';
        removeBtn.title = 'إزالة';
        removeBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>';
        removeBtn.addEventListener('click', function() {
            pendingFiles.splice(idx, 1);
            renderImagePreviews();
        });
        item.appendChild(removeBtn);

        imagePreviewList.appendChild(item);
    });
}

function clearImagePreview() {
    pendingFiles = [];
    if (imageInput) imageInput.value = '';
    if (imagePreviewList) imagePreviewList.innerHTML = '';
    if (imagePreviewStrip) imagePreviewStrip.style.display = 'none';
    if (uploadBtn) uploadBtn.classList.remove('has-image');
}

/* ===== Voice recording ===== */
var recordBtn = document.getElementById('recordBtn');
var recordTimer = document.getElementById('recordTimer');
var recordTime = document.getElementById('recordTime');
var mediaRecorder = null;
var audioChunks = [];
var recordingInterval = null;
var recordStartTime = 0;

function formatRecordTime(ms) {
    var secs = Math.floor(ms / 1000);
    var m = Math.floor(secs / 60);
    var s = secs % 60;
    return m + ':' + (s < 10 ? '0' : '') + s;
}

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream, { mimeType: getSupportedMime() });

            mediaRecorder.addEventListener('dataavailable', function(e) {
                if (e.data.size > 0) audioChunks.push(e.data);
            });

            mediaRecorder.addEventListener('stop', function() {
                stream.getTracks().forEach(function(t) { t.stop(); });
                clearInterval(recordingInterval);
                if (recordTimer) recordTimer.style.display = 'none';
                if (recordBtn) {
                    recordBtn.classList.remove('recording');
                    recordBtn.classList.add('transcribing');
                }

                var blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
                sendForTranscription(blob, mediaRecorder.mimeType);
            });

            mediaRecorder.start();
            recordStartTime = Date.now();
            if (recordBtn) recordBtn.classList.add('recording');
            if (recordTimer) recordTimer.style.display = '';
            if (recordTime) recordTime.textContent = '0:00';

            recordingInterval = setInterval(function() {
                if (recordTime) recordTime.textContent = formatRecordTime(Date.now() - recordStartTime);
            }, 500);
        })
        .catch(function(err) {
            console.error('Microphone access denied:', err);
            showToast('لم يتم السماح بالوصول إلى الميكروفون');
        });
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

function getSupportedMime() {
    var types = ['audio/webm', 'audio/mp4', 'audio/ogg', 'audio/wav'];
    for (var i = 0; i < types.length; i++) {
        if (MediaRecorder.isTypeSupported(types[i])) return types[i];
    }
    return '';
}

function sendForTranscription(blob, mimeType) {
    var formData = new FormData();
    var ext = mimeType.split('/')[1] || 'webm';
    formData.append('audio', blob, 'recording.' + ext);

    var settings = (typeof getSettings === 'function') ? getSettings() : {};
    if (settings.apiKey) formData.append('api_key', settings.apiKey);
    if (settings.model) formData.append('model', settings.model);

    fetch('/gemini/transcribe', { method: 'POST', body: formData })
        .then(function(res) {
            return res.json().then(function(data) {
                return { ok: res.ok, data: data };
            });
        })
        .then(function(result) {
            if (recordBtn) recordBtn.classList.remove('transcribing');

            if (!result.ok) {
                throw new Error(result.data.detail || 'فشل تحويل الصوت');
            }

            var transcript = result.data.transcript || '';
            if (transcript && chatInput) {
                chatInput.value = chatInput.value ? chatInput.value + ' ' + transcript : transcript;
                chatInput.focus();
                if (typeof autoResize === 'function') autoResize();
                showToast('تم تحويل الصوت إلى نص');
            } else {
                showToast('لم يتم التعرف على كلام');
            }
        })
        .catch(function(err) {
            if (recordBtn) recordBtn.classList.remove('transcribing');
            showToast('خطأ: ' + err.message);
        });
}

if (recordBtn) {
    recordBtn.addEventListener('click', function() {
        if (recordBtn.classList.contains('recording')) {
            stopRecording();
        } else if (!recordBtn.classList.contains('transcribing')) {
            startRecording();
        }
    });
}

/* ===== Lightbox ===== */
function openLightbox(src) {
    if (lightboxImg) lightboxImg.src = src;
    if (imageLightbox) imageLightbox.classList.add('open');
}

function closeLightbox() {
    if (imageLightbox) imageLightbox.classList.remove('open');
    if (lightboxImg) lightboxImg.src = '';
}

if (imageLightbox) {
    imageLightbox.addEventListener('click', closeLightbox);
}

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
            data.messages.forEach(function(m) {
                var imgUrls = (m.images || []).map(function(img) { return img.path; });
                addMessage(m.text, m.role, imgUrls);
            });

            updateSummaryBtn();
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
    clearImagePreview();
    updateSummaryBtn();
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

function buildImagesHtml(imageUrls) {
    if (!imageUrls || !imageUrls.length) return '';
    var html = '<div class="msg-images">';
    imageUrls.forEach(function(src) {
        html += '<img class="msg-image" src="' + escapeHtml(src) + '" alt="صورة مرفقة" onclick="openLightbox(this.src)">';
    });
    html += '</div>';
    return html;
}

function addMessage(text, role, imageUrls) {
    if (chatEmpty) chatEmpty.style.display = 'none';
    if (!messagesContainer) return;

    var msg = document.createElement('div');
    msg.className = 'msg ' + role;

    var avatarSvg = role === 'user'
        ? '<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
        : '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>';

    var imagesHtml = buildImagesHtml(imageUrls);
    var content = role === 'bot' ? formatMarkdown(text) : escapeHtml(text);

    msg.innerHTML =
        '<div class="msg-avatar">' + avatarSvg + '</div>' +
        '<div class="msg-bubble">' + imagesHtml + content + '</div>';

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

/* ===== Submit ===== */
if (chatForm) {
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();

        var message = chatInput ? chatInput.value.trim() : '';
        if (!message && !pendingFiles.length) return;

        var localImageUrls = pendingFiles.map(function(f) {
            return URL.createObjectURL(f);
        });

        if (chatInput) { chatInput.value = ''; chatInput.style.height = 'auto'; }
        if (sendBtn) sendBtn.disabled = true;

        addMessage(message || '', 'user', localImageUrls.length ? localImageUrls : null);
        chatHistory.push({ role: 'user', text: message });
        showTyping();

        var settings = (typeof getSettings === 'function') ? getSettings() : {};

        var formData = new FormData();
        formData.append('message', message || 'ما هذه الصورة؟');
        if (currentSessionId) formData.append('session_id', currentSessionId);
        if (settings.apiKey) formData.append('api_key', settings.apiKey);
        if (settings.model) formData.append('model', settings.model);
        formData.append('language', settings.language || 'ar');

        pendingFiles.forEach(function(file) {
            formData.append('images', file);
        });

        clearImagePreview();

        fetch('/gemini/chat', {
            method: 'POST',
            body: formData
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
                updateSummaryBtn();
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

/* ===== Summary popup ===== */
var summaryRefresh = document.getElementById('summaryRefresh');
var summaryMeta = document.getElementById('summaryMeta');

function updateSummaryBtn() {
    if (summaryBtn) {
        summaryBtn.style.display = currentSessionId ? '' : 'none';
    }
}

function fetchSummary(forceRefresh) {
    if (!currentSessionId) return;
    if (summaryLoading) summaryLoading.style.display = '';
    if (summaryContent) { summaryContent.innerHTML = ''; summaryContent.style.display = 'none'; }
    if (summaryMeta) { summaryMeta.innerHTML = ''; summaryMeta.style.display = 'none'; }
    if (summaryRefresh) summaryRefresh.classList.add('spinning');

    var url = '/sessions/' + currentSessionId + '/summary';
    if (forceRefresh) url += '?refresh=true';

    fetch(url)
        .then(function(res) {
            return res.json().then(function(data) {
                return { ok: res.ok, data: data };
            });
        })
        .then(function(result) {
            if (summaryLoading) summaryLoading.style.display = 'none';
            if (summaryRefresh) summaryRefresh.classList.remove('spinning');
            if (summaryContent) summaryContent.style.display = '';

            if (!result.ok) {
                throw new Error(result.data.detail || 'فشل إنشاء الملخص');
            }

            if (summaryContent) {
                summaryContent.innerHTML = formatMarkdown(result.data.summary);
            }

            if (summaryMeta && result.data.generated_at) {
                summaryMeta.style.display = '';
                var metaHtml = '';
                if (result.data.cached) {
                    metaHtml += '<span class="summary-cached-badge">من الذاكرة المؤقتة</span>';
                }
                if (result.data.model_name) {
                    metaHtml += '<span class="summary-meta-item">' +
                        '<svg viewBox="0 0 24 24"><path d="M21 10.12h-6.78l2.74-2.82c-2.73-2.7-7.15-2.8-9.88-.1-2.73 2.71-2.73 7.08 0 9.79s7.15 2.71 9.88 0C18.32 15.65 19 14.08 19 12.1h2c0 1.98-.88 4.55-2.64 6.29-3.51 3.48-9.21 3.48-12.72 0-3.5-3.47-3.5-9.11 0-12.58 3.51-3.47 9.14-3.49 12.65-.06L21 3v7.12z"/></svg>' +
                        escapeHtml(result.data.model_name) + '</span>';
                }
                if (result.data.generated_at) {
                    var d = new Date(result.data.generated_at);
                    metaHtml += '<span class="summary-meta-item">' +
                        '<svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>' +
                        d.toLocaleString('ar') + '</span>';
                }
                summaryMeta.innerHTML = metaHtml;
            }
        })
        .catch(function(err) {
            if (summaryLoading) summaryLoading.style.display = 'none';
            if (summaryRefresh) summaryRefresh.classList.remove('spinning');
            if (summaryContent) {
                summaryContent.style.display = '';
                summaryContent.innerHTML = '<p style="color:#EF4444">خطأ: ' + escapeHtml(err.message) + '</p>';
            }
        });
}

function openSummaryPopup() {
    if (!currentSessionId) return;
    if (summaryOverlay) summaryOverlay.classList.add('open');
    if (summaryPopup) summaryPopup.classList.add('open');
    fetchSummary(false);
}

function closeSummaryPopup() {
    if (summaryOverlay) summaryOverlay.classList.remove('open');
    if (summaryPopup) summaryPopup.classList.remove('open');
}

if (summaryBtn) summaryBtn.addEventListener('click', openSummaryPopup);
if (summaryClose) summaryClose.addEventListener('click', closeSummaryPopup);
if (summaryOverlay) summaryOverlay.addEventListener('click', closeSummaryPopup);
if (summaryRefresh) summaryRefresh.addEventListener('click', function() { fetchSummary(true); });

/* ===== Init ===== */
loadSessions();
