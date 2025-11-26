// Admin page script

let currentUid = null;
let currentPwHash = null;
let isRootUser = false; // Track if current user is root
let allUsers = [];
let showDeleted = false;

// Dictionary management variables
let currentDictId = null;
let currentWordId = null;
let dicts = [];
let words = [];
let deleteMode = null; // 'dict' or 'word'
let deleteTargetId = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication first
    const isAuthenticated = await requireAuth();
    if (!isAuthenticated) return;
    
    currentUid = getCurrentUID();
    currentPwHash = getCurrentPWHash();
    
    // Check user access and role
    const adminAccessCheckResult = await checkAdminAccess();
    if (!adminAccessCheckResult) {
        showAlert('无效的访问权限', 'danger');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
        return;
    }
    
    // Setup event listeners
    const logoutBtn = document.getElementById('logoutBtn');
    logoutBtn.addEventListener('click', () => {
        if (confirm('确定要登出吗？')) {
            logout();
        }
    });
    
    // Only setup user management UI for root users
    if (isRootUser) {
        const showDeletedCheckbox = document.getElementById('showDeletedCheckbox');
        if (showDeletedCheckbox) {
            showDeletedCheckbox.addEventListener('change', (e) => {
                showDeleted = e.target.checked;
                loadUsers();
            });
        }
        
        // Setup user management modal listeners
        const resetPasswordForm = document.getElementById('resetPasswordForm');
        if (resetPasswordForm) {
            resetPasswordForm.addEventListener('submit', handleResetPassword);
        }
        const confirmBtn = document.getElementById('confirmBtn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', handleConfirmAction);
        }
        
        // Event delegation for server-rendered action buttons
        // document.addEventListener('click', (e) => {
        //     const resetBtn = e.target.closest('.action-btn-reset');
        //     if (resetBtn) {
        //         const uid = resetBtn.dataset.uid;
        //         const username = resetBtn.dataset.username || '';
        //         openResetPasswordModal(parseInt(uid), username);
        //         return;
        //     }

        //     const deleteBtn = e.target.closest('.action-btn-delete');
        //     if (deleteBtn) {
        //         const uid = deleteBtn.dataset.uid;
        //         const username = deleteBtn.dataset.username || '';
        //         openDeleteConfirm(parseInt(uid), username);
        //         return;
        //     }

        //     const restoreBtn = e.target.closest('.action-btn-restore');
        //     if (restoreBtn) {
        //         const uid = restoreBtn.dataset.uid;
        //         const username = restoreBtn.dataset.username || '';
        //         openRestoreConfirm(parseInt(uid), username);
        //         return;
        //     }
        // });
        
        // Load and render user table
        await loadUsers();
    } else {
        // Hide user management section for non-root users
        const userMgmtSection = document.getElementById('userManagementSection');
        if (userMgmtSection) {
            userMgmtSection.style.display = 'none';
        }
    }
    
    // Dictionary management listeners (available for all authenticated users)
    const createDictBtn = document.getElementById('createDictBtn');
    if (createDictBtn) createDictBtn.addEventListener('click', openCreateDictForm);
    const closeDictEditBtn = document.getElementById('closeDictEditBtn');
    if (closeDictEditBtn) closeDictEditBtn.addEventListener('click', closeDictEditSection);
    const saveDictBtn = document.getElementById('saveDictBtn');
    if (saveDictBtn) saveDictBtn.addEventListener('click', saveDict);
    const addWordBtn = document.getElementById('addWordBtn');
    if (addWordBtn) addWordBtn.addEventListener('click', openCreateWordModal);
    const saveWordBtn = document.getElementById('saveWordBtn');
    if (saveWordBtn) saveWordBtn.addEventListener('click', handleSaveWord);
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    if (downloadCsvBtn) downloadCsvBtn.addEventListener('click', downloadCsv);
    const uploadCsvBtn = document.getElementById('uploadCsvBtn');
    if (uploadCsvBtn) uploadCsvBtn.addEventListener('click', () => document.getElementById('csvFileInput').click());
    const csvFileInput = document.getElementById('csvFileInput');
    if (csvFileInput) csvFileInput.addEventListener('change', handleCsvFileSelect);
    const importCsvTextBtn = document.getElementById('importCsvTextBtn');
    if (importCsvTextBtn) importCsvTextBtn.addEventListener('click', importCsvText);
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) confirmDeleteBtn.addEventListener('click', handleConfirmDelete);
    
    // Load dictionaries
    await loadDicts();
});

