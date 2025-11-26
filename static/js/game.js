// Game management functions

// Game status tracking
let currentGameTab = 'pending'; // pending, running, finished
let allGames = [];
let AUTH_DATA = {};

// Initialize game page
document.addEventListener('DOMContentLoaded', async () => {
    // Get auth from cookies
    const auth = getAuthCookies();
    if (!auth.uid || !auth.pwhash) {
        window.location.href = '/login/';
        return;
    }
    AUTH_DATA = { uid: parseInt(auth.uid), pwhash: auth.pwhash };

    loadGames();
    setupEventListeners();

    // Auto-refresh games every 2 seconds
    setInterval(loadGames, 2000);
});

function setupEventListeners() {
    // Tab buttons
    const tabButtons = document.querySelectorAll('.games-tab');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentGameTab = btn.dataset.tab;
            renderGames();
        });
    });

    // Create game button
    const createGameBtn = document.getElementById('createGameBtn');
    if (createGameBtn) {
        createGameBtn.addEventListener('click', showCreateGameModal);
    }
}

async function loadGames() {
    try {
        const response = await fetch(`/api/game/list?uid=${AUTH_DATA.uid}&pwhash=${AUTH_DATA.pwhash}`);
        if (!response.ok) {
            console.error('Failed to load games:', response.status);
            return;
        }

        const data = await response.json();
        if (data.success) {
            allGames = data.games;

            // If any joined game has just started, redirect the joined users immediately (only from homepage)
            try {
                const locationPath = window.location.pathname;
                if (locationPath === '/') {
                    const myRunning = allGames.find(g => g.is_joined && g.status === 0);
                    if (myRunning) {
                        window.location.href = `/game/${myRunning.id}/`;
                        return;
                    }
                }
            } catch (e) {
                // ignore and continue
            }

            renderGames();
        }
    } catch (error) {
        console.error('Error loading games:', error);
    }
}

function renderGames() {
    const gamesList = document.getElementById('gamesList');
    if (!gamesList) return;

    // Filter games by status
    let filteredGames = [];
    if (currentGameTab === 'pending') {
        filteredGames = allGames.filter(g => g.status === -1);
    } else if (currentGameTab === 'running') {
        filteredGames = allGames.filter(g => g.status === 0);
    } else if (currentGameTab === 'finished') {
        filteredGames = allGames.filter(g => g.status === 1);
    }

    if (filteredGames.length === 0) {
        gamesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">
                    ${currentGameTab === 'pending' ? '暂无待开始对局' : currentGameTab === 'running' ? '暂无进行中的对局' : '暂无历史对局'}
                </div>
            </div>
        `;
        return;
    }

    gamesList.innerHTML = filteredGames.map(game => renderGameCard(game)).join('');

    // Attach event listeners to action buttons
    gamesList.querySelectorAll('.btn-join').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const gameId = parseInt(e.target.dataset.gameId);
            joinGame(gameId);
        });
    });

    gamesList.querySelectorAll('.btn-leave').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const gameId = parseInt(e.target.dataset.gameId);
            leaveGame(gameId);
        });
    });

    gamesList.querySelectorAll('.btn-start').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const gameId = parseInt(e.target.dataset.gameId);
            startGame(gameId);
        });
    });

    gamesList.querySelectorAll('.btn-watch').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const gameId = parseInt(e.target.dataset.gameId);
            watchGame(gameId);
        });
    });

    gamesList.querySelectorAll('.btn-history').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const gameId = parseInt(e.target.dataset.gameId);
            viewGameDetail(gameId);
        });
    });
}

function renderGameCard(game) {
    const statusNum = game.status;
    const statusMap = { '-1': 'pending', '0': 'running', '1': 'finished' };
    const statusText = statusNum === -1 ? '待开始' : (statusNum === 0 ? '进行中' : '已结束');
    const statusBadge = `<span class="game-status-badge status-${statusMap[statusNum]}">${statusText}</span>`;

    const users = game.users || [];
    const usersList = users.map((user, idx) => {
        const userName = user.username || `User ${user.id}`;
        return `<span class="user-badge">${idx + 1}. ${userName}</span>`;
    }).join('');

    const isJoined = game.is_joined;
    const canJoin = statusNum === -1 && !isJoined;
    const isOwner = game.owner && game.owner.id === AUTH_DATA.uid;
    const canLeave = statusNum === -1 && isJoined && !isOwner;
    const canStart = statusNum === -1 && isJoined && users.length >= 2;
    const canWatch = statusNum === 0;
    const canViewHistory = statusNum === 1;

    let actions = '';
    if (canJoin) {
        actions += `<button class="game-btn btn-join" data-game-id="${game.id}">报名</button>`;
    }
    if (canLeave) {
        actions += `<button class="game-btn btn-leave" data-game-id="${game.id}">撤销报名</button>`;
    }
    if (canStart) {
        actions += `<button class="game-btn btn-start" data-game-id="${game.id}">开始</button>`;
    }
    if (canWatch) {
        actions += `<button class="game-btn btn-watch" data-game-id="${game.id}">观战</button>`;
    }
    if (canViewHistory) {
        actions += `<button class="game-btn btn-history" data-game-id="${game.id}">详情</button>`;
    }

    return `
        <div class="game-card">
            <div class="game-card-header">
                <h3 class="game-card-title">对局 #${game.id}</h3>
                ${statusBadge}
            </div>
            <div class="game-card-info">
                <div class="game-card-info-item">
                    <span class="game-card-info-label">词典：</span>
                    <span>${game.dictname || '未知'}</span>
                </div>
                <div class="game-card-info-item">
                    <span class="game-card-info-label">参赛者：</span>
                    <span>${users.length} 人</span>
                </div>
            </div>
            <div class="game-card-users">
                <div class="game-card-users-label">参赛者列表：</div>
                <div class="game-users-list">${usersList}</div>
            </div>
            <div class="game-card-actions">
                ${actions}
            </div>
        </div>
    `;
}

async function joinGame(gameId) {
    try {
        const response = await fetch(`/api/game/${gameId}/join`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: AUTH_DATA.uid,
                pwhash: AUTH_DATA.pwhash
            })
        });

        const data = await response.json();
        if (data.success) {
            alert('成功加入对局！');
            loadGames();
        } else {
            alert(data.message || '加入失败');
        }
    } catch (error) {
        console.error('Error joining game:', error);
        alert('加入对局出错');
    }
}

async function leaveGame(gameId) {
    if (!confirm('确定要撤销报名吗？')) return;

    try {
        const response = await fetch(`/api/game/${gameId}/leave`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: AUTH_DATA.uid,
                pwhash: AUTH_DATA.pwhash
            })
        });

        const data = await response.json();
        if (data.success) {
            alert('成功撤销报名！');
            loadGames();
        } else {
            alert(data.message || '撤销报名失败');
        }
    } catch (error) {
        console.error('Error leaving game:', error);
        alert('撤销报名出错');
    }
}

async function startGame(gameId) {
    if (!confirm('确定要开始对局吗？')) return;

    try {
        const response = await fetch(`/api/game/${gameId}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: AUTH_DATA.uid,
                pwhash: AUTH_DATA.pwhash
            })
        });

        const data = await response.json();
        if (data.success) {
            alert('对局已开始！');
            window.location.href = `/game/${gameId}/`;
        } else {
            alert(data.message || '开始对局失败');
        }
    } catch (error) {
        console.error('Error starting game:', error);
        alert('开始对局出错');
    }
}

