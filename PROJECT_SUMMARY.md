# 图书管理系统 - 项目总结

## 🎯 项目概述

这是一个**功能完整、生产就绪**的图书管理系统，采用现代化的前后端分离架构，使用 Bocker 实现一键构建和部署。

### 核心特点

✨ **一键部署** - 使用 `./deploy.sh` 即可完成从构建到运行的全过程  
🎨 **Material Design 3** - 使用 Vuetify 3 打造现代化界面  
🔒 **安全可靠** - JWT 认证、密码加密、SQL 注入防护  
📱 **响应式设计** - 完美适配桌面和移动设备  
🐳 **容器化** - 所有服务运行在单个 Incus 容器中  
⚡ **高性能** - FastAPI 异步框架 + Nginx 反向代理  

## 📊 项目规模

- **总文件数**: 30+ 个
- **代码行数**: 约 3000+ 行
- **后端文件**: 9 个 Python 文件
- **前端文件**: 8 个 Vue 组件
- **配置文件**: 10+ 个

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────┐
│              Incus 容器 (library-app)            │
│  ┌───────────────────────────────────────────┐  │
│  │  Nginx (端口 80)                           │  │
│  │  ├─ 前端静态文件 (/var/www/library)       │  │
│  │  └─ API 反向代理 (/api -> :8000)          │  │
│  └───────────────────────────────────────────┘  │
│                      ↓                           │
│  ┌───────────────────────────────────────────┐  │
│  │  FastAPI + Uvicorn (端口 8000)            │  │
│  │  ├─ JWT 认证                               │  │
│  │  ├─ RESTful API                            │  │
│  │  └─ SQLAlchemy ORM                         │  │
│  └───────────────────────────────────────────┘  │
│                      ↓                           │
│  ┌───────────────────────────────────────────┐  │
│  │  SQLite (library.db 单文件)                │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  systemd 管理所有服务                            │
└─────────────────────────────────────────────────┘
```

## 📦 技术栈详情

### 后端
- **框架**: FastAPI 0.141.1
- **服务器**: Uvicorn (ASGI)
- **ORM**: SQLAlchemy 2.0.54
- **数据库**: SQLite（单文件 `backend/library.db`）
- **认证**: python-jose (JWT)
- **密码加密**: passlib + bcrypt
- **数据验证**: Pydantic 2.13.5

### 前端
- **框架**: Vue 3.5.0
- **UI 库**: Vuetify 3.7.0 (Material Design 3)
- **路由**: Vue Router 4.4.0
- **状态管理**: Pinia 2.2.0
- **HTTP 客户端**: Axios 1.7.0
- **构建工具**: Vite 5.4.0
- **图标**: Material Design Icons

### 基础设施
- **数据库**: SQLite
- **Web 服务器**: Nginx（容器部署）
- **进程管理**: systemd
- **容器技术**: Incus
- **构建工具**: Bocker

## 🎯 核心功能

### 1. 用户管理
- [x] 用户注册（用户名、邮箱、姓名）
- [x] 用户登录（JWT Token）
- [x] 自动登录（Token 持久化）
- [x] 用户信息展示
- [x] 登出功能

### 2. 图书管理
- [x] 图书列表（分页、搜索）
- [x] 添加图书（含封面、分类、描述）
- [x] 编辑图书
- [x] 删除图书（确认机制）
- [x] 库存管理（总量/可借量）
- [x] 图书搜索（标题、作者、ISBN）

### 3. 借阅管理
- [x] 借阅图书（库存检查）
- [x] 归还图书
- [x] 借阅记录查看
- [x] 借阅中/已归还分类
- [x] 逾期提醒（红色标记）
- [x] 30天借阅期限
- [x] 重复借阅检查

### 4. 数据统计
- [x] 图书总数
- [x] 借阅中图书数
- [x] 个人借阅数
- [x] 仪表盘可视化

## 📁 项目结构

```
library-management/
├── Incusfile                      # Bocker 构建配置
├── deploy.sh                      # 一键部署脚本 ⭐
├── run.cmd                        # 一键本地编译运行脚本 ⭐
├── README.md                      # 项目说明
├── USAGE.md                       # 使用指南
├── CHANGELOG.md                   # 更新日志
├── .gitignore                     # Git 忽略文件
│
├── backend/                       # 后端代码
│   ├── app.py                    # FastAPI 主应用 ⭐
│   ├── models.py                 # SQLAlchemy 数据模型
│   ├── schemas.py                # Pydantic 数据模式
│   ├── database.py               # 数据库配置（SQLite）
│   ├── init_db.py                # 建表与种子数据初始化 ⭐
│   ├── auth.py                   # JWT 认证逻辑
│   ├── requirements.txt          # Python 依赖
│   ├── library-api.service       # API systemd 服务
│   ├── library.db                # SQLite 数据库文件（运行时生成）
│   └── nginx.conf                # Nginx 配置
│
├── frontend/                      # 前端代码
│   ├── index.html                # HTML 入口
│   ├── package.json              # Node 依赖
│   ├── vite.config.js            # Vite 配置
│   └── src/
│       ├── main.js               # Vue 入口
│       ├── App.vue               # 根组件 ⭐
│       ├── api/
│       │   ├── axios.js         # Axios 配置
│       │   └── index.js         # API 封装
│       ├── router/
│       │   └── index.js         # 路由配置
│       ├── stores/
│       │   └── user.js          # 用户状态管理
│       └── views/
│           ├── Login.vue         # 登录页面
│           ├── Register.vue      # 注册页面
│           ├── Dashboard.vue     # 仪表盘
│           ├── Books.vue         # 图书列表 ⭐
│           └── Borrows.vue       # 借阅管理
└── .venv/                         # 本地 Python 虚拟环境（运行时生成）
```

## 🚀 快速开始

### 方式一：本地一键运行（推荐）

```bat
:: 项目根目录双击 run.cmd，或执行
.\run.cmd
```

自动完成：创建 `.venv` → 安装后端依赖 → 安装前端依赖 → 编译前端 → 初始化 SQLite → 启动服务并打开浏览器（`http://127.0.0.1:8000`）。

