/* ============================================
   RAG Page — page-specific JS
   ============================================ */

let currentMode = 'normal';

const WEBSITE_NAMES = {
    altibbi: 'الطبي',
    mayoclinic: 'مايو كلينك',
    mawdoo3: 'موضوع'
};

const queryInput = document.getElementById('queryInput');
const numLinks = document.getElementById('numLinks');
const submitBtn = document.getElementById('submitBtn');
const loadingState = document.getElementById('loadingState');
const resultCard = document.getElementById('resultCard');
const errorCard = document.getElementById('errorCard');
const compareResult = document.getElementById('compareResult');
const mainContainer = document.getElementById('mainContainer');

function setMode(mode) {
    currentMode = mode;

    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    document.getElementById('normalWebsite').style.display = mode === 'normal' ? '' : 'none';
    document.getElementById('compareWebsites').style.display = mode === 'compare' ? '' : 'none';

    const btnText = document.getElementById('submitBtnText');
    btnText.textContent = mode === 'normal' ? 'ابحث واحصل على الإجابة' : 'قارن بين المصدرين';

    hideAll();
    mainContainer.classList.toggle('wide', mode === 'compare');
}

function hideAll() {
    loadingState.classList.remove('active');
    resultCard.classList.remove('active');
    errorCard.classList.remove('active');
    compareResult.classList.remove('active');
}

function animateSteps() {
    const steps = [
        document.getElementById('step1'),
        document.getElementById('step2'),
        document.getElementById('step3')
    ];

    steps.forEach(s => { s.classList.remove('active', 'done'); });
    steps[0].classList.add('active');

    setTimeout(() => {
        steps[0].classList.remove('active');
        steps[0].classList.add('done');
        steps[1].classList.add('active');
    }, 2500);

    setTimeout(() => {
        steps[1].classList.remove('active');
        steps[1].classList.add('done');
        steps[2].classList.add('active');
    }, 5000);
}

function decodeUrl(url) {
    try { return decodeURIComponent(url); }
    catch { return url; }
}

function renderSources(container, links) {
    container.innerHTML = '';
    links.forEach((link, i) => {
        const a = document.createElement('a');
        a.href = link.url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.className = 'source-link';
        a.innerHTML = `
            <span class="source-num">${i + 1}</span>
            <div class="source-body">
                <div class="source-title">${link.title}</div>
                <div class="source-snippet">${link.snippet}</div>
                <div class="source-url">
                    <svg viewBox="0 0 24 24"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>
                    <span>${decodeUrl(link.url)}</span>
                </div>
            </div>
            <svg class="source-external" viewBox="0 0 24 24"><path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>
        `;
        container.appendChild(a);
    });
}

async function fetchRAG(query, numLinks, website) {
    const settings = getSettings();
    const body = { query, num_links: numLinks, website };
    if (settings.apiKey) body.api_key = settings.apiKey;
    if (settings.model) body.model = settings.model;

    const res = await fetch('/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'حدث خطأ غير متوقع');
    return data;
}

async function submitNormal(query, links) {
    const website = document.getElementById('websiteSelect').value;

    hideAll();
    loadingState.classList.add('active');
    animateSteps();

    try {
        const data = await fetchRAG(query, links, website);

        hideAll();
        resultCard.classList.add('active');

        document.getElementById('resultMeta').textContent =
            `تم الاسترجاع من ${data.used_links.length} مصدر — ${data.source}`;
        document.getElementById('responseBody').textContent = data.response;
        renderSources(document.getElementById('sourcesList'), data.used_links);
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (err) {
        hideAll();
        errorCard.classList.add('active');
        document.getElementById('errorMessage').textContent = err.message;
    }
}

async function submitCompare(query, links) {
    const ws1 = document.getElementById('compareSelect1').value;
    const ws2 = document.getElementById('compareSelect2').value;

    if (ws1 === ws2) {
        hideAll();
        errorCard.classList.add('active');
        document.getElementById('errorMessage').textContent = 'يرجى اختيار مصدرين مختلفين للمقارنة';
        return;
    }

    hideAll();
    compareResult.classList.add('active');

    document.getElementById('compareBadge1').textContent = WEBSITE_NAMES[ws1];
    document.getElementById('compareBadge2').textContent = WEBSITE_NAMES[ws2];

    document.getElementById('compareLoading1').style.display = '';
    document.getElementById('compareContent1').style.display = 'none';
    document.getElementById('compareError1').style.display = 'none';

    document.getElementById('compareLoading2').style.display = '';
    document.getElementById('compareContent2').style.display = 'none';
    document.getElementById('compareError2').style.display = 'none';

    compareResult.scrollIntoView({ behavior: 'smooth', block: 'start' });

    const handleSide = async (website, sideNum) => {
        try {
            const data = await fetchRAG(query, links, website);
            document.getElementById(`compareLoading${sideNum}`).style.display = 'none';
            document.getElementById(`compareContent${sideNum}`).style.display = '';
            document.getElementById(`compareBody${sideNum}`).textContent = data.response;
            renderSources(document.getElementById(`compareSources${sideNum}`), data.used_links);
        } catch (err) {
            document.getElementById(`compareLoading${sideNum}`).style.display = 'none';
            document.getElementById(`compareError${sideNum}`).style.display = '';
            document.getElementById(`compareErrorMsg${sideNum}`).textContent = err.message;
        }
    };

    await Promise.all([
        handleSide(ws1, 1),
        handleSide(ws2, 2)
    ]);
}

async function submitQuery(e) {
    e.preventDefault();

    const query = queryInput.value.trim();
    const links = parseInt(numLinks.value);

    if (!query) return;

    submitBtn.disabled = true;

    if (currentMode === 'normal') {
        await submitNormal(query, links);
    } else {
        await submitCompare(query, links);
    }

    submitBtn.disabled = false;
}
