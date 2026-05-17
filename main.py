import os
import httpx
from typing import Optional
from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.auth.providers.google import GoogleTokenVerifier
from fastmcp.server.auth.auth import AccessToken
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)

# 1. 사용자 정의 구글 토큰 검증기
class ExtendedGoogleTokenVerifier(GoogleTokenVerifier):
    def __init__(
        self,
        *,
        required_scopes: list[str] | None = None,
        timeout_seconds: int = 10,
        http_client: httpx.AsyncClient | None = None,
        audience: str
    ):
        super().__init__(
            required_scopes=required_scopes, 
            timeout_seconds=timeout_seconds, 
            http_client=http_client
        )
        logger.info("Audience: %s", audience)
        self.audience = audience
   
    async def verify_token(self, token: str) -> AccessToken | None:
        ret = await super().verify_token(token)
        # 문자열 포맷팅 오류 수정: aud는 보통 문자열(str)이므로 %s를 사용하는 것이 안전합니다.
        if ret is not None and ret.claims.get("aud") != self.audience:
            logger.debug(
                "Google token missing required audience. Has %s, expected %s",
                ret.claims.get("aud"),
                self.audience
            )
            return None
        ret.token = token
        return ret


# 구글 드라이브 파일 읽기 권한 스코프 추가
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive.readonly' # 드라이브 파일 내용을 읽기 위해 필수
]

verifier = ExtendedGoogleTokenVerifier(
    required_scopes=SCOPES, 
    audience=os.getenv('CLIENT_ID', 'your-default-client-id')
)
mcp = FastMCP("Google Drive Summarizer MCP", auth=verifier)

# 2. 구글 드라이브 요약 Tool 정의
@mcp.tool(description="사용자의 구글 드라이브에 있는 파일 내용을 읽고 요약합니다.")
async def summarize_drive_files(context: Context) -> str:
    """
    "구글 드라이브에 모든 파일 내용을 요약해 줘"와 같은 사용자 요청이 들어올 때 실행됩니다.
    """
    # 1. FastMCP 컨텍스트에서 인증 객체를 안전하게 가져옵니다.
    access_token = get_access_token()  
    if not access_token:
        return "인증 토큰을 찾을 수 없습니다. 다시 로그인해 주세요."

    headers = {
        "Authorization": f"Bearer {access_token.token}",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            # 1. 파일 목록 가져오기 (예제이므로 텍스트 문서 상위 5개만 조회)
            # 실제 운영 시에는 페이지네이션 처리와 더 다양한 mimeType 필터링이 필요합니다.
            list_url = "https://www.googleapis.com/drive/v3/files?q=mimeType='text/plain'&pageSize=5"
            list_response = await client.get(list_url, headers=headers)
            list_response.raise_for_status()
            
            files = list_response.json().get('files', [])
            
            if not files:
                return "구글 드라이브에 요약할 텍스트 파일이 없습니다."

            # 2. 파일 내용 읽기 및 요약 생성
            summaries = []
            for f in files:
                file_id = f['id']
                file_name = f['name']
                
                # 파일 내용 다운로드 (alt=media 파라미터 사용)
                content_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
                content_resp = await client.get(content_url, headers=headers)
                
                if content_resp.status_code == 200:
                    content = content_resp.text
                    
                    # TODO: 이 부분에 LLM(OpenAI, Gemini 등) API를 연결하여 실제 텍스트 요약을 진행합니다.
                    # 본 예제에서는 파일 내용의 앞 150자만 잘라서 보여주는 것으로 대체합니다.
                    summary_text = content[:150] + "..." if len(content) > 150 else content
                    summaries.append(f"📄 **{file_name}**\n요약: {summary_text}")
                else:
                    summaries.append(f"📄 **{file_name}**\n요약: (파일 내용을 읽을 권한이 없거나 오류가 발생했습니다)")
            return "구글 드라이브 파일 요약 결과입니다:\n\n" + "\n\n---\n\n".join(summaries)

        except httpx.HTTPStatusError as e:
            logger.error(f"Google Drive API 호출 중 오류 발생: {e}")
            return f"구글 드라이브 API 오류가 발생했습니다. (상태 코드: {e.response.status_code})"