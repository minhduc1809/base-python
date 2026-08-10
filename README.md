# AISoft Backend (Python FastAPI Migration)

Dự án Backend chuyển đổi từ NestJS (TypeScript) sang Python (FastAPI).

## 🚀 Cấu Trúc Dự Án (Clean Layered Architecture)

```text
python-backend/
├── app/
│   ├── core/                  # Cấu hình hệ thống, DB (SQLAlchemy, Motor, Beanie), Security (bcrypt, JWT), ContextVars, Logging
│   ├── common/                # Middleware (DataPartition, RequestID), Exceptions format chuẩn NestJS
│   ├── modules/               # Các module nghiệp vụ (health, danh_muc, form_dong, quy_tac_ma, auth...)
│   ├── tasks/                 # Celery workers cho tác vụ chạy ngầm (batch import Excel/Docx)
│   └── main.py                # Entrypoint khởi tạo ứng dụng FastAPI & Swagger OpenAPI
├── requirements.txt           # Danh sách các thư viện Python
├── Dockerfile                 # Dockerfile tối ưu đa nhân với Gunicorn + Uvicorn Workers
└── .env.example               # Mẫu file cấu hình môi trường
```

## 🛠️ Hướng Dẫn Khởi Chạy (Development)

### 1. Cài đặt Virtual Environment & Dependencies
```bash
cd python-backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Cấu hình file `.env`
```bash
cp .env.example .env
```

### 3. Chạy Server Development
```bash
python -m app.main
```
Hoặc dùng uvicorn trực tiếp:
```bash
uvicorn app.main:app --reload --port 3000
```

### 4. Chạy Celery Worker (Background Tasks)
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

## 📄 Swagger OpenAPI Documentation
Khi server khởi chạy, truy cập đường dẫn Swagger:
- **Swagger Docs**: [http://localhost:3000/api](http://localhost:3000/api)
- **ReDoc**: [http://localhost:3000/api/redoc](http://localhost:3000/api/redoc)
- **OpenAPI Schema**: [http://localhost:3000/api/openapi.json](http://localhost:3000/api/openapi.json)
