from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from db import get_db
from api.contacts_api import router


app = FastAPI(
    title='Contacts REST API',
    description='API for managing contacts with CRUD operations',
    version='1.0.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)


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
