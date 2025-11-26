// Game Detail page logic

let gameId = null;
let AUTH_DATA = {};

// Extract game ID from URL
document.addEventListener('DOMContentLoaded', () => {
    // Get auth from cookies
    const auth = getAuthCookies();
    if (!auth.uid || !auth.pwhash) {
        window.location.href = '/login/';
        return;
    }
    AUTH_DATA = { uid: parseInt(auth.uid), pwhash: auth.pwhash };

    // Get game ID from URL path
    const pathMatch = window.location.pathname.match(/\/game\/(\d+)\/detail\//);
    if (pathMatch) {
        gameId = parseInt(pathMatch[1]);
        loadGameDetail(gameId);
    }
});

async function loadGameDetail(gameId) {
    try {
        const response = await fetch(`/api/game/${gameId}?uid=${AUTH_DATA.uid}&pwhash=${AUTH_DATA.pwhash}`);
        if (!response.ok) {
            console.error('Failed to load game:', response.status);
            showError('无法加载对局信息');
            return;
        }

        const data = await response.json();
        if (data.success) {
            const game = data.game;
            renderGameDetail(game);
        } else {
            showError(data.message || '加载对局失败');
        }
    } catch (error) {
        console.error('Error loading game detail:', error);
        showError('加载对局出错');
    }
}

function renderGameDetail(game) {
    // Update page title
    document.getElementById('pageTitle').textContent = `对局 #${game.id} 详情`;

    // Render game summary
    renderGameSummary(game);

    // Render perf summary
    renderPerfSummary(game);

    // Render results table
    renderResultsTable(game);
}

function renderGameSummary(game) {
    const container = document.getElementById('gameSummary');
    const users = (game.users || []).map(u => u.username).join(', ');
    
    container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div>
                <strong>词典：</strong>
                <div>${game.dictname || '未知'}</div>
            </div>
            <div>
                <strong>参赛者数：</strong>
                <div>${game.users.length} 人</div>
            </div>
            <div>
                <strong>总题目数：</strong>
                <div>${game.words.length} 题</div>
            </div>
            <div>
                <strong>已答题数：</strong>
                <div>${game.result.length} 题</div>
            </div>
            <div>
                <strong>状态：</strong>
                <div>${game.status === 0 ? '进行中' : (game.status === 1 ? '已结束' : '待开始')}</div>
            </div>
        </div>
        <div style="margin-top: 1rem;">
            <strong>参赛者：</strong>
            <div>${users}</div>
        </div>
    `;
}

function renderPerfSummary(game) {
    const container = document.getElementById('perfSummary');
    const perfData = game.perf || {};

    const perfRows = Object.entries(perfData).map(([userId, perf]) => {
        const user = game.users.find(u => u.id == userId);
        const userName = user ? user.username : `User ${userId}`;
        const perfClass = perf.perf > 0 ? 'status-active' : (perf.perf < 0 ? 'status-deleted' : '');
        const perfSign = perf.perf > 0 ? '+' : '';

        return `
            <tr>
                <td>${userName}</td>
                <td style="text-align: center;">${perf.correct}</td>
                <td style="text-align: center;">${perf.wrong}</td>
                <td style="text-align: center; class="${perfClass}"><strong>${perfSign}${perf.perf}</strong></td>
            </tr>
        `;
    }).join('');

    container.innerHTML = `
        <div class="table-container">
            <table class="users-table">
                <thead>
                    <tr>
                        <th>用户</th>
                        <th style="text-align: center;">正确</th>
                        <th style="text-align: center;">错误</th>
                        <th style="text-align: center;">Perf变更</th>
                    </tr>
                </thead>
                <tbody>
                    ${perfRows}
                </tbody>
            </table>
        </div>
    `;
}

function renderResultsTable(game) {
    const tbody = document.getElementById('resultTable');
    const words = game.words || [];
    const results = game.result || [];

    if (results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 1.5rem;">暂无答题记录</td></tr>';
        return;
    }

    const rows = results.map((result, idx) => {
        const user = game.users.find(u => u.id == result.uid);
        const userName = user ? user.username : `User ${result.uid}`;
        
        const word = words.find(w => w.id == result.word_id);
        const wordText = word ? `${word.english} → ${word.chinese}` : '未知单词';
        
        const resultClass = result.result ? 'status-active' : 'status-deleted';
        const resultText = result.result ? '✓ 正确' : '✗ 错误';

        return `
            <tr>
                <td>${idx + 1}</td>
                <td>${userName}</td>
                <td>${wordText}</td>
                <td>${result.answer}</td>
                <td>${word ? word.english : '未知'}</td>
                <td class="${resultClass}"><strong>${resultText}</strong></td>
            </tr>
        `;
    }).join('');

    tbody.innerHTML = rows;
}

function showError(message) {
    document.getElementById('gameSummary').innerHTML = `<div class="alert alert-danger">${message}</div>`;
    document.getElementById('perfSummary').innerHTML = '';
    document.getElementById('resultTable').innerHTML = '';
}
