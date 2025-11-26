// Change password page script

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication first
    const isAuthenticated = await requireAuth();
    if (!isAuthenticated) return;
    
    const changepwForm = document.getElementById('changepwForm');
    const updateBtn = document.getElementById('updateBtn');
    const uid = getCurrentUID();
    const pwHash = getCurrentPWHash();
    
    // Load current user info
    try {
        const response = await fetch(`/api/user/${uid}`);
        const data = await response.json();
        
        if (data.success && data.user) {
            document.getElementById('introduction').value = data.user.introduction || '';
        }
    } catch (error) {
        console.error('Load user info error:', error);
    }
    
    updateBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        
        // Clear previous errors
        clearError('currentPasswordError');
        clearError('newPasswordError');
        clearError('confirmPasswordError');
        clearError('introductionError');
        
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const introduction = document.getElementById('introduction').value.trim();
        
        // Validation
        let hasError = false;

        // Only require current password when changing password
        if (newPassword) {
            if (!currentPassword) {
                showError('currentPasswordError', '请输入当前密码以修改密码');
                hasError = true;
            }
            if (!validatePassword(newPassword)) {
                showError('newPasswordError', '新密码至少需6字符');
                hasError = true;
            }
            if (newPassword !== confirmPassword) {
                showError('confirmPasswordError', '两次输入的新密码不一致');
                hasError = true;
            }
        } else {
            // Not changing password — validate introduction length
            if (introduction.length > 2000) {
                showError('introductionError', '简介过长');
                hasError = true;
            }
        }

        if (hasError) return;
        
        // Disable button and show loading
        disableButton('updateBtn');
        showLoading('alert');
        
        try {
            const response = await fetch(`/api/user/${uid}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_password: currentPassword || null,
                    new_password: newPassword || null,
                    introduction: introduction,
                    pwhash: pwHash
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // If password was changed, update cookies and redirect
                if (newPassword) {
                    const newHash = await hashPassword(newPassword);
                    setAuthCookies(uid, newHash);
                    showAlert('更新成功，1秒后返回...', 'success');
                    setTimeout(() => {
                        location.href="/";
                    }, 1000);
                } else {
                    showAlert('更新成功', 'success');
                    clearLoading('alert');
                    enableButton('updateBtn');
                    showAlert('更新成功，1秒后返回...', 'success');
                    setTimeout(() => {
                        location.href="/"; 
                    }, 1000);
                }
            } else {
                showAlert(data.message || '更新失败', 'danger');
                enableButton('updateBtn');
                clearLoading('alert');
            }
        } catch (error) {
            console.error('Update error:', error);
            showAlert('更新失败，请重试', 'danger');
            enableButton('updateBtn');
            clearLoading('alert');
        }
    });
});