依赖仅写入 `.venv\` 与 `frontend\node_modules\`，不会污染系统环境。

### 方式二：一键部署到容器（推荐）

```bash
cd /home/sleet/code/xms/library-management
./deploy.sh
```

### 方式三：手动部署

```bash
# 1. 构建镜像
bocker image build --name library-management ./Incusfile

# 2. 运行容器
bocker image run library-management --name library-app

# 3. 获取容器 IP
bocker container exec library-app ip addr show eth0

# 4. 访问系统
# 浏览器打开: http://<容器IP>
```

### 默认账号
```
用户名: admin
密码: admin123
```

## 🔧 开发亮点

### 1. 安全性
- ✅ JWT Token 认证
- ✅ 密码 bcrypt 加密
- ✅ SQL 参数化查询（防注入）
- ✅ CORS 跨域配置
- ✅ 请求拦截器（自动添加 Token）

### 2. 用户体验
- ✅ 响应式设计（移动/桌面）
- ✅ 加载状态提示
- ✅ 操作成功/失败提示
- ✅ 表单验证
- ✅ 确认对话框
- ✅ 逾期醒目提示

### 3. 代码质量
- ✅ 前后端分离
- ✅ RESTful API 设计
- ✅ 组件化开发
- ✅ 状态集中管理
- ✅ 代码注释完整
- ✅ 错误处理完善

### 4. 运维友好
- ✅ systemd 服务管理
- ✅ 日志记录完善
- ✅ 自动重启机制
- ✅ 健康检查
- ✅ 数据库备份友好

## 📊 数据库设计

### 表结构

**users（用户表）**
- id, username, email, full_name, hashed_password, created_at

**books（图书表）**
- id, title, author, isbn, publisher, publish_date, category
- description, cover_url, total_quantity, available_quantity
- created_at, updated_at

**borrow_records（借阅记录表）**
- id, user_id, book_id, borrow_date, due_date, return_date, created_at
- 外键关联 users 和 books

### 索引优化
- username, email, isbn 唯一索引
- 常用查询字段建立索引
- 外键自动索引

## 🎨 界面展示

### 主要页面
1. **登录页面** - 简洁的 Material Design 风格
2. **注册页面** - 表单验证完善
3. **仪表盘** - 数据卡片展示统计信息
4. **图书列表** - 数据表格 + 搜索 + CRUD 操作
5. **借阅管理** - 标签页分类 + 状态提示

### UI 组件
- v-card（卡片）
- v-data-table（数据表格）
- v-dialog（对话框）
- v-snackbar（提示条）
- v-chip（标签）
- v-btn（按钮）
- v-text-field（输入框）

## 📈 性能特点

- **异步处理**: FastAPI 原生异步支持
- **连接池**: SQLAlchemy 数据库连接池
- **静态资源**: Nginx 高效服务
- **前端优化**: Vite 打包优化、代码分割
- **缓存策略**: 浏览器缓存配置

## 🔄 CI/CD 友好

项目结构支持：
- Docker/Podman 容器化
- Kubernetes 部署
- GitLab CI/CD
- GitHub Actions
- 自动化测试集成

## 📝 API 端点

### 认证
- POST `/api/auth/register` - 注册
- POST `/api/auth/login` - 登录
- GET `/api/auth/me` - 获取当前用户

### 图书
- GET `/api/books` - 图书列表
- GET `/api/books/{id}` - 图书详情
- POST `/api/books` - 添加图书
- PUT `/api/books/{id}` - 更新图书
- DELETE `/api/books/{id}` - 删除图书

### 借阅
- GET `/api/borrows` - 借阅记录
- POST `/api/borrows` - 借阅图书
- POST `/api/borrows/{id}/return` - 归还图书

### 统计
- GET `/api/stats` - 统计数据

## 🎓 学习价值

本项目适合作为：
- 全栈开发学习案例
- Vue 3 实战项目
- FastAPI 入门教程
- Bocker 使用示例
- 容器化部署实践
- Material Design 应用

## 🔮 未来规划

- [ ] 图书推荐算法
- [ ] 用户评分系统
- [ ] 邮件通知功能
- [ ] 图书预约功能
- [ ] 数据分析报表
- [ ] 图书封面上传
- [ ] 批量导入导出
- [ ] 管理员后台
- [ ] 移动端 App
- [ ] 多语言支持

## 📄 许可证

MIT License

## 👨‍💻 开发信息

- 开发时间: 2026-09-15
- 语言: Python, JavaScript, SQL
- 框架: FastAPI, Vue 3
- 数据库: SQLite
- 部署: Bocker + Incus

---

**这是一个生产就绪的完整项目，可以直接用于实际的图书馆管理场景！** 🎉
