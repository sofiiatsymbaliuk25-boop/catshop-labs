import pytest
import app as shop


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(shop, "COUNTER_FILE", tmp_path / "visits.txt")
    monkeypatch.setattr(shop, "DATABASE_URL", None)
    return shop.app.test_client()


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_data(as_text=True) == "ok\n"


def test_ready_reports_file_store(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json["ready"] is True


def test_visits_counts_up(client):
    assert client.get("/visits").json["visits"] == 1
    assert client.get("/visits").json["visits"] == 2


def test_visits_503_when_store_breaks(client, monkeypatch):
    def boom():
        raise OSError("disk gone")

    monkeypatch.setattr(shop, "bump_file", boom)
    assert client.get("/visits").status_code == 503


def test_price_partner_down_gives_502(client, monkeypatch):
    def boom(*args, **kwargs):
        raise shop.requests.ConnectionError("no partner")

    monkeypatch.setattr(shop.requests, "get", boom)
    assert client.get("/price/MK-II").status_code == 502