from backend.app.config import normalize_database_url


def test_postgres_provider_urls_use_psycopg_v3():
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("postgresql+psycopg://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_sqlite_database_url_is_unchanged():
    assert normalize_database_url("sqlite:///privexis.db") == "sqlite:///privexis.db"
