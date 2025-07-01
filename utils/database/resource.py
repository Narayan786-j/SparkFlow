"""Database module."""

from contextlib import contextmanager

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session


class DatabaseResource:
    engine_url = '{}+{}://{}:{}@{}:{}/?service_name={}'

    def __init__(self, config: dict) -> None:
        db_url = self.engine_url.format(
            config['dialect'],
            config['sql_driver'],
            config['username'],
            config['password'],
            config['host'],
            config['port'],
            config['service']
        )

        self._engine = create_engine(
            db_url, pool_size=20, max_overflow=15, echo=False,
            pool_recycle=300, pool_pre_ping=True, pool_use_lifo=True
        )

        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    @contextmanager
    def session(self):
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
