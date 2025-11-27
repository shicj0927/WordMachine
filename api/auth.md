# API 文档 - /api/auth

1. `/api/register`

- 类型：POST
- 参数：`username`,`password`,`introduction`
- Cookies：无
- 返回：`{'success':True/False, 'message':xxx}`
- 信息：
Username and password required（400）

Invalid username or password length（400）

Username already exists（409）

Registration successful（201）

Server error（500）