from fastapi import Request
from backend.exceptions.arogya_errors import AuthenticationError

async def get_api_key_credential(request: Request) -> str:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise AuthenticationError('API key required. Use: Authorization: Bearer <api_key>')
    plain_key = auth[7:].strip()
    if not plain_key or len(plain_key) < 10:
        raise AuthenticationError('Invalid API key format')
    return plain_key
