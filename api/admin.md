# API 文档 - 管理

## 1. /api/admin/check
- 类型：POST（json）
- 参数：
	- `uid`：整数，用户id
	- `password`：字符串，密码
- 返回1：`{'success': True, 'type': xxx}`（200）
- 返回2：`{'success': False}`（400）,缺少用户id或密码哈希
- 返回3：`{'success': False, 'message': 'Authentication failed'}`（401）
- 返回4：`{'success': False, 'message': 'User not found'}`（404）
- 返回5：`{'success': False}`（500）

## 2. /api/admin/users
- 类型：GET
- 参数：
	- `uid`：整数，用户id
	- `pwhash`：字符串，密码哈希
	- `include_deleted`：字符串，true/false
- 返回1：`{'success': False}`
	- 400：缺少用户id或密码哈希
	- 401：验证失败
	- 403：用户不是root
	- 500：系统错误
- 返回2：`{'success': True, 'users': users}`（200）

## 3. /api/admin/user/target_uid(int)/reset-password
- 类型：POST（json）
- 参数：
	- `uid`：整数，用户id
	- `pwhash`：字符串，密码哈希
	- `new_password`：新密码
- 返回1：`{'success': False, 'message': 'Missing required fields'}`（400）
- 返回2：`{'success': False, 'message': 'Password must be at least 6 characters'}`（400）
- 返回3：`{'success': False}`（401），验证失败
- 返回4：`{'success': False}`
	- 401：验证失败
	- 403：用户不是root
	- 500：系统错误
- 返回5：`{'success': False, 'message': 'Cannot reset own password via admin'}`（400）
- 返回6：`{'success': False, 'message': 'Target user not found'}`（404）
- 返回7：`{'success': True, 'message': 'Password reset successfully'}`（200）


## 4. /api/admin/user/target_uid(int)/delete
- 类型：POST（json）
- 参数：
	- `uid`：整数，用户id
	- `pwhash`：字符串，密码哈希
- 返回1：`{'success': False}`
	- 400：缺少用户id或密码哈希
	- 401：验证失败
	- 403：用户不是root
	- 500：系统错误
- 返回2：`{'success': False, 'message': 'Cannot delete own account'}`（400）
- 返回3：`{'success': False, 'message': 'Target user not found'}`（404）
- 返回4：`{'success': True, 'message': 'User deleted successfully'}`（200）

## 5. /api/admin/user/target_uid(int)/restore
- 类型：POST（json）
- 参数：
	- `uid`：整数，用户id
	- `pwhash`：字符串，密码哈希
- 返回1：`{'success': False}`
	- 400：缺少用户id或密码哈希
	- 401：验证失败
	- 403：用户不是root
	- 500：系统错误
- 返回2：`{'success': False, 'message': 'Target user not found'}`（404）
- 返回3：`{'success': True, 'message': 'User restored successfully'}`（200）

