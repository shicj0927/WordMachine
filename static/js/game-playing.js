// Game Playing page logic

let gameId = null;
let currentGameData = null;
let currentWordIndex = 0;
let userAnswers = [];
let userScores = {};
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
    const pathMatch = window.location.pathname.match(/\/game\/(\d+)\/$/);
    if (pathMatch) {
        gameId = parseInt(pathMatch[1]);
        loadGameAndStart();
    }
});

async function loadGameAndStart() {
    try {
        const response = await fetch(`/api/game/${gameId}?uid=${AUTH_DATA.uid}&pwhash=${AUTH_DATA.pwhash}`);
        if (!response.ok) {
            showError('无法加载对局信息');
            return;
        }

        const data = await response.json();
        if (data.success) {
                currentGameData = data.game;
                // sync current index from server
                currentWordIndex = data.game.current_index || 0;
                initializeScores();
                displayCurrentWord();
            updateParticipantsList();
            autoRefresh();
        } else {
            showError(data.message || '加载对局失败');
        }
    } catch (error) {
        console.error('Error loading game:', error);
        showError('加载对局出错');
    }
}

function initializeScores() {
    const users = currentGameData.users || [];
    users.forEach(user => {
        userScores[user.id] = { correct: 0, wrong: 0, perf: 0 };
    });

    // Count existing results
    const results = currentGameData.result || [];
    results.forEach(result => {
        if (userScores[result.uid]) {
            if (result.result) {
                userScores[result.uid].correct++;
                userScores[result.uid].perf++;
            } else {
                userScores[result.uid].wrong++;
                userScores[result.uid].perf--;
            }
        }
    });

    updateMyScore();
}

function displayCurrentWord() {
    if (!currentGameData) return;

    // If server provides next_word, use it; otherwise fall back to words list
    const nextWord = currentGameData.next_word || (currentGameData.words ? currentGameData.words[currentWordIndex] : null);

    // Check if all words are answered
    if (!nextWord) {
        showGameComplete();
        return;
    }
    const currentWord = nextWord;

    const total = currentGameData.words ? currentGameData.words.length : (currentGameData.wordlist ? currentGameData.wordlist.length : 0);
    document.getElementById('progressText').textContent = `第 ${currentWordIndex + 1} / ${total} 题`;

    // Show Chinese prompt as main question (users must input English)
    document.getElementById('wordDisplay').textContent = currentWord.chinese || '-';
    document.getElementById('wordChinese').textContent = `(请填写对应的英文)`;

    // Show current turn information
    const turnInfoEl = document.getElementById('turnInfo');
    if (currentGameData.next_turn) {
        const isMyTurn = currentGameData.next_turn === AUTH_DATA.uid;
        let turnText = '你';
        if (!isMyTurn) {
            const turnUser = (currentGameData.users || []).find(u => u.id === currentGameData.next_turn);
            turnText = turnUser ? turnUser.username : ('用户 #' + currentGameData.next_turn);
        }
        turnInfoEl.textContent = `当前轮次：${turnText}`;
        // Disable input if not my turn
        document.getElementById('answerInput').disabled = !isMyTurn;
        document.getElementById('submitBtn').disabled = !isMyTurn;
    } else {
        turnInfoEl.textContent = '';
        document.getElementById('answerInput').disabled = false;
        document.getElementById('submitBtn').disabled = false;
    }
    
    // Clear answer input
    const answerInput = document.getElementById('answerInput');
    answerInput.value = '';
    answerInput.focus();
    
    updateResultsDisplay();
}

