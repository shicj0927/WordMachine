// Login page script

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Clear previous errors
        clearError('usernameError');
        clearError('passwordError');
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        // Validation
        if (!username) {
            showError('usernameError', '请输入用户名');
            return;
        }
        
        if (!password) {
            showError('passwordError', '请输入密码');
            return;
        }
        
        // Disable button and show loading
        disableButton('loginBtn');
        showLoading('alert');
        
        try {
            const result = await login(username, password);
            
            if (result.success) {
                showAlert('登录成功，正在跳转...', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                showAlert(result.message, 'danger');
                enableButton('loginBtn');
                clearLoading('alert');
            }
        } catch (error) {
            console.error('Login error:', error);
            showAlert('登录失败，请重试', 'danger');
            enableButton('loginBtn');
            clearLoading('alert');
        }
    });
});
