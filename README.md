# 未来智慧云图书管理系统

一个用于毕业设计演示的前后端一体化图书馆管理系统，包含书目检索、实体册条码追踪、服务台借还、预约排队、罚金、书评、通知、推荐、统计和 RBAC 权限控制。

## 技术栈

- 后端：FastAPI、SQLAlchemy 2、Pydantic 2、SQLite、JWT、bcrypt
- 前端：Vue 3、Vue Router、Pinia、Tailwind CSS、Vite
- 部署：Uvicorn；可选 Nginx 反向代理配置见 `backend/nginx.conf`

## 本地运行

环境要求：Python 3.10+、Node.js 18+、npm。

Linux/macOS：

```bash
./run.sh
```

Windows：

```bat
run.cmd
```

脚本会在项目目录创建 `.venv` 和 `frontend/node_modules`，构建前端并初始化 `backend/library.db`。访问 `http://127.0.0.1:8000`，接口文档为 `/docs`。删除数据库文件后重新运行可恢复演示数据。

也可以手动启动：

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
(cd frontend && npm install && npm run build)
(cd backend && python init_db.py && uvicorn app:app --host 127.0.0.1 --port 8000)
```

## 演示账号

所有演示账号初始密码均为 `admin123`：

| 用户名 | 角色 | 借书卡号 |
| --- | --- | --- |
| `admin` | 系统管理员 | `CARD-888801` |
| `librarian` | 图书管理员 | `CARD-888802` |
| `student` | 普通读者 | `CARD-202601` |
| `zhangsan` | 逾期读者 | `CARD-202602` |
| `lisi` | 普通读者 | `CARD-202603` |

## 测试与构建

```bash
./.venv/bin/python -m pytest -q
(cd frontend && npm run build)
```

测试会使用临时 SQLite 数据库，不会修改本地演示数据库。

## 配置

可在 `backend/.env` 或环境变量中覆盖配置，例如 `DATABASE_URL`、`SECRET_KEY`、`CORS_ORIGINS` 和业务规则默认值。生产环境应设置随机的 `SECRET_KEY`，并将 CORS 来源限制为实际前端域名。