// Check if current user has admin access and get user type
async function checkAdminAccess() {
    try {
        const response = await fetch('/api/admin/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                uid: currentUid,
                pwhash: currentPwHash
            })
        });
        
        const data = await response.json();
        if (data.success) {
            isRootUser = data.type === 'root';
            return true; // Any authenticated user can access
        }
        return false;
    } catch (error) {
        console.error('Admin check error:', error);
        return false;
    }
}

// Load users from server
async function loadUsers() {
    try {
        showLoading('usersTableBody');
        
        const response = await fetch(
            `/api/admin/users?uid=${currentUid}&pwhash=${currentPwHash}&include_deleted=${showDeleted}`,
            {
                method: 'GET'
            }
        );
        
        const data = await response.json();
        
        if (!data.success) {
            showAlert('加载用户失败: ' + (data.message || '未知错误'), 'danger');
            return;
        }
        
        allUsers = data.users || [];
        renderUserTable();
    } catch (error) {
        console.error('Load users error:', error);
        showAlert('加载用户失败，请重试', 'danger');
    } finally {
        clearLoading('usersTableBody');
    }
}

// Render user table
function renderUserTable() {
    const tbody = document.getElementById('usersTableBody');
    
    if (allUsers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center" style="padding: 2rem;">
                    没有用户信息
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = allUsers.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>${escapeHtml(user.username)}</td>
            <td>${escapeHtml(user.introduction || '-')}</td>
            <td>${user.rating}</td>
            <td>
                <span class="type-${user.type}">
                    ${user.type === 'root' ? 'root' : 'normal'}
                </span>
            </td>
            <td>
                <span class="status-${user.deleted ? 'deleted' : 'active'}">
                    ${user.deleted ? '已删除' : '正常'}
                </span>
            </td>
            <td>
                <div class="action-buttons">
                    ${!user.deleted ? `
                        <button class="action-btn action-btn-reset" onclick="openResetPasswordModal(${user.id}, '${escapeHtml(user.username)}')">
                            重置密码
                        </button>
                        ${user.id !== currentUid ? `
                            <button class="action-btn action-btn-delete" onclick="openDeleteConfirm(${user.id}, '${escapeHtml(user.username)}')">
                                删除
                            </button>
                        ` : ''}
                    ` : `
                        <button class="action-btn action-btn-restore" onclick="openRestoreConfirm(${user.id}, '${escapeHtml(user.username)}')">
                            恢复
                        </button>
                    `}
                </div>
            </td>
        </tr>
    `).join('');
}

// Modal Management Functions

// Reset Password Modal
let resetPasswordUserId = null;

function openResetPasswordModal(uid, username) {
    // Ensure uid is a valid integer
    const parsed = Number.isFinite(Number(uid)) ? parseInt(uid) : NaN;
    resetPasswordUserId = parsed;
    document.getElementById('resetUserId').value = Number.isFinite(parsed) ? parsed : '';
    document.getElementById('resetUsername').value = username;
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmNewPassword').value = '';
    clearError('newPasswordError');
    clearError('confirmNewPasswordError');
    clearError('resetPasswordAlert');
    document.getElementById('resetPasswordModal').classList.remove('hidden');
}

function closeResetPasswordModal() {
    document.getElementById('resetPasswordModal').classList.add('hidden');
    resetPasswordUserId = null;
}

async function handleResetPassword(e) {
    e.preventDefault();
    
    clearError('newPasswordError');
    clearError('confirmNewPasswordError');
    clearError('resetPasswordAlert');
    
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    
    // Validation
    let hasError = false;
    
    if (!validatePassword(newPassword)) {
        showError('newPasswordError', '密码至少需6字符');
        hasError = true;
    }
    
    if (newPassword !== confirmPassword) {
        showError('confirmNewPasswordError', '两次输入的密码不一致');
        hasError = true;
    }
    
    if (hasError) return;
    
    // Validate target id
    if (!Number.isFinite(resetPasswordUserId)) {
        showError('resetPasswordAlert', '无效的用户ID，操作已取消');
        return;
    }

    try {
        disableButton('resetPasswordForm');

        const response = await fetch(`/api/admin/user/${resetPasswordUserId}/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                uid: currentUid,
                pwhash: currentPwHash,
                new_password: newPassword
            })
        });

        const contentType = response.headers.get('content-type') || '';
        let data;
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const txt = await response.text();
            console.warn('Reset-password non-JSON response:', txt);
            showError('resetPasswordAlert', '服务器返回非JSON响应，请检查控制台');
            return;
        }

        if (data.success) {
            showAlert('密码重置成功', 'success');
            closeResetPasswordModal();
            await loadUsers();
        } else {
            showError('resetPasswordAlert', data.message || '重置失败');
        }
    } catch (error) {
        console.error('Reset password error:', error);
        showError('resetPasswordAlert', '重置失败，请重试');
    } finally {
        enableButton('resetPasswordForm');
    }
}