async function submitAnswer(event) {
    event.preventDefault();

    if (!currentGameData || !currentGameData.words) return;
    
    // Use server-provided expected word id to avoid mismatch
    const nextWord = currentGameData.next_word;
    const expectedWordId = nextWord ? nextWord.id : (currentGameData.words ? currentGameData.words[currentWordIndex].id : null);
    const answer = document.getElementById('answerInput').value.trim();

    if (!answer) return;

    // Disable submit button during processing
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;

    try {
        const response = await fetch(`/api/game/${gameId}/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                uid: AUTH_DATA.uid,
                pwhash: AUTH_DATA.pwhash,
                word_id: expectedWordId,
                answer: answer
            })
        });

        const data = await response.json();
        if (data.success) {
            // Record the answer
            userAnswers.push({
                word_id: expectedWordId,
                answer: answer,
                correct: data.correct
            });

            // Update scores
            if (data.correct) {
                userScores[AUTH_DATA.uid].correct++;
                userScores[AUTH_DATA.uid].perf++;
            } else {
                userScores[AUTH_DATA.uid].wrong++;
                userScores[AUTH_DATA.uid].perf--;
            }

            updateMyScore();

            // Move to next word (sync with server index if provided)
            currentWordIndex = (data.next_word && data.next_word.id) ? currentWordIndex + 1 : currentWordIndex + 1;
            // fetch latest game state to sync next_turn/next_word
            setTimeout(async () => {
                submitBtn.disabled = false;
                await refreshGameOnce();
                displayCurrentWord();
            }, 300);
        } else {
            alert(data.message || '提交答案失败');
            submitBtn.disabled = false;
        }
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('提交答案出错');
        submitBtn.disabled = false;
    }
}

function updateMyScore() {
    const myScore = userScores[AUTH_DATA.uid] || { correct: 0, wrong: 0, perf: 0 };
    document.getElementById('myCorrect').textContent = myScore.correct;
    document.getElementById('myWrong').textContent = myScore.wrong;
    document.getElementById('myPerf').textContent = myScore.perf > 0 ? '+' + myScore.perf : myScore.perf;
}

function updateResultsDisplay() {
    const container = document.getElementById('resultsContainer');

    if (!currentGameData || !currentGameData.result || currentGameData.result.length === 0) {
        container.innerHTML = '';
        return;
    }

    // Show last 10 global answers (most recent first)
    const recent = currentGameData.result.slice(-10).reverse();

    const html = recent.map(item => {
        const uid = item.uid;
        const word = (currentGameData.words || []).find(w => w.id === item.word_id) || {english: '未知', chinese: ''};
        const userObj = (currentGameData.users || []).find(u => u.id === uid) || {id: uid, username: 'User ' + uid};
        const isMe = uid === AUTH_DATA.uid;
        const nameLabel = isMe ? `${userObj.username} (你)` : userObj.username;
        const resultClass = item.result ? 'result-correct' : 'result-wrong';
        const resultText = item.result ? '✓ 正确' : '✗ 错误';

        return `
            <div class="result-item ${resultClass}">
                <div style="flex:1">
                    <div style="font-size:0.95rem; color:var(--text-secondary); margin-bottom:0.25rem;">${nameLabel}</div>
                    <div><span class="result-word">${word.chinese} → ${word.english}</span></div>
                    <div style="margin-top:0.25rem">回答：<strong>${item.answer}</strong></div>
                </div>
                <div style="margin-left:1rem">${resultText}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = `<h3 style="margin-top: 0; font-size: 1rem; color: var(--text-primary);">最近答题</h3>${html}`;
}

function updateParticipantsList() {
    const container = document.getElementById('participantsList');
    const users = currentGameData.users || [];

    const html = users.map(user => {
        const score = userScores[user.id] || { correct: 0, wrong: 0, perf: 0 };
        const isCurrent = user.id === AUTH_DATA.uid ? ' (你)' : '';
        return `
            <li>
                <strong>${user.username}${isCurrent}</strong><br>
                <span style="font-size: 0.8rem; color: var(--text-secondary);">
                    ✓${score.correct} ✗${score.wrong} ${score.perf > 0 ? '+' + score.perf : score.perf}
                </span>
            </li>
        `;
    }).join('');

    container.innerHTML = html;
}

function showGameComplete() {
    const main = document.querySelector('.game-playing-main');
    main.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <h2 style="color: var(--success-color); margin-bottom: 1rem;">🎉 所有题目已完成！</h2>
            <p style="font-size: 1rem; color: var(--text-secondary); margin-bottom: 2rem;">
                等待对局其他参赛者完成或点击"结束对局"结束本场游戏。
            </p>
            <button class="end-game-btn" onclick="endGame()" style="max-width: 300px; margin: 0 auto;">结束对局</button>
        </div>
    `;
}

async function endGame() {
    if (!confirm('确定要结束对局吗？')) return;

    try {
        const response = await fetch(`/api/game/${gameId}/end`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: AUTH_DATA.uid,
                pwhash: AUTH_DATA.pwhash
            })
        });

        const data = await response.json();
        if (data.success) {
            alert('对局已结束！');
            window.location.href = `/game/${gameId}/detail/`;
        } else {
            alert(data.message || '结束对局失败');
        }
    } catch (error) {
        console.error('Error ending game:', error);
        alert('结束对局出错');
    }
}

function autoRefresh() {
    // Refresh game data every 5 seconds to sync with other players
    setInterval(async () => {
        try {
            const response = await fetch(`/api/game/${gameId}?uid=${AUTH_DATA.uid}&pwhash=${AUTH_DATA.pwhash}`);
            if (!response.ok) return;

            const data = await response.json();
            if (data.success) {
                const newResults = data.game.result || [];

                // Update participant scores and UI if game has changed
                if (!currentGameData || newResults.length !== (currentGameData.result || []).length || data.game.current_index !== currentWordIndex) {
                    currentGameData = data.game;
                    currentWordIndex = data.game.current_index || 0;
                    initializeScores();
                    updateParticipantsList();
                    displayCurrentWord();
                }
            }
        } catch (error) {
            // Silent fail for auto-refresh
        }
    }, 5000);
}

async function refreshGameOnce() {
    try {
        const response = await fetch(`/api/game/${gameId}?uid=${AUTH_DATA.uid}&pwhash=${AUTH_DATA.pwhash}`);
        if (!response.ok) return;
        const data = await response.json();
        if (data.success) {
            currentGameData = data.game;
            currentWordIndex = data.game.current_index || 0;
            initializeScores();
            updateParticipantsList();
        }
    } catch (e) {
        // ignore
    }
}

function showError(message) {
    const main = document.querySelector('.game-playing-main');
    main.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <h2 style="color: var(--danger-color);">加载失败</h2>
            <p style="color: var(--text-secondary);">${message}</p>
            <a href="/" class="btn-primary" style="display: inline-block; padding: 0.75rem 1.5rem; background-color: var(--primary-color); color: white; border-radius: 0.5rem; text-decoration: none;">返回首页</a>
        </div>
    `;
}
