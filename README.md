cat > README.md << 'EOF'
# FastAPI Docker Template

FastAPI 프로젝트를 위한 Docker + CI/CD 템플릿

## 🚀 Features

- ✅ FastAPI
- ✅ Docker & Docker Compose
- ✅ PostgreSQL 16
- ✅ Redis 7
- ✅ uv (빠른 패키지 관리)
- ✅ GitHub Actions CI/CD
- ✅ Multi-stage Dockerfile
- ✅ Development & Production 환경 분리

## 📦 Quick Start

### 1. 환경 설정
```bash
cp .env.example .env
# .env 파일 수정
```

### 2. 개발 서버 실행
```bash
# 의존성 설치
uv sync

# Docker로 실행
docker compose up --build
```

### 3. API 확인

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🛠️ Commands
```bash
make dev    # 개발 서버 시작
make up     # 백그라운드 실행
make down   # 서버 중지
make logs   # 로그 확인
make shell  # 컨테이너 접속
make test   # 테스트 실행
make clean  # 캐시 정리
```

## 📁 Project Structure
```
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── models/
│   └── schemas/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── pyproject.toml
└── .github/workflows/ci-cd.yml
```

## 🚢 Deployment

### GitHub Secrets 설정
```
DOCKER_USERNAME
DOCKER_PASSWORD
EC2_HOST
EC2_KEY
```

### 배포 흐름

1. `main` 브랜치 푸시
2. 자동 테스트 실행
3. Docker 이미지 빌드 & 푸시
4. EC2 자동 배포

## 📝 License

MIT
EOF