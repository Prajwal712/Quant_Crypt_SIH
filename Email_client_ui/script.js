document.addEventListener('DOMContentLoaded', () => {
    // =============================
    // CONFIG
    // =============================

    // Configurable API base
    const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? `http://localhost:${new URLSearchParams(window.location.search).get("port") || "5000"}`
        : "https://quantum-mail-api.onrender.com";

    // =============================
    // STATE
    // =============================
    const state = {
        currentUser: null,
        emails: [],
        currentFolder: 'inbox',
        searchTerm: '',
        emailFilter: 'quantum',  // 'quantum' or 'all'
        decryptedCache: {},       // message_id -> decrypted data (session cache)
    };

    // =============================
    // DOM ELEMENTS
    // =============================
    const screens = {
        login: document.getElementById('loginScreen'),
        app: document.getElementById('emailClient')
    };

    const loginBtn = document.getElementById('googleSignInBtn');
    const loginStatus = document.getElementById('loginStatus');

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
    const refreshBtn = document.getElementById('refreshBtn');

    const filterToggle = document.getElementById('filterToggle');

    // =============================
    // CHECK AUTH ON PAGE LOAD
    // =============================
    checkAuthStatus();

    // Handle OAuth callback redirect
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth') === 'success') {
        // Remove the query param from URL
        window.history.replaceState({}, document.title, window.location.pathname);
        checkAuthStatus();
    } else if (urlParams.get('auth') === 'error') {
        window.history.replaceState({}, document.title, window.location.pathname);
        showLoginError('Authentication failed. Please try again.');
    }

    async function checkAuthStatus() {
        try {
            const res = await fetch(`${API_BASE}/api/me`, {
                credentials: 'include'
            });
            const data = await res.json();

            if (data.status === 'success' && data.user) {
                // User is already authenticated
                await loginUser(data.user);
            }
        } catch (err) {
            // Not authenticated, stay on login screen
            console.log('Not authenticated');
        }
    }

    function showLoginError(msg) {
        if (loginStatus) {
            loginStatus.textContent = msg;
            loginStatus.style.color = '#ef4444';
            loginStatus.style.display = 'block';
        }
    }

    // =============================
    // REFRESH BUTTON
    // =============================
    refreshBtn.addEventListener('click', async () => {
        refreshBtn.classList.add('spinning');
        await refreshInbox();
        refreshBtn.classList.remove('spinning');
    });

    // =============================
    // FILTER TOGGLE
    // =============================
    if (filterToggle) {
        filterToggle.addEventListener('change', async () => {
            state.emailFilter = filterToggle.checked ? 'all' : 'quantum';
            await refreshInbox();
        });
    }

    // =============================
    // API HELPERS
    // =============================
    async function apiInit() {
        const res = await fetch(`${API_BASE}/api/init`, {
            method: "POST",
            credentials: 'include'
        });
        return res.json();
    }

    async function apiListEmails(filter = 'quantum') {
        const res = await fetch(`${API_BASE}/api/list?filter=${filter}`, {
            credentials: 'include'
        });
        return res.json();
    }

    async function apiSendEmail(payload) {
        const res = await fetch(`${API_BASE}/api/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        return res.json();
    }

    async function apiDecrypt(messageId) {
        const res = await fetch(`${API_BASE}/api/decrypt`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: 'include',
            body: JSON.stringify({ messageId })
        });
        return res.json();
    }

    // =============================
    // LOGIN — Google OAuth Flow
    // =============================
    loginBtn.addEventListener('click', async () => {
        loginBtn.disabled = true;
        loginBtn.innerHTML = `
            <div class="btn-spinner"></div>
            Connecting to Google...
        `;

        try {
            const res = await fetch(`${API_BASE}/api/auth/google`, {
                credentials: 'include'
            });
            const data = await res.json();

            if (data.status === 'success' && data.auth_url) {
                // Redirect user to Google OAuth consent screen
                window.location.href = data.auth_url;
            } else {
                showLoginError('Failed to start sign-in. Please try again.');
                resetLoginBtn();
            }
        } catch (err) {
            showLoginError('Could not connect to server. Is the backend running?');
            resetLoginBtn();
        }
    });

    function resetLoginBtn() {
        loginBtn.disabled = false;
        loginBtn.innerHTML = `
            <svg class="google-icon" viewBox="0 0 24 24" width="18" height="18">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Sign in with Google
        `;
    }

    async function loginUser(userInfo) {
        // Initialize the backend engine
        const init = await apiInit();

        if (init.status !== "success" && init.status !== "already_initialized") {
            showLoginError("Backend initialization failed. Please try again.");
            resetLoginBtn();
            return;
        }

        // Use user info from /api/me or from init response
        const user = userInfo || init.user;

        state.currentUser = {
            name: user.name || 'User',
            email: user.email || '',
            picture: user.picture || '',
        };

        // Update UI with user info
        updateUserProfile();

        // Switch screens
        screens.login.classList.remove('active');
        screens.app.classList.add('active');

        // Load decrypted cache from server
        await loadDecryptedCache();

        // Load inbox
        await refreshInbox();
    }

    function updateUserProfile() {
        const { name, email, picture } = state.currentUser;
        const initial = name ? name[0].toUpperCase() : 'U';

        document.getElementById("userName").innerText = name;
        document.querySelector(".popover-name").innerText = name;
        document.querySelector(".popover-email").innerText = email;

        const userAvatar = document.querySelector(".user-avatar");
        const popoverAvatar = document.querySelector(".popover-avatar");

        if (picture) {
            userAvatar.innerHTML = `<img src="${picture}" alt="${initial}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
            popoverAvatar.innerHTML = `<img src="${picture}" alt="${initial}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
        } else {
            userAvatar.innerText = initial;
            popoverAvatar.innerText = initial;
        }
    }

    async function loadDecryptedCache() {
        try {
            const res = await fetch(`${API_BASE}/api/decrypted-cache`, {
                credentials: 'include'
            });
            const data = await res.json();
            if (data.status === 'success') {
                state.decryptedCache = data.decrypted_emails || {};
            }
        } catch (err) {
            console.log('Could not load decrypted cache');
        }
    }

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

    logoutBtn.addEventListener('click', async () => {
        await fetch(`${API_BASE}/api/logout`, {
            method: "POST",
            credentials: 'include'
        });

        state.currentUser = null;
        state.emails = [];
        state.decryptedCache = {};
        profilePopover.classList.remove('active');

        screens.app.classList.remove('active');
        screens.login.classList.add('active');

        // Reset login button
        resetLoginBtn();
        if (loginStatus) loginStatus.style.display = 'none';
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

        sendBtn.disabled = true;
        sendBtn.textContent = 'Sending...';

        const result = await apiSendEmail({
            recipient,
            subject,
            body,
            security
        });

        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';

        if (result.status === "success") {
            const sentMail = {
                id: result.message_id,
                sender: state.currentUser ? state.currentUser.email : "Me",
                subject,
                time: "Just now",
                read: true,
                folder: "sent",
                security_level: Number(result.security_level ?? security),
                is_quantum: true,
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
            const subjectText = (email.subject || "").toLowerCase();
            const senderText = (email.sender || "").toLowerCase();

            const searchMatch =
                !state.searchTerm ||
                subjectText.includes(state.searchTerm) ||
                senderText.includes(state.searchTerm);

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

            // Check decrypted cache for read state
            const isCached = state.decryptedCache[email.id] || email.decrypted;
            const readClass = isCached || email.read ? 'read' : 'unread';

            el.className = `email-item ${readClass}`;
            const subject =
                email.subject && email.subject.trim()
                    ? email.subject
                    : "(No subject)";

            const quantumBadge = email.is_quantum
                ? `<span class="quantum-badge" title="Quantum Encrypted">🔐</span>`
                : '';

            const decryptedBadge = isCached
                ? `<span class="decrypted-badge" title="Decrypted (cached)">✅</span>`
                : '';

            el.innerHTML = `
                <div class="email-sender">
                    <span>${email.sender} ${quantumBadge} ${decryptedBadge}</span>
                    <span class="email-time">${email.time}</span>
                </div>
                <div class="email-subject">${subject}</div>
            `;
            el.addEventListener('click', () => openEmail(email));
            emailList.appendChild(el);
        });
    }

   
    async function refreshInbox() {
        const res = await apiListEmails(state.emailFilter);
        if (res.status === "success") {
            // Remove old inbox mails
            state.emails = state.emails.filter(m => m.folder !== "inbox");

            // Add fresh inbox mails
            res.emails.forEach(e => {
                const isCached = state.decryptedCache[e.id] || e.is_decrypted;
                state.emails.push({
                    ...e,
                    folder: "inbox",
                    read: isCached,
                    decrypted: isCached,
                    security_level: Number(e.security_level)
                });
            });

            renderEmailList();
        }
    }

    // =============================
    // OPEN & DECRYPT EMAIL
    // =============================
    async function openEmail(email) {

        // Check in-memory cache first
        if (state.decryptedCache[email.id]) {
            const cached = state.decryptedCache[email.id];
            showDecryptedEmail(cached, email);
            return;
        }

        // If already decrypted in this page load
        if (email.decrypted && email._cachedContent) {
            emailDetail.innerHTML = email._cachedContent;
            return;
        }

        // For non-quantum emails, show a basic view
        if (!email.is_quantum) {
            emailDetail.innerHTML = `
                <div class="detail-header">
                    <div class="detail-subject">${email.subject || '(No subject)'}</div>
                    <div class="detail-meta">
                        From: <strong>${email.sender}</strong>
                    </div>
                    <div class="detail-security" style="background:rgba(180,180,200,0.1);color:var(--text-secondary);">
                        📧 Standard Email (not quantum-encrypted)
                    </div>
                </div>
                <div class="detail-body">
                    <p style="color:var(--text-secondary);font-style:italic;">
                        This email is not quantum-encrypted. Content preview is not available.
                    </p>
                </div>
            `;
            return;
        }

        emailDetail.innerHTML = `
            <div class="decrypt-loading">
                <div class="decrypt-spinner"></div>
                <p>🔐 Decrypting message with QKD key…</p>
            </div>
        `;

        try {
            const data = await apiDecrypt(email.id);

            if (data.status !== "success") {
                throw new Error(data.error || "Decryption failed");
            }

            // Store in session cache
            state.decryptedCache[email.id] = data;

            showDecryptedEmail(data, email);

        } catch (err) {
            emailDetail.innerHTML = `
                <div style="padding:40px; color: var(--danger)">
                    ❌ Decryption failed<br/>
                    ${err.message}
                </div>
            `;
        }
    }

    function showDecryptedEmail(data, email) {
        const detailHTML = `
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

        emailDetail.innerHTML = detailHTML;

        // Cache the decrypted content in the email object too
        email._cachedContent = detailHTML;
        email.decrypted = true;
        email.security_level = Number(data.security_level);
        email.read = true;

        // Re-render list to update read/decrypted badges
        renderEmailList();
    }
});