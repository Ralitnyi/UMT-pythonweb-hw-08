from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from db import get_db
from api.contacts_api import router as contacts_router
from api.auth_api import router as auth_router


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title='Contacts REST API',
    description='API for managing contacts with CRUD operations',
    version='1.0.0'
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(contacts_router)
app.include_router(auth_router)


@app.get('/')
def root():
    """Root endpoint"""
    return {
        'message': 'Contacts API',
        'version': '1.0.0',
        'docs': '/docs',
        'redoc': '/redoc'
    }


@app.get('/health')
async def health_check():
    """Health check endpoint"""
    async for db in get_db():
        try:
            await db.execute(text('SELECT 1'))
            return {'status': 'ok'}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)