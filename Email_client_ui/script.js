document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        currentUser: null,
        emails: [],
        currentFolder: 'inbox',
        searchTerm: ''
    };

    // DOM Elements
    const screens = {
        login: document.getElementById('loginScreen'),
        app: document.getElementById('emailClient')
    };

    // Login
    const loginBtn = document.getElementById('googleSignInBtn');

    // Profile
    const profileTrigger = document.getElementById('userProfileTrigger');
    const profilePopover = document.getElementById('profilePopover');
    const logoutBtn = document.getElementById('logoutBtn');

    // App Navigation & Search
    const searchInput = document.getElementById('searchInput');
    const navItems = document.querySelectorAll('.nav-item');
    const listHeaderTitle = document.querySelector('.email-list-header span');

    // Compose
    const composeBtn = document.getElementById('composeBtn');
    const composeModal = document.getElementById('composeModal');
    const closeComposeBtn = document.getElementById('closeComposeBtn');
    const sendBtn = document.getElementById('sendEmailBtn');

    // List & Detail
    const emailList = document.getElementById('emailList');
    const emailDetail = document.getElementById('emailDetail');
    const editor = document.getElementById('emailBody');
    const toolbarBtns = document.querySelectorAll('.toolbar-btn');

    // Data Generation
    const generateMockEmails = () => {
        const senders = ['Google Security', 'Netflix', 'Amazon', 'LinkedIn', 'Twitter', 'Slack', 'GitHub'];
        const subjects = ['Security Alert', 'New Arrival', 'Your Order', 'New Connection', 'Login Alert', 'Mentioned in #general', 'Workflow success'];
        const folders = ['inbox', 'inbox', 'inbox', 'starred', 'important', 'spam', 'trash'];

        return Array.from({ length: 25 }, (_, i) => ({
            id: i + 1,
            sender: senders[Math.floor(Math.random() * senders.length)],
            subject: subjects[Math.floor(Math.random() * subjects.length)],
            body: `This is the body for email #${i + 1}. It contains confidential information.`,
            time: new Date(Date.now() - Math.floor(Math.random() * 5000000000)).toLocaleDateString(),
            read: Math.random() > 0.4,
            folder: folders[Math.floor(Math.random() * folders.length)],
            securityLevel: ['standard', 'confidential', 'top-secret'][Math.floor(Math.random() * 3)]
        }));
    };

    // --- Event Listeners ---

    // Login
    loginBtn.addEventListener('click', () => {
        screens.login.classList.remove('active');
        screens.app.classList.add('active');
        state.emails = generateMockEmails();
        state.currentUser = { name: 'User Name', email: 'user@gmail.com' };
        renderEmailList();
    });

    // Profile Popover
    profileTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        profilePopover.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
        if (!profileTrigger.contains(e.target)) {
            profilePopover.classList.remove('active');
        }
    });

    logoutBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // prevent re-triggering popover
        // Reset
        state.currentUser = null;
        state.emails = [];
        profilePopover.classList.remove('active');

        // Switch Screens
        screens.app.classList.remove('active');
        screens.login.classList.add('active');
    });

    // Search
    searchInput.addEventListener('input', (e) => {
        state.searchTerm = e.target.value.toLowerCase();
        renderEmailList();
    });

    // Navigation
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            const folderName = item.querySelector('span').textContent.toLowerCase();
            state.currentFolder = folderName;

            // Update Header
            listHeaderTitle.textContent = item.querySelector('span').textContent;

            renderEmailList();
        });
    });

    // Compose
    composeBtn.addEventListener('click', () => composeModal.classList.add('active'));
    closeComposeBtn.addEventListener('click', () => composeModal.classList.remove('active'));

    toolbarBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            document.execCommand(btn.dataset.command, false, null);
        });
    });

    sendBtn.addEventListener('click', () => {
        const recipient = document.getElementById('recipientEmail').value;
        const subject = document.getElementById('emailSubject').value;
        const body = editor.innerHTML;
        const security = document.getElementById('securityLevel').value;

        if (!recipient || !subject) return alert('Please fill in required fields');

        const newEmail = {
            id: Date.now(),
            sender: 'Me',
            subject: subject,
            body: body,
            time: 'Just now',
            read: true,
            folder: 'sent',
            securityLevel: security
        };

        state.emails.unshift(newEmail);
        composeModal.classList.remove('active');

        // Clear form
        document.getElementById('recipientEmail').value = '';
        document.getElementById('emailSubject').value = '';
        editor.innerHTML = '';

        if (state.currentFolder === 'sent') renderEmailList();
        // Optional: show toast
        console.log("Email sent!");
    });

    // --- Render Logic ---

    function renderEmailList() {
        emailList.innerHTML = '';

        const filtered = state.emails.filter(email => {
            // Folder Filter
            const folderMatch = email.folder === state.currentFolder;

            // Search Filter
            const searchMatch = !state.searchTerm ||
                email.subject.toLowerCase().includes(state.searchTerm) ||
                email.sender.toLowerCase().includes(state.searchTerm);

            return folderMatch && searchMatch;
        });

        if (filtered.length === 0) {
            emailList.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-secondary)">No emails found</div>`;
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
                <div class="email-preview">${email.body.replace(/<[^>]*>/g, '')}</div>
            `;
            el.addEventListener('click', () => openEmail(email));
            emailList.appendChild(el);
        });
    }

    function openEmail(email) {
        email.read = true;
        renderEmailList();

        const badgeText = email.securityLevel === 'top-secret' ? 'Top Secret' :
            email.securityLevel === 'confidential' ? 'Confidential' : 'Standard';

        emailDetail.innerHTML = `
            <div class="detail-header">
                <div class="detail-subject">${email.subject}</div>
                <div class="detail-meta">
                    <span>From: <strong>${email.sender}</strong></span>
                    <span>${email.time}</span>
                </div>
                <div class="detail-security" style="
                    color: ${email.securityLevel === 'top-secret' ? '#ef4444' : '#667eea'};
                    background: ${email.securityLevel === 'top-secret' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(102, 126, 234, 0.1)'}
                ">
                    Security: ${badgeText}
                </div>
            </div>
            <div class="detail-body">${email.body}</div>
        `;
    }
});
