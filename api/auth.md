# API 文档 - /api/auth

## 1. `/api/register`
	- 类型：POST（json）
	- 参数：
		- `username`：字符串，用户名
		- `password`：字符串，密码
		- `introduction`：字符串，用户简介
	- Cookies：无
	- 返回1：`{'success': False, 'message': xxx}`
	- 信息（状态码）：
		- `Username and password required`（400）
		- `Invalid username or password length`（400）
		- `Username already exists`（409）
		- `Server error`（500）
	- 返回2：`{'success': True, 'message': xxx}`
	- 信息（状态码）：
		- `Registration successful`（201）

## 2. `/api/login`
	- 类型：POST（json）
	- 参数：
		- `username`：字符串，用户名
		- `password`：字符串，密码
	- Cookies：无
	- 返回1：`{'success': False, 'message': xxx}`
	- 信息（状态码）：
		- `Username and password required`（400）
		- `Invalid username or password`（401）
		- `Server error`（500）
	- 返回2：`{'success': True, 'uid': uid, 'pwhash': pwhash}`（200）
		- `uid`：整数，用户id
		- `pwhash`：字符串，密码哈希

## 3. `/api/verify`
	- 类型：GET（json）
	- 参数：
		- `uid`：整数，用户id
		- `pwhash`：字符串，密码哈希
	- 返回1：`{'success': False}`
	- 状态码：
		- 400：用户名或密码哈希为空
		- 401：用户名或密码错误
		- 500：系统错误
	- 返回2：`{'success': True}`（200）

## 4. `/api/user/<int: uid>`
	- 类型：GET
	- 参数：无
	- 返回1：`{'success': True, 'user': user}`（200）
	- 返回2：`{'success':  False, 'message':  'User not found'}`（404）
	- 返回3：`{'success': False, 'message': 'Server error'}`（500）

## 5. `/api/user/<int:uid>/update`
	- 类型：POST（json）
	- 参数：
		- `current_password`：字符串，原始密码
		- `new_password`：字符串，新密码（非必需）
		- `introduction`：字符串，用户简介（非必需）
		- `pwhash`：字符串，密码哈希
	- 返回1：`{'success': False, 'message': xxx}`
	- 信息（状态码）：
		- `Current password incorrect`（401）
		- `New password must be at least 6 characters`（400）
		- `No updates provided`（400）
		- `Server error`（500）
	- 返回2：`{'success': False, 'message': xxx}`
	- 信息（状态码）：
		- `User updated successfully`（200）