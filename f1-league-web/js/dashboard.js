document.addEventListener('DOMContentLoaded', async () => {
    // 1. Check Authentication
    const user = await checkAuth();
    if (!user) {
        window.location.href = '/login.html';
        return;
    }

    // Update User Info
    document.getElementById('adminName').textContent = user.username;
    if (user.avatar) {
        document.getElementById('adminAvatar').src = `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`;
    }

    // 2. Initial Data Load
    loadDashboardData();

    // 3. Event Listeners
    setupEventListeners();
});

// -- Authentication --
async function checkAuth() {
    try {
        // 1. Check Admin Status First (since password login sets this)
        const adminCheck = await fetch('/api/admin/check');
        const adminData = await adminCheck.json();

        if (adminData.isAdmin) {
            // If admin, we can mock a user object or fetch discord user if available
            const userRes = await fetch('/api/user');
            const userData = await userRes.json();

            return userData.authenticated ? userData.user : {
                username: "Admin User",
                id: "admin",
                avatar: null,
                isAdmin: true
            };
        }

        // 2. If not admin, check if normal discord user
        const res = await fetch('/api/user');
        const data = await res.json();
        return data.authenticated ? data.user : null;

    } catch (e) {
        console.error("Auth check failed", e);
        return null;
    }
}

// -- Data Loading --
async function loadDashboardData() {
    try {
        const res = await fetch('/api/players');
        const players = await res.json();

        updateOverview(players);
        updateDriversTable(players);
    } catch (e) {
        console.error("Failed to load players", e);
    }
}

function updateOverview(players) {
    const drivers = players.filter(p => p.role === 'driver');

    // Stats
    document.getElementById('totalDrivers').textContent = drivers.length;

    // Penalties (mock calculation based on player.penalties)
    let activePenalties = 0;
    drivers.forEach(p => {
        if (p.penalties && p.penalties.total_points > 0) activePenalties++;
    });
    document.getElementById('activePenalties').textContent = activePenalties;

    // Completed Races (Mock)
    document.getElementById('completedRaces').textContent = "0"; // To be connected to races api

    // Top 5 Table
    const top5 = drivers.sort((a, b) => (b.total_points || 0) - (a.total_points || 0)).slice(0, 5);
    const top5Html = top5.map((p, i) => `
        <tr>
            <td><span class="position-badge p${i + 1}">${i + 1}</span></td>
            <td>
                <div class="driver-info">
                    <span class="driver-name">${p.username}</span>
                </div>
            </td>
            <td class="points">${p.total_points || 0}</td>
        </tr>
    `).join('');
    document.getElementById('topDriversTable').innerHTML = top5Html || '<tr><td colspan="3">Žádná data</td></tr>';
}

function updateDriversTable(players) {
    const tbody = document.getElementById('allDriversTable');
    tbody.innerHTML = players.map(p => `
        <tr>
            <td>${p.username}</td>
            <td>${p.team || '-'}</td>
            <td>${p.role}</td>
            <td>${p.total_points || 0}</td>
            <td>${(p.penalties && p.penalties.total_points) || 0}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="editDriver('${p.id}')"><i class="fa-solid fa-pen"></i></button>
            </td>
        </tr>
    `).join('');
}

// -- Interaction --
function setupEventListeners() {
    // Tabs
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabName = item.dataset.tab;

            // Switch Menu
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Switch Content
            document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');
            const tab = document.getElementById(tabName);
            if (tab) tab.style.display = 'block';

            // Update Title
            document.getElementById('pageTitle').textContent = item.textContent.trim();
        });
    });

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        window.location.href = '/auth/logout';
    });

    // Modal Close
    document.querySelector('.close-modal').addEventListener('click', () => {
        document.getElementById('editDriverModal').style.display = 'none';
    });

    // Form Submit
    document.getElementById('editDriverForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('editDriverId').value;
        const updates = {
            username: document.getElementById('editDriverName').value,
            penalties: {
                total_points: parseInt(document.getElementById('editDriverPenaltyPoints').value) || 0
            }
        };

        try {
            await fetch('/api/admin/save_player', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, ...updates })
            });
            document.getElementById('editDriverModal').style.display = 'none';
            loadDashboardData(); // Refresh
        } catch (err) {
            alert('Chyba při ukládání');
        }
    });

    // Search
    document.getElementById('driverSearch').addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#allDriversTable tr');
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    });
}

// Global functions for inline onclicks
window.editDriver = async (id) => {
    // Fetch fresh data
    const res = await fetch('/api/players');
    const players = await res.json();
    const player = players.find(p => p.id === id);

    if (player) {
        document.getElementById('editDriverId').value = player.id;
        document.getElementById('editDriverName').value = player.username;
        document.getElementById('editDriverPenaltyPoints').value = player.penalties ? player.penalties.total_points : 0;

        document.getElementById('editDriverModal').style.display = 'flex';
    }
};

window.exportData = () => {
    window.location.href = '/api/export/csv'; // Need backend for this or client side
};

// -- Add Driver Logic --
window.openAddDriverModal = () => {
    document.getElementById('addDriverModal').style.display = 'flex';
};

window.closeAddDriverModal = () => {
    document.getElementById('addDriverModal').style.display = 'none';
};

document.getElementById('addDriverForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        username: document.getElementById('addDriverName').value,
        team: document.getElementById('addDriverTeam').value,
        role: document.getElementById('addDriverRole').value
    };

    try {
        const res = await fetch('/api/admin/create_player', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            closeAddDriverModal();
            document.getElementById('addDriverForm').reset();
            loadDashboardData();
        } else {
            alert('Chyba při vytváření');
        }
    } catch (e) {
        alert('Chyba serveru');
    }
});
