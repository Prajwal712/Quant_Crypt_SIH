document.addEventListener('DOMContentLoaded', () => {
    // =============================
    // CONFIG
    // =============================
 

    const API_BASE = window.location.search.includes("bob")
  ? "http://localhost:5001"
  : "http://localhost:5000";

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

    async function apiDecrypt(messageId) {
        const res = await fetch(`${API_BASE}/api/decrypt`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ messageId })
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

        await refreshInbox();
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

            if (state.currentFolder === "inbox") {
                refreshInbox();
            } else {
                renderEmailList();
            }
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
            const sentMail = {
                id: result.message_id,
                sender: "Me",
                subject,
                time: "Just now",
                read: true,
                folder: "sent",
                security
            };

            state.emails.unshift(sentMail);

            composeModal.classList.remove('active');
            editor.innerHTML = '';
            document.getElementById('recipientEmail').value = '';
            document.getElementById('emailSubject').value = '';

            // 🔥 Force UI refresh if user is in Sent
            if (state.currentFolder === "sent") {
                renderEmailList();
            }

            alert("🔐 Quantum-Encrypted Email Sent");
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
            const folderMatch =
                state.currentFolder === "inbox"
                    ? email.folder === "inbox"
                    : email.folder === state.currentFolder;
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

   
    
    async function refreshInbox() {
        const res = await apiListEmails();
        if (res.status === "success") {
            // Remove old inbox mails
            state.emails = state.emails.filter(m => m.folder !== "inbox");

            // Add fresh inbox mails
            res.emails.forEach(e => {
                state.emails.push({
                    ...e,
                    folder: "inbox",
                    read: false,
                    decrypted: false
                });
            });

            renderEmailList();
        }
    }

    // =============================
    // OPEN & DECRYPT EMAIL (FINAL)
    // =============================
   async function openEmail(email) {

    if (email.decrypted) {
        emailDetail.innerHTML = `
            <div style="padding:40px; color: var(--danger)">
                🔒 This message was already decrypted once.<br/>
                OTP keys cannot be reused.
            </div>
        `;
        return;
    }
    emailDetail.innerHTML = `
        <div style="padding:40px; color: var(--text-secondary)">
            🔐 Decrypting message…
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/api/decrypt`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                messageId: email.id
            })
        });

        const data = await res.json();

        if (data.status !== "success") {
            throw new Error(data.error || "Decryption failed");
        }

        emailDetail.innerHTML = `
            <div class="detail-header">
                <div class="detail-subject">${data.subject || "Decrypted Mail"}</div>
                <div class="detail-meta">
                    From: <strong>${data.sender}</strong>
                </div>
                <div class="detail-security">
                    🔑 QKD Key: ${data.key_id}
                </div>
            </div>
            <div class="detail-body" style="white-space: pre-wrap">
                ${data.content}
            </div>
        `;

            email.decrypted = true;   
            email.read = true;
    } catch (err) {
        emailDetail.innerHTML = `
            <div style="padding:40px; color: var(--danger)">
                ❌ Decryption failed<br/>
                ${err.message}
            </div>
        `;
    }
}
});