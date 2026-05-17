# 가볍고 안정적인 Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY main.py .

# 포트 노출 (기본값 8080)
ENV PORT=8080
EXPOSE $PORT

RUN useradd -m mcpuser
USER mcpuser

# 서버 실행
CMD ["fastmcp", "run", "main.py:mcp", "--transport",  "http", "--port", "8080", "--host", "0.0.0.0"]