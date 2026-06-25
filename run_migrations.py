"""Run async database migrations"""
import asyncio
from alembic.config import Config
from alembic import command


def run_migrations():
    """Run alembic migrations"""
    alembic_cfg = Config('alembic.ini')
    command.upgrade(alembic_cfg, 'head')


if __name__ == '__main__':
    run_migrations()