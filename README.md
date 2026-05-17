# Google Drive Summarizer MCP Server

이 프로젝트는 Gemini Enterprise에서 사용자의 구글 드라이브에 있는 파일 내용을 읽고 요약할 수 있도록 돕는 MCP(Model Context Protocol) 서버입니다.

`main.py`는 FastMCP 라이브러리를 사용하여 구현되었으며, 구글 OAuth 토큰 검증을 수행합니다.

## 🚀 배포 방법 (Cloud Run)

이 폴더에서 아래 명령어를 실행하여 Google Cloud Run에 배포합니다.

```bash
gcloud run deploy gdrive-summarizer \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLIENT_ID="your-google-client-id"
```

> **⚠️ 중요 (보안 및 아키텍처):** 
> 현재 설정은 Cloud Run 자체의 접근 제어(`--no-allow-unauthenticated`)를 사용하면 Gemini Enterprise가 보내는 토큰과 충돌이 발생합니다. 따라서 서버 자체는 누구나 접근 가능하게 열어두되(`--allow-unauthenticated`), **FastMCP 서버 내부에서 구글 토큰의 유효성을 검증**하는 구조를 취하고 있습니다.

## 🤖 Gemini Enterprise에서 연동하기

1. **Gemini Enterprise 콘솔**의 데이터 스토어(Data Store) 또는 MCP 설정 메뉴로 이동합니다.
2. **Custom MCP Server 추가**를 클릭합니다.
3. 다음 정보를 입력합니다.
   - **MCP 서버 URL:** `https://<본인의_Cloud_Run_도메인>/mcp` (또는 환경에 따라 `/mcp` 없이 입력)
   - **승인 URL:** `https://accounts.google.com/o/oauth2/v2/auth`
   - **승인 URL 매개변수:** `&access_type=offline&prompt=consent`
   - **토큰 URL:** `https://oauth2.googleapis.com/token`
   - **클라이언트 ID / 비밀번호:** 발급받은 Credential 정보 입력
   - **범위 (Scopes):** `hhttps://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/drive.readonly`

4. **Description** 란에 아래 텍스트를 입력합니다.
   ```text
   This MCP server connects to Google Drive and provides a tool to read and summarize the content of text files in the user's drive.
   ```

5. **MCP Agent Instructions** 란에 아래 텍스트를 입력합니다.
   ```text
   You are an assistant with access to the user's Google Drive. Use the `summarize_drive_files` tool when the user asks to read and summarize files in their Google Drive.
   ```

## 📝 제공 기능 (Tools)

* `summarize_drive_files`: 구글 드라이브의 텍스트 파일(상위 5개)을 가져와서 요약본을 제공합니다. (현재 코드 기준으로는 `text/plain` 파일만 지원합니다.)
