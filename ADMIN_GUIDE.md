# WordMachine 管理界面使用指南

## 功能概述

管理界面允许 root 类型的用户进行以下操作：

### 1. 查看所有用户
- 显示所有活跃用户的列表
- 支持显示已删除的用户（通过复选框）
- 显示用户信息：ID、用户名、简介、评分、类型、状态

### 2. 重置用户密码
- 管理员可以为任何用户设置新密码
- 不能重置自己的密码（需要在"修改密码"页面操作）
- 新密码需要至少6个字符

### 3. 删除用户
- 支持软删除（用户记录保留，标记为已删除）
- 不能删除自己的账号
- 已删除的用户无法登录

### 4. 恢复用户
- 恢复被删除的用户
- 恢复后用户可以正常登录

## 访问要求

- 用户必须已登录
- 用户的 `type` 字段必须为 `root`
- 如果非 root 用户尝试访问，将被自动重定向到主页

## URL 和 API 端点

### 页面
- `/admin/` - 管理界面主页

### API 端点

#### 检查管理员权限
```
POST /api/admin/check
{
    "uid": 1,
    "pwhash": "password_hash"
}
```

#### 获取用户列表
```
GET /api/admin/users?uid=1&pwhash=password_hash&include_deleted=false
```

#### 重置用户密码
```
POST /api/admin/user/<user_id>/reset-password
{
    "uid": 1,
    "pwhash": "password_hash",
    "new_password": "new_password"
}
```

#### 删除用户
```
POST /api/admin/user/<user_id>/delete
{
    "uid": 1,
    "pwhash": "password_hash"
}
```

#### 恢复用户
```
POST /api/admin/user/<user_id>/restore
{
    "uid": 1,
    "pwhash": "password_hash"
}
```

## 创建 Root 用户

### 方法1：使用 SQL 脚本
```bash
mysql -u wm -p wm123!@# wm < setup.sql
```

### 方法2：手动 SQL 命令
```sql
-- 用 root 身份登录
sudo mysql

-- 选择 WordMachine 数据库
use wm;

-- 插入 root 用户（密码：admin123）
INSERT INTO user (username, pwhash, introduction, rating, type, deleted) 
VALUES ('admin', '0c33f88b65fea2988e34c20b8efc81c111ce579052081803d1b5aade66e4b08a', 'Administrator', 0, 'root', 0);

-- 查看用户
SELECT * FROM user;
```

## 安全说明

1. **密码哈希**：所有密码使用 SHA256 哈希存储
2. **身份验证**：每个管理操作都需要提供 uid 和密码哈希进行验证
3. **权限检查**：服务器端验证用户是否为 root 类型
4. **软删除**：用户数据不会被物理删除，只是标记为已删除
5. **自我保护**：管理员不能删除或修改自己的密码

## UI 特性

- **响应式设计**：适配桌面和移动设备
- **模态对话框**：用于密码重置和确认操作
- **表格视图**：清晰展示用户信息和可用操作
- **实时刷新**：操作完成后自动刷新用户列表
- **错误处理**：友好的错误提示和验证反馈

## 常见操作流程

### 重置用户密码
1. 在用户表中找到目标用户
2. 点击"重置密码"按钮
3. 输入新密码并确认
4. 点击"重置密码"确认操作

### 删除用户
1. 找到要删除的用户
2. 点击"删除"按钮
3. 在确认对话框中点击"确定"

### 恢复用户
1. 勾选"显示已删除用户"复选框
2. 找到要恢复的用户
3. 点击"恢复"按钮

## 技术栈

- **后端**：Flask + PyMySQL
- **前端**：Vanilla JavaScript + HTML5 + CSS3
- **数据库**：MySQL
- **身份验证**：Cookie 存储 + SHA256 密码哈希
