"""relay_mirror.sync() reconciles the DynamoDB bindings mirror (Track 1 T1d)."""

import pytest

from src.alerting import relay_mirror


class FakeDdb:
    def __init__(self):
        self.puts = []
        self.deletes = []

    def put_item(self, TableName, Item):  # noqa: N803
        self.puts.append((TableName, Item))

    def delete_item(self, TableName, Key):  # noqa: N803
        self.deletes.append((TableName, Key))


def test_noop_without_table(monkeypatch):
    monkeypatch.delenv("RELAY_BINDINGS_TABLE", raising=False)
    fake = FakeDdb()
    relay_mirror.sync(client=fake)  # returns before ever touching the client
    assert fake.puts == [] and fake.deletes == []
    assert relay_mirror.enabled() is False


def test_puts_enabled_binding(monkeypatch):
    monkeypatch.setenv("RELAY_BINDINGS_TABLE", "relay-bindings")
    monkeypatch.setattr(
        relay_mirror.inbound,
        "iter_configs",
        lambda: iter(
            [
                (
                    "",
                    {
                        "telegram": {
                            "inboundEnabled": True,
                            "routingId": "rid-1",
                            "webhookSecret": "whsec-plain",
                        }
                    },
                )
            ]
        ),
    )
    fake = FakeDdb()
    relay_mirror.sync(client=fake)
    assert len(fake.puts) == 1
    _table, item = fake.puts[0]
    assert item["routingId"]["S"] == "rid-1"
    assert item["webhookSecret"]["S"] == "whsec-plain"
    assert fake.deletes == []


def test_deletes_disabled_binding(monkeypatch):
    monkeypatch.setenv("RELAY_BINDINGS_TABLE", "relay-bindings")
    monkeypatch.setattr(
        relay_mirror.inbound,
        "iter_configs",
        lambda: iter(
            [("admin-1", {"telegram": {"inboundEnabled": False, "routingId": "rid-2"}})]
        ),
    )
    fake = FakeDdb()
    relay_mirror.sync(client=fake)
    assert fake.deletes and fake.deletes[0][1]["routingId"]["S"] == "rid-2"
    assert fake.puts == []


def test_skips_binding_without_routing_id(monkeypatch):
    monkeypatch.setenv("RELAY_BINDINGS_TABLE", "relay-bindings")
    monkeypatch.setattr(
        relay_mirror.inbound,
        "iter_configs",
        lambda: iter([("", {"telegram": {"inboundEnabled": True}})]),
    )
    fake = FakeDdb()
    relay_mirror.sync(client=fake)
    assert fake.puts == [] and fake.deletes == []