function watchGame(gameId) {
    // Open game playing/watching page
    window.location.href = `/game/${gameId}/`;
}

function viewGameDetail(gameId) {
    window.location.href = `/game/${gameId}/detail/`;
}

function showCreateGameModal() {
    // Fetch available dictionaries
    fetchDictionaries().then(dicts => {
        const modal = createModal('createGameModal', '创建新对局');
        const modalBody = modal.querySelector('.modal-body');

        const dictOptions = dicts.map(dict => `<option value="${dict.id}">${dict.dictname}</option>`).join('');
        console.log(dictOptions)
        modalBody.innerHTML = `
            <div class="form-group-modal">
                <label for="createGameDict">选择词典</label>
                <select id="createGameDict">
                    <option value="">-- 选择词典 --</option>
                    ${dictOptions}
                </select>
            </div>
        `;

        const modalFooter = modal.querySelector('.modal-footer');
        modalFooter.innerHTML = `
            <button class="btn-secondary" onclick="closeModal('createGameModal')">取消</button>
            <button class="btn-primary" id="confirmCreateGameBtn">创建</button>
        `;

        document.getElementById('confirmCreateGameBtn').addEventListener('click', async () => {
            const dictId = parseInt(document.getElementById('createGameDict').value);
            if (!dictId) {
                alert('请选择词典');
                return;
            }

            try {
                const response = await fetch('/api/game/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        uid: AUTH_DATA.uid,
                        pwhash: AUTH_DATA.pwhash,
                        dict_id: dictId
                    })
                });

                const data = await response.json();
                if (data.success) {
                    alert(`对局已创建！对局ID: ${data.game_id}`);
                    closeModal('createGameModal');
                    loadGames();
                } else {
                    alert(data.message || '创建对局失败');
                }
            } catch (error) {
                console.error('Error creating game:', error);
                alert('创建对局出错');
            }
        });

        showModal('createGameModal');
    });
}

async function fetchDictionaries() {
    try {
        const response = await fetch(`/api/dicts?uid=${AUTH_DATA.uid}&pwhash=${AUTH_DATA.pwhash}`);
        if (!response.ok) return [];

        const data = await response.json();
        return data.success ? data.dicts : [];
    } catch (error) {
        console.error('Error fetching dictionaries:', error);
        return [];
    }
}

// Modal utilities (reuse from admin.js if possible)
function createModal(id, title) {
    const modal = document.createElement('div');
    modal.id = id;
    modal.className = 'modal hidden';
    modal.innerHTML = `
        <div class="modal-overlay"></div>
        <div class="modal-content modal-small">
            <div class="modal-header">
                <h3>${title}</h3>
                <button class="modal-close" onclick="closeModal('${id}')">×</button>
            </div>
            <div class="modal-body"></div>
            <div class="modal-footer"></div>
        </div>
    `;
    document.body.appendChild(modal);
    return modal;
}

function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('hidden');
        modal.remove();
    }
}

// Fetch user names for display
async function fetchUserName(userId) {
    try {
        const response = await fetch(`/api/user/${userId}?uid=${AUTH_DATA.uid}&pwhash=${AUTH_DATA.pwhash}`);
        if (!response.ok) return `User ${userId}`;

        const data = await response.json();
        return data.success ? data.user.username : `User ${userId}`;
    } catch (error) {
        console.error('Error fetching user:', error);
        return `User ${userId}`;
    }
}
