## 对局功能快速启动指南

### 🚀 快速开始

1. **启动 Flask 服务器**
```bash
cd /home/shicj/wm
source wm/bin/activate
python app.py
```

服务器将在 `http://localhost:8080` 启动

2. **访问对局大厅**
- 浏览器打开 `http://localhost:8080`
- 登录账户（如无账户先注册）
- 进入对局大厅

### 📋 对局流程测试步骤

#### 步骤1：创建对局
1. 点击"+ 创建新对局"按钮
2. 选择一个词典（如：TEST词典）
3. 点击"创建"
4. 新对局出现在"待开始"标签页

#### 步骤2：加入对局（可选，多用户测试）
1. 用另一个账户登录
2. 在首页找到刚创建的对局
3. 点击"报名"按钮
4. 成功加入后按钮变为"撤销报名"

#### 步骤3：开始对局
1. 返回创建者账户
2. 点击对局卡片上的"开始"按钮
3. 对局状态变为"进行中"
4. 自动跳转到答题页面

#### 步骤4：实时答题
1. 看到英文单词和中文提示
2. 在输入框输入英文翻译
3. 点击"提交"按钮
4. 显示答题结果
5. 自动进入下一题
6. 右侧边栏实时显示个人成绩

#### 步骤5：结束对局
1. 所有题目完成后显示完成提示
2. 点击"结束对局"按钮（或任何参赛者点击）
3. 系统自动计算 Perf 和更新 Rating
4. 重定向到对局详情页

#### 步骤6：查看对局详情
1. 显示对局基本信息
2. 显示参赛者成绩表（含 Perf 变更）
3. 显示完整答题记录

### 🧪 测试场景

#### 场景1：单人对局
```
用户A 创建对局 → 立即开始 → 答题完成 → 结束对局 → 查看成绩
```

#### 场景2：多人对局
```
用户A 创建对局
用户B 加入对局
用户C 加入对局
↓
用户A 开始对局
↓
用户A, B, C 同时答题
↓
用户A 点击结束
↓
所有用户的 Rating 更新
```

#### 场景3：中途加入和撤销
```
用户A 创建对局
用户B 加入 → 撤销报名
用户C 加入
↓
用户A 开始对局（3人参赛）
```

### 📊 数据验证

#### 验证 Perf 计算
- 6题全对：Perf = +6
- 3对3错：Perf = 0
- 2对4错：Perf = -2

#### 验证 Rating 更新
1. 对局前查看用户 Rating
2. 对局后查看排行榜
3. 确认 Rating 值已更新

### 🔍 常见问题排查

**问题1：无法创建对局**
- 检查是否已登录
- 检查是否选择了词典
- 查看浏览器控制台错误信息

**问题2：答题不响应**
- 检查网络连接
- 刷新页面重试
- 检查服务器日志

**问题3：成绩不更新**
- 检查数据库连接
- 确认对局已正确结束
- 检查用户表的 Rating 字段

### 📝 API 测试命令

#### 创建对局
```bash
curl -X POST http://localhost:8080/api/game/create \
  -H "Content-Type: application/json" \
  -d '{
    "uid": 1,
    "pwhash": "你的pwhash",
    "dict_id": 1
  }'
```

#### 列表对局
```bash
curl "http://localhost:8080/api/game/list?uid=1&pwhash=你的pwhash"
```

#### 获取对局详情
```bash
curl "http://localhost:8080/api/game/1?uid=1&pwhash=你的pwhash"
```

#### 加入对局
```bash
curl -X POST http://localhost:8080/api/game/1/join \
  -H "Content-Type: application/json" \
  -d '{
    "uid": 2,
    "pwhash": "用户2的pwhash"
  }'
```

#### 开始对局
```bash
curl -X POST http://localhost:8080/api/game/1/start \
  -H "Content-Type: application/json" \
  -d '{
    "uid": 1,
    "pwhash": "你的pwhash"
  }'
```

#### 提交答案
```bash
curl -X POST http://localhost:8080/api/game/1/answer \
  -H "Content-Type: application/json" \
  -d '{
    "uid": 1,
    "pwhash": "你的pwhash",
    "word_id": 1,
    "answer": "apple"
  }'
```

#### 结束对局
```bash
curl -X POST http://localhost:8080/api/game/1/end \
  -H "Content-Type: application/json" \
  -d '{
    "uid": 1,
    "pwhash": "你的pwhash"
  }'
```

### 🎯 性能优化建议

1. **答题超时** - 添加 30 秒或 60 秒的答题时间限制
2. **实时更新** - 考虑使用 WebSocket 替代 5 秒轮询
3. **缓存策略** - 缓存对局列表以减少数据库查询
4. **分页显示** - 对超过100个对局进行分页

### 🐛 日志查看

查看 Flask 服务器日志：
```bash
tail -f /tmp/flask.log
```

检查特定错误：
```bash
grep "error\|Error\|ERROR" /tmp/flask.log
```

### 💾 数据库查询

查看所有对局：
```sql
SELECT id, dictid, users, running FROM game ORDER BY id DESC;
```

查看对局结果：
```sql
SELECT game_id, uid, word_id, result FROM game_result ORDER BY id DESC LIMIT 20;
```

查看用户 Rating：
```sql
SELECT id, username, rating FROM user ORDER BY rating DESC;
```

### ✅ 检查清单

部署前确认：
- [ ] Flask 服务器可正常启动
- [ ] 数据库连接正常
- [ ] 至少有 1 个词典和 5+ 个单词
- [ ] 至少有 2 个测试用户账户
- [ ] 首页能正常加载和显示
- [ ] 所有 CSS 样式加载正常
- [ ] 浏览器控制台无错误

### 📞 获取帮助

- 查看 `GAME_IMPLEMENTATION.md` 了解完整实现细节
- 查看 `app.py` 了解后端代码
- 查看 `static/js/game.js` 了解前端逻辑
- 检查浏览器开发者工具的 Network 和 Console 标签

---

**祝对局测试顺利！** 🎮
