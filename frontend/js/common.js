/* ============================================
   Common JS — shared across all pages
   (menu dropdown, settings panel, toast)
   ============================================ */

document.addEventListener('click', (e) => {
    const dd = document.getElementById('menuDropdown');
    if (dd && !dd.contains(e.target)) dd.classList.remove('open');
});

const apiKeyInput = document.getElementById('apiKeyInput');
const modelSelect = document.getElementById('modelSelect');
const contextRange = document.getElementById('contextRange');
const contextValue = document.getElementById('contextValue');
const settingsPanel = document.getElementById('settingsPanel');
const settingsOverlay = document.getElementById('settingsOverlay');
const settingsClose = document.getElementById('settingsClose');
const settingsSave = document.getElementById('settingsSave');

let cachedSettings = { api_key: '', model: 'gemini-2.5-flash-lite', language: 'ar', context_messages: 4 };

async function loadSettings() {
    try {
        const res = await fetch('/settings/');
        if (res.ok) {
            const s = await res.json();
            cachedSettings = s;
            if (apiKeyInput) apiKeyInput.value = s.api_key || '';
            if (modelSelect && s.model) modelSelect.value = s.model;
            if (contextRange && s.context_messages !== undefined) {
                contextRange.value = s.context_messages;
                if (contextValue) contextValue.textContent = s.context_messages;
            }
            if (typeof onSettingsLoaded === 'function') onSettingsLoaded(s);
        }
    } catch (e) {
        console.warn('Failed to load settings from API', e);
    }
}

async function saveSettings(extraData) {
    const data = {
        api_key: apiKeyInput ? apiKeyInput.value.trim() : (cachedSettings.api_key || ''),
        model: modelSelect ? modelSelect.value : (cachedSettings.model || 'gemini-2.5-flash-lite'),
        language: cachedSettings.language || 'ar',
        context_messages: contextRange ? parseInt(contextRange.value) : (cachedSettings.context_messages ?? 4),
        ...extraData,
    };
    try {
        const res = await fetch('/settings/', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            cachedSettings = await res.json();
        }
    } catch (e) {
        console.warn('Failed to save settings to API', e);
    }
}

function getSettings() {
    return {
        apiKey: cachedSettings.api_key || '',
        model: cachedSettings.model || 'gemini-2.5-flash-lite',
        language: cachedSettings.language || 'ar',
        contextMessages: cachedSettings.context_messages ?? 4
    };
}

function openSettings() {
    settingsPanel.classList.add('active');
    settingsOverlay.classList.add('active');
}

function closeSettings() {
    settingsPanel.classList.remove('active');
    settingsOverlay.classList.remove('active');
}

function showToast(message) {
    let toast = document.querySelector('.toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}

if (settingsClose) settingsClose.addEventListener('click', closeSettings);
if (settingsOverlay) settingsOverlay.addEventListener('click', closeSettings);

if (settingsSave) {
    settingsSave.addEventListener('click', async () => {
        if (typeof beforeSaveSettings === 'function') beforeSaveSettings();
        await saveSettings();
        closeSettings();
        showToast('تم حفظ الإعدادات بنجاح');
    });
}

if (contextRange && contextValue) {
    contextRange.addEventListener('input', () => {
        contextValue.textContent = contextRange.value;
    });
}

loadSettings();
