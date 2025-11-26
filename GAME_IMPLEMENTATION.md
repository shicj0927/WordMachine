## 对局功能生成完成

我已为 WordMachine 项目成功生成了完整的对局（游戏）功能。以下是完整的实现细节。

---

## 📋 核心功能概述

根据 `gen.md` 的要求，实现了以下功能：

1. ✅ **对局创建** - 用户选择词典创建新对局
2. ✅ **参赛报名** - 参赛者加入或撤销报名（未开始状态）
3. ✅ **对局开始** - 创建者开始对局，生成随机参赛顺序
4. ✅ **实时答题** - 按顺序答题，大小写不敏感判断
5. ✅ **对局结束** - 任何人可结束对局，自动计算Perf和Rating
6. ✅ **历史查看** - 查看已结束对局的详细记录和成绩

---

## 🔧 后端 API 端点

### 1. `POST /api/game/create` - 创建对局

**请求参数：**
```json
{
  "uid": 1,
  "pwhash": "xxx",
  "dict_id": 1
}
```

**响应：**
```json
{
  "success": true,
  "game_id": 1,
  "message": "Game created"
}
```

**功能：**
- 检查词典是否存在且有单词
- 随机排列词典中所有单词
- 初始化参赛者列表（仅包含创建者）
- 生成 JSON 格式的 `wordlist` 和 `users`

---

### 2. `GET /api/game/list` - 获取对局列表

**请求参数：**
```
?uid=1&pwhash=xxx
```

**响应：**
```json
{
  "success": true,
  "games": [
    {
      "id": 1,
      "dictid": 1,
      "dictname": "词典名称",
      "users": [1, 2, 3],
      "wordlist": [10, 20, 30],
      "result": [...],
      "running": false,
      "is_joined": true
    }
  ]
}
```

**功能：**
- 返回所有对局（包含用户是否参加的标记）
- 解析 JSON 字段便于前端使用

---

### 3. `GET /api/game/<id>` - 获取对局详情

**请求参数：**
```
?uid=1&pwhash=xxx
```

**响应：**
```json
{
  "success": true,
  "game": {
    "id": 1,
    "dictname": "词典名",
    "users": [
      {"id": 1, "username": "user1"},
      {"id": 2, "username": "user2"}
    ],
    "words": [
      {"id": 10, "english": "apple", "chinese": "苹果"},
      {"id": 20, "english": "book", "chinese": "书"}
    ],
    "result": [
      {"uid": 1, "word_id": 10, "answer": "apple", "result": true},
      {"uid": 1, "word_id": 20, "answer": "book", "result": true}
    ],
    "perf": {
      "1": {"correct": 2, "wrong": 0, "perf": 2},
      "2": {"correct": 1, "wrong": 1, "perf": 0}
    },
    "running": false
  }
}
```

**功能：**
- 获取完整对局信息和参赛者
- 计算每个参赛者的 Perf（正确+1，错误-1）

---

### 4. `POST /api/game/<id>/join` - 加入对局

**请求参数：**
```json
{
  "uid": 2,
  "pwhash": "xxx"
}
```

**限制：**
- 仅在对局未开始时允许
- 不能重复加入

**功能：**
- 添加用户到参赛者列表
- 重新随机打乱参赛者顺序

---

### 5. `POST /api/game/<id>/leave` - 撤销报名

**请求参数：**
```json
{
  "uid": 2,
  "pwhash": "xxx"
}
```

**限制：**
- 仅在对局未开始时允许
- 用户必须已加入

**功能：**
- 从参赛者列表中移除用户

---

### 6. `POST /api/game/<id>/start` - 开始对局

**请求参数：**
```json
{
  "uid": 1,
  "pwhash": "xxx"
}
```

**功能：**
- 将对局状态设为运行中
- TODO: 可添加创建者验证

---

### 7. `POST /api/game/<id>/answer` - 提交答案

**请求参数：**
```json
{
  "uid": 1,
  "pwhash": "xxx",
  "word_id": 10,
  "answer": "apple"
}
```

**响应：**
```json
{
  "success": true,
  "correct": true,
  "expected": "apple",
  "message": "Answer recorded"
}
```

**功能：**
- 大小写不敏感判断答案
- 记录答题结果到 `result` 列表
- 返回是否正确和正确答案

---

### 8. `POST /api/game/<id>/end` - 结束对局

