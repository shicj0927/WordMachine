// Dictionary Admin Page Script

let currentUid = null;
let currentPwHash = null;
let currentDictId = null;
let currentWordId = null;
let dicts = [];
let words = [];
let deleteMode = null; // 'dict' or 'word'
let deleteTargetId = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const isAuthenticated = await requireAuth();
    if (!isAuthenticated) return;

    currentUid = getCurrentUID();
    currentPwHash = getCurrentPWHash();

    // Check admin access (root required)
    try {
        const response = await fetch('/api/admin/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uid: currentUid, pwhash: currentPwHash })
        });
        const data = await response.json();
        if (!data.success) {
            showAlert('您需要管理员权限', 'danger');
            setTimeout(() => window.location.href = '/', 2000);
            return;
        }
    } catch (error) {
        console.error('Admin check error:', error);
        showAlert('权限检查失败', 'danger');
        return;
    }

    // Setup UI listeners
    document.getElementById('logoutBtn').addEventListener('click', () => {
        if (confirm('确定要登出吗？')) logout();
    });
    document.getElementById('createDictBtn').addEventListener('click', openCreateDictForm);
    document.getElementById('closeDictEditBtn').addEventListener('click', closeDictEditSection);
    document.getElementById('saveDictBtn').addEventListener('click', saveDict);
    document.getElementById('addWordBtn').addEventListener('click', openCreateWordModal);
    document.getElementById('saveWordBtn').addEventListener('click', handleSaveWord);
    document.getElementById('downloadCsvBtn').addEventListener('click', downloadCsv);
    document.getElementById('uploadCsvBtn').addEventListener('click', () => document.getElementById('csvFileInput').click());
    document.getElementById('csvFileInput').addEventListener('change', handleCsvFileSelect);
    document.getElementById('importCsvTextBtn').addEventListener('click', importCsvText);
    document.getElementById('confirmDeleteBtn').addEventListener('click', handleConfirmDelete);

    // Load dicts
    await loadDicts();
});

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
        container.innerHTML = '<div class="empty-state">还没有词典，点击"新建词典"创建一个</div>';
        return;
    }

    container.innerHTML = `
        <div class="dict-grid">
            ${dicts.map(dict => `
                <div class="dict-card">
                    <div class="dict-card-header">
                        <h3>${escapeHtml(dict.dictname)}</h3>
                    </div>
                    <div class="dict-card-body">
                        <p>单词数: ${dict.word_count || 0}</p>
                    </div>
                    <div class="dict-card-footer">
                        <button class="btn-small btn-primary" onclick="openDictEdit(${dict.id}, '${escapeHtml(dict.dictname)}')">编辑</button>
                        <button class="btn-small btn-danger" onclick="openDeleteDictConfirm(${dict.id}, '${escapeHtml(dict.dictname)}')">删除</button>
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
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">暂无单词</td></tr>';
        return;
    }

    tbody.innerHTML = words.map(word => `
        <tr>
            <td>${word.id}</td>
            <td>${escapeHtml(word.english)}</td>
            <td>${escapeHtml(word.chinese)}</td>
            <td>
                <button class="btn-small btn-primary" onclick="openEditWordModal(${word.id}, '${escapeHtml(word.english)}', '${escapeHtml(word.chinese)}')">编辑</button>
                <button class="btn-small btn-danger" onclick="openDeleteWordConfirm(${word.id}, '${escapeHtml(word.english)}')">删除</button>
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
            // Create download link
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
