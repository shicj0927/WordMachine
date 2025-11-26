// Home page script

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication first
    const isAuthenticated = await requireAuth();
    if (!isAuthenticated) return;
    
    const uid = getCurrentUID();
    const logoutBtn = document.getElementById('logoutBtn');
    
    // Load user info
    try {
        const response = await fetch(`/api/user/${uid}`);
        const data = await response.json();
        
        if (data.success && data.user) {
            const user = data.user;
            const welcomeMessage = document.getElementById('welcomeMessage');
            welcomeMessage.innerHTML = `
                <strong>欢迎，${escapeHtml(user.username)}！</strong><br>
                评分：${user.rating} <br> 权限：${user.type === 'normal' ? '普通' : (user.type === 'root' ? '管理员' : user.type)}
            `;
        }
    } catch (error) {
        console.error('Load user info error:', error);
    }
    
    // Logout button handler
    logoutBtn.addEventListener('click', () => {
        if (confirm('确定要登出吗？')) {
            logout();
        }
    });
});