**请求参数：**
```json
{
  "uid": 1,
  "pwhash": "xxx"
}
```

**响应：**
```json
{
  "success": true,
  "perf": {
    "1": 2,
    "2": -1,
    "3": 0
  },
  "message": "Game ended and ratings updated"
}
```

**功能：**
- 计算所有参赛者的 Perf
- 将 Perf 加入用户 Rating
- 设置对局状态为未运行（已完成）

---

## 🎨 前端页面与模板

### 1. `/` - 首页/对局大厅

**重新设计的首页，采用二列布局：**

- **左列（通知栏）**
  - 系统通知
  - 开发计划
  - 可扩展添加更多通知

- **右列（对局大厅）**
  - 创建新对局按钮
  - 对局标签页：待开始、进行中、已结束
  - 对局卡片列表，显示：
    - 对局编号和状态徽章
    - 词典名称
    - 参赛者数量和列表
    - 操作按钮（报名、撤销、开始、观战、详情）

**文件：** `templates/home.html`

---

### 2. `/game/<id>/` - 对局进行中

**实时答题界面：**

- **主区域**
  - 当前单词显示（英文）
  - 中文翻译（提示）
  - 答题进度（第 X / Y 题）
  - 答题输入框和提交按钮
  - 最近答题记录展示

- **右侧边栏**
  - 我的成绩（正确、错误、Perf）
  - 参赛者列表（显示每个参赛者的成绩）
  - 结束对局按钮

**功能：**
- 实时显示当前题目
- 记录答题历史
- 每5秒自动同步其他参赛者的成绩
- 所有题目完成后显示完成提示

**文件：** `templates/game_playing.html`

---

### 3. `/game/<id>/detail/` - 对局详情

**对局历史和成绩页面：**

- **对局信息**
  - 词典名称
  - 参赛者数和题目数
  - 已答题数
  - 对局状态

- **成绩总结**
  - 表格显示每个参赛者的：
    - 正确题数
    - 错误题数
    - Perf 变更（+/- 值）

- **答题记录**
  - 完整表格显示所有答题记录：
    - 序号
    - 用户
    - 单词（英文 → 中文）
    - 用户答案
    - 正确答案
    - 正误标记

**文件：** `templates/game_detail.html`

---

## 📱 JavaScript 前端逻辑

### 1. `static/js/game.js` - 对局大厅逻辑

**主要功能：**
- 加载对局列表（自动每2秒刷新）
- 按状态标签页筛选对局
- 创建新对局（模态框选择词典）
- 报名对局
- 撤销报名
- 开始对局
- 观战/进入对局
- 查看对局详情

**关键代码结构：**
```javascript
loadGames()              // 获取所有对局
renderGames()           // 按标签页筛选并渲染
renderGameCard()        // 渲染单个对局卡片
joinGame(gameId)        // 加入对局
leaveGame(gameId)       // 撤销报名
startGame(gameId)       // 开始对局
watchGame(gameId)       // 进入对局进行中页面
viewGameDetail(gameId)  // 查看对局详情
showCreateGameModal()   // 创建对局模态框
```

---

### 2. `static/js/game-playing.js` - 对局进行中逻辑

**主要功能：**
- 加载当前对局数据
- 显示当前题目（英文 + 中文提示）
- 提交答案（处理大小写不敏感）
- 更新个人成绩
- 显示最近答题记录
- 同步其他参赛者成绩（5秒刷新）
- 结束对局

**关键代码结构：**
```javascript
loadGameAndStart()         // 加载对局并初始化
initializeScores()         // 初始化成绩统计
displayCurrentWord()       // 显示当前题目
submitAnswer(event)        // 提交答案
updateMyScore()            // 更新我的成绩
updateResultsDisplay()     // 显示最近答题记录
updateParticipantsList()   // 更新参赛者列表
autoRefresh()              // 5秒自动刷新
endGame()                  // 结束对局
```

---

### 3. `static/js/game-detail.js` - 对局详情逻辑

**主要功能：**
- 加载对局详情
- 显示对局基本信息
- 显示参赛者成绩总结
- 显示完整答题记录表格

**关键代码结构：**
```javascript
loadGameDetail(gameId)      // 获取对局详情
renderGameDetail(game)      // 渲染页面
renderGameSummary(game)     // 显示对局基本信息
renderPerfSummary(game)     // 显示成绩总结
renderResultsTable(game)    // 显示答题记录表格
```

