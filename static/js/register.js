// Register page script

document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    const registerBtn = document.getElementById('registerBtn');
    
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Clear previous errors
        clearError('usernameError');
        clearError('passwordError');
        clearError('confirmPasswordError');
        clearError('introductionError');
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const introduction = document.getElementById('introduction').value.trim();
        
        // Validation
        let hasError = false;
        
        if (!validateUsername(username)) {
            showError('usernameError', '用户名长度需为3-255字符');
            hasError = true;
        }
        
        if (!validatePassword(password)) {
            showError('passwordError', '密码至少需6字符');
            hasError = true;
        }
        
        if (password !== confirmPassword) {
            showError('confirmPasswordError', '两次输入的密码不一致');
            hasError = true;
        }
        
        if (hasError) return;
        
        // Disable button and show loading
        disableButton('registerBtn');
        showLoading('alert');
        
        try {
            const result = await register(username, password, introduction);
            
            if (result.success) {
                showAlert('注册成功，正在跳转到登录...', 'success');
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 1500);
            } else {
                showAlert(result.message, 'danger');
                enableButton('registerBtn');
                clearLoading('alert');
            }
        } catch (error) {
            console.error('Register error:', error);
            showAlert('注册失败，请重试', 'danger');
            enableButton('registerBtn');
            clearLoading('alert');
        }
    });
});
