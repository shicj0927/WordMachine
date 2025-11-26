# 🎯 快速参考 - WordMachine 管理界面

## 快速命令

### 启动应用
```bash
cd /home/shicj/wm
python3 app.py
```

### 初始化数据库
```bash
mysql -u wm -p wm123!@# wm < setup.sql
```

### 进入 MySQL 命令行
```bash
mysql -u wm -p wm123!@# wm
```

## 测试账户

### Root 管理员
- 用户名：`admin`
- 密码：`admin123`
- 访问权限：✓ 管理界面

### 普通用户
- 用户名：`testuser`
- 密码：`test123456`
- 访问权限：✗ 管理界面

## URL 列表

| 页面 | URL |
|------|-----|
| 主页 | http://localhost:5000 |
| 登录 | http://localhost:5000/login/ |
| 注册 | http://localhost:5000/register/ |
| 修改密码 | http://localhost:5000/changepw/ |
| 管理 | http://localhost:5000/admin/ |

## 管理界面功能快速指南

### 1️⃣ 查看用户列表
- 默认显示活跃用户
- 勾选"显示已删除用户"看已删除用户

### 2️⃣ 重置用户密码
- 点击"重置密码"按钮
- 输入新密码（≥6字符）
- 确认密码
- 点击"重置密码"

### 3️⃣ 删除用户
- 点击"删除"按钮
- 在确认对话框中点击"确定"
- 用户变为已删除状态

### 4️⃣ 恢复用户
- 勾选"显示已删除用户"
- 点击"恢复"按钮
- 用户恢复到活跃状态

## 常见问题

### Q：非 Root 用户访问管理界面会怎样？
A：自动重定向到主页，并显示"没有管理员权限"提示

### Q：Root 用户能重置自己的密码吗？
A：不能。需要通过"修改密码"页面修改自己的密码

### Q：Root 用户能删除自己的账号吗？
A：不能。系统会阻止自我删除

### Q：删除用户后能恢复吗？
A：能。通过"显示已删除用户"选项可以恢复

### Q：新设置的密码格式有要求吗？
A：至少 6 个字符，区分大小写

## 新建 Root 用户（手动 SQL）

```sql
-- 登录 MySQL
mysql -u wm -p wm123!@# wm

-- 查看现有用户
SELECT id, username, type FROM user;

-- 新建 root 用户
-- 密码哈希可通过 Python 生成：
-- import hashlib
-- hashlib.sha256(b"密码").hexdigest()

INSERT INTO user (username, pwhash, introduction, rating, type, deleted) 
VALUES ('newadmin', '将SHA256哈希值填写在这里', 'Admin Description', 0, 'root', 0);
```

## 生成 SHA256 密码哈希

### Python
```python
import hashlib
password = "mypassword"
hashed = hashlib.sha256(password.encode()).hexdigest()
print(hashed)
```

### Linux 命令行
```bash
echo -n "mypassword" | sha256sum
```

## 文件清单

| 文件 | 说明 |
|------|------|
| `app.py` | 后端应用 + API |
| `static/css/admin.css` | 管理界面样式 |
| `static/js/admin.js` | 管理界面逻辑 |
| `templates/admin.html` | 管理界面模板 |
| `setup.sql` | 数据库初始化 |
| `ADMIN_GUIDE.md` | 详细使用指南 |
| `ADMIN_IMPLEMENTATION.md` | 实现细节 |
| `ADMIN_SUMMARY.md` | 完整总结 |

## 导航快速链接

### 文档
- [管理指南](./ADMIN_GUIDE.md)
- [实现细节](./ADMIN_IMPLEMENTATION.md)
- [完整总结](./ADMIN_SUMMARY.md)
- [原始需求](./gen.md)
- [数据库指南](./start.md)

### 核心代码
- 后端：[app.py](./app.py)
- HTML：[admin.html](./templates/admin.html)
- JavaScript：[admin.js](./static/js/admin.js)
- CSS：[admin.css](./static/css/admin.css)

## 关键密码哈希值

| 用户名 | 密码 | 哈希值 |
|--------|------|--------|
| admin | admin123 | 0c33f88b65fea2988e34c20b8efc81c111ce579052081803d1b5aade66e4b08a |
| testuser | test123456 | 589cff1767de5e24db2cf088f34f1fcd8a46c6d9b5aba27d6d31a38c5c5f2e7f |

## 系统要求

- Python 3.10+
- MySQL 5.7+
- Flask 3.1.2
- PyMySQL 1.1.2
- 现代浏览器（Chrome, Firefox, Safari, Edge）

## 联系方式

有问题？检查：
1. 数据库连接是否正常
2. Flask 服务是否运行
3. 浏览器控制台是否有错误
4. 查看 Flask 服务器日志

---

**最后更新**: 2025年11月26日
**版本**: 1.0 (完整版)