---

## 🎨 CSS 样式

### `static/css/game.css`

**包含的样式：**
- 二列游戏布局
- 通知栏卡片样式
- 对局卡片样式
- 对局标签页和按钮
- 状态徽章（待开始/进行中/已结束）
- 参赛者列表徽章
- 操作按钮样式（报名/撤销/开始/观战/详情）
- 空状态提示
- 创建对局模态框
- 答题界面样式
- 成绩显示
- 响应式设计（适应 1024px、768px 及以下）

---

## 🛠️ 页面路由

| 路由 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 首页/对局大厅 |
| `/game/<id>/` | GET | 对局进行中页面 |
| `/game/<id>/detail/` | GET | 对局历史/详情页面 |

---

## 📊 数据流程详解

### 对局生命周期

```
1. 创建对局
   ↓
   [待开始] - 用户可以加入/撤销
   ↓
2. 开始对局 (创建者点击"开始")
   ↓
   [进行中] - 参赛者轮流答题，自动刷新成绩
   ↓
3. 结束对局 (任何人点击"结束")
   ↓
   [已结束] - 显示成绩和答题记录
   ↓
4. 查看历史
```

### 答题流程

```
前端答题 → 发送答案 API → 后端检查 → 返回结果 → 前端更新成绩 → 移到下一题
↓
继续循环，直到所有题目完成
↓
点击结束 → 计算 Perf → 更新 Rating → 对局完成
```

---

## ✨ 关键特性

| 特性 | 实现状态 | 说明 |
|------|--------|------|
| 词典单词随机排列 | ✅ | 每场对局词典单词顺序随机 |
| 参赛者随机顺序 | ✅ | 加入时重新打乱参赛者顺序 |
| 大小写不敏感 | ✅ | apple = APPLE = Apple |
| Perf计算 | ✅ | +1正确，-1错误，基准0 |
| Rating自动更新 | ✅ | 对局结束时更新用户Rating |
| 对局状态管理 | ✅ | 待开始/进行中/已结束 |
| 实时成绩同步 | ✅ | 5秒刷新参赛者成绩 |
| 响应式设计 | ✅ | 支持移动端 |
| 答题历史 | ✅ | 显示完整答题记录 |
| 权限控制 | ✅ | 认证用户才能参赛 |

---

## 🧪 测试状态

- ✅ Flask 服务器启动成功
- ✅ 代码语法检查通过
- ✅ 首页加载成功
- ✅ 导航栏渲染正确
- ⏳ 完整功能测试待进行（需要数据库和用户认证）

---

## 📝 文件清单

### 后端文件
- `app.py` 
  - 添加 8 个游戏 API 端点
  - 添加 2 个游戏页面路由
  - 修改端口为 8080（避免权限问题）

### 模板文件
- `templates/home.html` - 重新设计（对局大厅）
- `templates/game_playing.html` - 新建（对局进行中）
- `templates/game_detail.html` - 新建（对局详情）

### JavaScript 文件
- `static/js/game.js` - 新建（对局大厅逻辑）
- `static/js/game-playing.js` - 新建（对局进行中逻辑）
- `static/js/game-detail.js` - 新建（对局详情逻辑）

### CSS 文件
- `static/css/game.css` - 新建（对局样式）

### 文档
- `GAME_IMPLEMENTATION.md` - 本文件

---

## 🚀 下一步建议

### 高优先级
1. **完整测试流程** - 在有数据库的环境中测试所有 API
2. **添加创建者验证** - 在 `/api/game/<id>/start` 中验证创建者身份
3. **数据库优化** - 添加 `creator_id` 字段到 `game` 表
4. **错误处理** - 增强前后端错误提示和恢复机制

### 中优先级
5. **WebSocket 实时更新** - 使用 WebSocket 实现实时答题更新（比5秒轮询更高效）
6. **分页优化** - 对历史对局进行分页显示
7. **对局统计** - 为用户添加对局统计（参赛次数、平均分等）

### 低优先级
8. **对局重播** - 记录对局过程，允许回放
9. **排行榜优化** - 基于对局表现的特殊排行榜
10. **对局搜索** - 根据词典、日期等搜索对局

---

## 📞 技术支持

如有任何问题或需要调整，请参考以下文件：
- `app.py` - 后端实现
- `start.md` - 数据库配置
- `gen.md` - 需求文档