// Confirm Modal Functions
let confirmAction = null;
let confirmActionData = null;

function openDeleteConfirm(uid, username) {
    confirmAction = 'delete';
    confirmActionData = { uid, username };
    document.getElementById('confirmTitle').textContent = '删除用户';
    document.getElementById('confirmMessage').textContent = `确定要删除用户 "${username}" 吗？此操作不可撤销。`;
    document.getElementById('confirmModal').classList.remove('hidden');
}

function openRestoreConfirm(uid, username) {
    confirmAction = 'restore';
    confirmActionData = { uid, username };
    document.getElementById('confirmTitle').textContent = '恢复用户';
    document.getElementById('confirmMessage').textContent = `确定要恢复用户 "${username}" 吗？`;
    document.getElementById('confirmModal').classList.remove('hidden');
}

function closeConfirmModal() {
    document.getElementById('confirmModal').classList.add('hidden');
    confirmAction = null;
    confirmActionData = null;
}

async function handleConfirmAction() {
    if (!confirmAction || !confirmActionData) return;

    let { uid } = confirmActionData;
    uid = Number.isFinite(Number(uid)) ? parseInt(uid) : NaN;

    if (!Number.isFinite(uid)) {
        showAlert('无效的用户ID，操作已取消', 'danger');
        return;
    }

    try {
        const response = await fetch(
            `/api/admin/user/${uid}/${confirmAction === 'delete' ? 'delete' : 'restore'}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    uid: currentUid,
                    pwhash: currentPwHash
                })
            }
        );

        const contentType = response.headers.get('content-type') || '';
        let data;
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const txt = await response.text();
            console.warn('Confirm-action non-JSON response:', txt);
            showAlert('服务器返回非JSON响应，请检查控制台', 'danger');
            return;
        }

        if (data.success) {
            const action = confirmAction === 'delete' ? '删除' : '恢复';
            showAlert(`用户${action}成功`, 'success');
            closeConfirmModal();
            await loadUsers();
        } else {
            showAlert(data.message || `${confirmAction === 'delete' ? '删除' : '恢复'}失败`, 'danger');
        }
    } catch (error) {
        console.error('Confirm action error:', error);
        showAlert('操作失败，请重试', 'danger');
    }
}

// ============ Dictionary Management Functions ============

// Load dictionaries
async function loadDicts() {
    try {
        const response = await fetch(`/api/dicts?uid=${currentUid}&pwhash=${currentPwHash}`);
        const data = await response.json();

        if (!data.success) {
            showAlert('加载词典失败', 'danger');
            return;
        }

        dicts = data.dicts || [];
        renderDictList();
    } catch (error) {
        console.error('Load dicts error:', error);
        showAlert('加载词典失败，请重试', 'danger');
    }
}

// Render dictionary list
function renderDictList() {
    const container = document.getElementById('dictListContainer');

    if (dicts.length === 0) {
        container.innerHTML = '<div class="empty-state" style="text-align: center; padding: 2rem; color: #999;">还没有词典，点击"新建词典"创建一个</div>';
        return;
    }

    container.innerHTML = `
        <div class="dict-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem;">
            ${dicts.map(dict => `
                <div class="dict-card" style="background: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem;">
                        <h3 style="margin: 0; font-size: 1.1rem; overflow-x:auto; white-space:nowrap;">${escapeHtml(dict.dictname)}</h3>
                    </div>
                    <div style="padding: 1rem; color: #666;">
                        <p style="margin: 0.5rem 0; font-size: 0.95rem;">单词数: ${dict.word_count || 0}</p>
                    </div>
                    <div style="padding: 1rem; display: flex; gap: 0.5rem; border-top: 1px solid #e0e0e0;">
                        <button class="btn-small btn-primary" onclick="openDictEdit(${dict.id}, '${escapeHtml(dict.dictname)}')" style="flex: 1; padding: 0.5rem 1rem; font-size: 0.85rem; border: none; border-radius: 4px; cursor: pointer; background: #667eea; color: white;">编辑</button>
                        <button class="btn-small btn-danger" onclick="openDeleteDictConfirm(${dict.id}, '${escapeHtml(dict.dictname)}')" style="flex: 1; padding: 0.5rem 1rem; font-size: 0.85rem; border: none; border-radius: 4px; cursor: pointer; background: #e74c3c; color: white;">删除</button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Open create dict form
function openCreateDictForm() {
    currentDictId = null;
    document.getElementById('editDictTitle').textContent = '新建词典';
    document.getElementById('dictName').value = '';
    document.getElementById('dictEditSection').classList.remove('hidden');
    clearError('dictNameError');
}

// Open dict edit section
async function openDictEdit(dictId, dictName) {
    currentDictId = dictId;
    document.getElementById('editDictTitle').textContent = '编辑词典';
    document.getElementById('dictName').value = dictName;
    document.getElementById('dictEditSection').classList.remove('hidden');
    document.getElementById('csvTextarea').value = '';
    clearError('dictNameError');

    await loadWords();
}

// Close dict edit section
function closeDictEditSection() {
    document.getElementById('dictEditSection').classList.add('hidden');
    currentDictId = null;
}

// Save dict
async function saveDict() {
    clearError('dictNameError');
    const dictName = document.getElementById('dictName').value.trim();

    if (!dictName) {
        showError('dictNameError', '词典名称不能为空');
        return;
    }

    try {
        const method = currentDictId ? 'PUT' : 'POST';
        const url = currentDictId ? `/api/dict/${currentDictId}` : '/api/dict';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: currentUid,
                pwhash: currentPwHash,
                dictname: dictName
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert(currentDictId ? '词典已更新' : '词典已创建', 'success');
            if (!currentDictId) {
                currentDictId = data.dict_id;
                document.getElementById('editDictTitle').textContent = '编辑词典';
            }
            await loadDicts();
        } else {
            showAlert(data.message || '保存失败', 'danger');
        }
    } catch (error) {
        console.error('Save dict error:', error);
        showAlert('保存失败，请重试', 'danger');
    }
}

// Load words
async function loadWords() {
    if (!currentDictId) return;

    try {
        const response = await fetch(`/api/dict/${currentDictId}/words?uid=${currentUid}&pwhash=${currentPwHash}`);
        const data = await response.json();

        if (!data.success) {
            showAlert('加载单词失败', 'danger');
            return;
        }

        words = data.words || [];
        renderWordTable();
    } catch (error) {
        console.error('Load words error:', error);
        showAlert('加载单词失败，请重试', 'danger');
    }
}

// Render words table
function renderWordTable() {
    const tbody = document.getElementById('wordsTableBody');

    if (words.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center" style="padding: 2rem;">暂无单词</td></tr>';
        return;
    }

    tbody.innerHTML = words.map((word, index) => `
        <tr>
            <td>${word.id}</td>
            <td>${index + 1}</td>
            <td>${escapeHtml(word.english)}</td>
            <td>${escapeHtml(word.chinese)}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn action-btn-primary" onclick="openEditWordModal(${word.id}, '${escapeHtml(word.english)}', '${escapeHtml(word.chinese)}')">编辑</button>
                    <button class="action-btn action-btn-delete" onclick="openDeleteWordConfirm(${word.id}, '${escapeHtml(word.english)}')">删除</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Open create word modal
function openCreateWordModal() {
    if (!currentDictId) {
        showAlert('请先选择或创建词典', 'danger');
        return;
    }

    currentWordId = null;
    document.getElementById('wordModalTitle').textContent = '新增单词';
    document.getElementById('wordEnglish').value = '';
    document.getElementById('wordChinese').value = '';
    clearError('wordEnglishError');
    clearError('wordChineseError');
    clearError('wordModalError');
    document.getElementById('wordModal').classList.remove('hidden');
}

// Open edit word modal
function openEditWordModal(wordId, english, chinese) {
    currentWordId = wordId;
    document.getElementById('wordModalTitle').textContent = '编辑单词';
    document.getElementById('wordEnglish').value = english;
    document.getElementById('wordChinese').value = chinese;
    clearError('wordEnglishError');
    clearError('wordChineseError');
    clearError('wordModalError');
    document.getElementById('wordModal').classList.remove('hidden');
}

// Close word modal
function closeWordModal() {
    document.getElementById('wordModal').classList.add('hidden');
    currentWordId = null;
}

// Handle save word
async function handleSaveWord() {
    clearError('wordEnglishError');
    clearError('wordChineseError');
    clearError('wordModalError');

    const english = document.getElementById('wordEnglish').value.trim();
    const chinese = document.getElementById('wordChinese').value.trim();

    if (!english) {
        showError('wordEnglishError', 'English不能为空');
        return;
    }
    if (!chinese) {
        showError('wordChineseError', '中文不能为空');
        return;
    }

    try {
        const method = currentWordId ? 'PUT' : 'POST';
        const url = currentWordId ? `/api/word/${currentWordId}` : `/api/dict/${currentDictId}/word`;

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: currentUid,
                pwhash: currentPwHash,
                english: english,
                chinese: chinese
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert(currentWordId ? '单词已更新' : '单词已添加', 'success');
            closeWordModal();
            await loadWords();
        } else {
            showError('wordModalError', data.message || '保存失败');
        }
    } catch (error) {
        console.error('Save word error:', error);
        showError('wordModalError', '保存失败，请重试');
    }
}

// Download CSV
async function downloadCsv() {
    if (!currentDictId) {
        showAlert('请先选择词典', 'danger');
        return;
    }

    try {
        const response = await fetch(`/api/dict/${currentDictId}/export-csv?uid=${currentUid}&pwhash=${currentPwHash}`);
        const data = await response.json();

        if (data.success) {
            const element = document.createElement('a');
            element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(data.content));
            element.setAttribute('download', data.filename);
            element.style.display = 'none';
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
            showAlert('CSV已下载', 'success');
        } else {
            showAlert(data.message || '导出失败', 'danger');
        }
    } catch (error) {
        console.error('Download CSV error:', error);
        showAlert('导出失败，请重试', 'danger');
    }
}

// Handle CSV file select
function handleCsvFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        document.getElementById('csvTextarea').value = event.target.result;
    };
    reader.readAsText(file);
}

// Import CSV text
async function importCsvText() {
    if (!currentDictId) {
        showAlert('请先选择词典', 'danger');
        return;
    }

    const csvContent = document.getElementById('csvTextarea').value.trim();
    if (!csvContent) {
        showAlert('请输入CSV内容', 'danger');
        return;
    }

    try {
        const response = await fetch(`/api/dict/${currentDictId}/import-csv`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: currentUid,
                pwhash: currentPwHash,
                csv: csvContent
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert(`成功导入 ${data.count} 个单词`, 'success');
            document.getElementById('csvTextarea').value = '';
            await loadWords();
        } else {
            showAlert(data.message || '导入失败', 'danger');
        }
    } catch (error) {
        console.error('Import CSV error:', error);
        showAlert('导入失败，请重试', 'danger');
    }
}

// Open delete dict confirm
function openDeleteDictConfirm(dictId, dictName) {
    deleteMode = 'dict';
    deleteTargetId = dictId;
    document.getElementById('confirmDeleteMessage').textContent = `确定要删除词典 "${dictName}" 吗？其中所有单词也将被删除，此操作不可撤销。`;
    document.getElementById('confirmDeleteModal').classList.remove('hidden');
}

// Open delete word confirm
function openDeleteWordConfirm(wordId, english) {
    deleteMode = 'word';
    deleteTargetId = wordId;
    document.getElementById('confirmDeleteMessage').textContent = `确定要删除单词 "${english}" 吗？`;
    document.getElementById('confirmDeleteModal').classList.remove('hidden');
}

// Close confirm delete modal
function closeConfirmDeleteModal() {
    document.getElementById('confirmDeleteModal').classList.add('hidden');
    deleteMode = null;
    deleteTargetId = null;
}

// Handle confirm delete
async function handleConfirmDelete() {
    if (!deleteMode || !deleteTargetId) return;

    try {
        const url = deleteMode === 'dict'
            ? `/api/dict/${deleteTargetId}`
            : `/api/word/${deleteTargetId}`;

        const response = await fetch(url, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: currentUid,
                pwhash: currentPwHash
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert(deleteMode === 'dict' ? '词典已删除' : '单词已删除', 'success');
            closeConfirmDeleteModal();

            if (deleteMode === 'dict') {
                await loadDicts();
                closeDictEditSection();
            } else {
                await loadWords();
            }
        } else {
            showAlert(data.message || '删除失败', 'danger');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showAlert('删除失败，请重试', 'danger');
    }
}
