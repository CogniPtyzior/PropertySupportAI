from app.db.repositories import PropertySupportRepository


def test_data_health_returns_status(session):
    repo = PropertySupportRepository(session)
    result = repo.data_health()
    assert result["status"] in {"ok", "error"}
    assert "tables" in result
