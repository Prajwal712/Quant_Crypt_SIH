document.addEventListener('DOMContentLoaded', () => {
    // =============================
    // CONFIG
    // =============================
    const API_BASE = "http://localhost:5000";

    // =============================
    // STATE
    // =============================
    const state = {
        currentUser: null,
        emails: [],
        currentFolder: 'inbox',
        searchTerm: ''
    };

    // =============================
    // DOM ELEMENTS
    // =============================
    const screens = {
        login: document.getElementById('loginScreen'),
        app: document.getElementById('emailClient')
    };

    const loginBtn = document.getElementById('googleSignInBtn');

    const profileTrigger = document.getElementById('userProfileTrigger');
    const profilePopover = document.getElementById('profilePopover');
    const logoutBtn = document.getElementById('logoutBtn');

    const searchInput = document.getElementById('searchInput');
    const navItems = document.querySelectorAll('.nav-item');
    const listHeaderTitle = document.querySelector('.email-list-header span');

    const composeBtn = document.getElementById('composeBtn');
    const composeModal = document.getElementById('composeModal');
    const closeComposeBtn = document.getElementById('closeComposeBtn');
    const sendBtn = document.getElementById('sendEmailBtn');

    const emailList = document.getElementById('emailList');
    const emailDetail = document.getElementById('emailDetail');
    const editor = document.getElementById('emailBody');
    const toolbarBtns = document.querySelectorAll('.toolbar-btn');

    // =============================
    // API HELPERS
    // =============================
    async function apiInit() {
        const res = await fetch(`${API_BASE}/api/init`, { method: "POST" });
        return res.json();
    }

    async function apiListEmails() {
        const res = await fetch(`${API_BASE}/api/list`);
        return res.json();
    }

    async function apiSendEmail(payload) {
        const res = await fetch(`${API_BASE}/api/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        return res.json();
    }

    // =============================
    // LOGIN
    // =============================
    loginBtn.addEventListener('click', async () => {
        const init = await apiInit();

        if (init.status !== "success" && init.status !== "already_initialized") {
            alert("Backend initialization failed");
            return;
        }

        screens.login.classList.remove('active');
        screens.app.classList.add('active');

        state.currentUser = { name: "User", email: "me@gmail.com" };

        const inbox = await apiListEmails();
        state.emails = inbox.emails || [];
        renderEmailList();
    });

    // =============================
    // PROFILE POPOVER
    // =============================
    profileTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        profilePopover.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
        if (!profileTrigger.contains(e.target)) {
            profilePopover.classList.remove('active');
        }
    });

    logoutBtn.addEventListener('click', () => {
        state.currentUser = null;
        state.emails = [];
        profilePopover.classList.remove('active');

        screens.app.classList.remove('active');
        screens.login.classList.add('active');
    });

    // =============================
    // SEARCH
    // =============================
    searchInput.addEventListener('input', (e) => {
        state.searchTerm = e.target.value.toLowerCase();
        renderEmailList();
    });

    // =============================
    // NAVIGATION
    // =============================
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            state.currentFolder = item.querySelector('span').textContent.toLowerCase();
            listHeaderTitle.textContent = item.querySelector('span').textContent;

            renderEmailList();
        });
    });

    // =============================
    // COMPOSE
    // =============================
    composeBtn.addEventListener('click', () => composeModal.classList.add('active'));
    closeComposeBtn.addEventListener('click', () => composeModal.classList.remove('active'));

    toolbarBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            document.execCommand(btn.dataset.command, false, null);
        });
    });

    // =============================
    // SEND EMAIL (REAL BACKEND)
    // =============================
    sendBtn.addEventListener('click', async () => {
        const recipient = document.getElementById('recipientEmail').value;
        const subject = document.getElementById('emailSubject').value;
        const body = editor.innerText;
        const security = document.getElementById('securityLevel').value;

        if (!recipient || !subject || !body) {
            alert("Please fill all fields");
            return;
        }

        const result = await apiSendEmail({
            recipient,
            subject,
            body,
            security
        });

        if (result.status === "success") {
            alert("🔐 Quantum-Encrypted Email Sent");
            composeModal.classList.remove('active');

            editor.innerHTML = '';
            document.getElementById('recipientEmail').value = '';
            document.getElementById('emailSubject').value = '';
        } else {
            alert("❌ Send failed: " + result.error);
        }
    });

    // =============================
    // RENDER EMAIL LIST
    // =============================
    function renderEmailList() {
        emailList.innerHTML = '';

        const filtered = state.emails.filter(email => {
            const folderMatch = email.folder === state.currentFolder || state.currentFolder === "inbox";
            const searchMatch =
                !state.searchTerm ||
                email.subject.toLowerCase().includes(state.searchTerm) ||
                email.sender.toLowerCase().includes(state.searchTerm);

            return folderMatch && searchMatch;
        });

        if (filtered.length === 0) {
            emailList.innerHTML =
                `<div style="padding:20px;text-align:center;color:var(--text-secondary)">
                    No emails found
                 </div>`;
            return;
        }

        filtered.forEach(email => {
            const el = document.createElement('div');
            el.className = `email-item ${!email.read ? 'unread' : ''}`;
            el.innerHTML = `
                <div class="email-sender">
                    <span>${email.sender}</span>
                    <span class="email-time">${email.time}</span>
                </div>
                <div class="email-subject">${email.subject}</div>
            `;
            el.addEventListener('click', () => openEmail(email));
            emailList.appendChild(el);
        });
    }

    // =============================
    // OPEN EMAIL
    // =============================
    function openEmail(email) {
        email.read = true;
        renderEmailList();

        emailDetail.innerHTML = `
            <div class="detail-header">
                <div class="detail-subject">${email.subject}</div>
                <div class="detail-meta">
                    <span>From: <strong>${email.sender}</strong></span>
                </div>
            </div>
            <div class="detail-body">
                <em>Encrypted message – decrypt via backend</em>
            </div>
        `;
    }
});