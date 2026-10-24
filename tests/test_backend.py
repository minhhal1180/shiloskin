"""Atomicity and authorization checks, invariant in baseline and training mode."""
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from app import create_app, initialize


class BackendGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = create_app({"TESTING": True, "DATABASE": str(Path(self.temp.name) / "case.db"),
                               "SECRET_KEY": "only-for-tests", "TRAINING_BUGS": os.getenv("TRAINING_BUGS", "0") == "1"})
        initialize(self.app, demo=True)
        self.clients = {}

    def login(self, username, fresh=False):
        if fresh or username not in self.clients:
            client = self.app.test_client()
            self.assertEqual(client.post("/api/login", json={"username": username, "password": "Demo@123"}).status_code, 200)
            token = client.get("/api/me").json["csrf"]
            if fresh:
                return client, token
            self.clients[username] = (client, token)
        return self.clients[username]

    def get(self, username, path):
        return self.login(username)[0].get("/api" + path)

    def post(self, username, path, payload=None, key=None):
        client, token = self.login(username)
        headers = {"X-CSRF-Token": token}
        if key:
            headers["Idempotency-Key"] = key
        return client.post("/api" + path, json=payload or {}, headers=headers)

    def test_two_buyers_only_one_sale_and_one_balance_transfer(self):
        clients = [self.login("member01", fresh=True), self.login("member01", fresh=True)]
        barrier = Barrier(2)
        def buy(pair):
            client, token = pair
            barrier.wait(timeout=5)
            return client.post("/api/listings/1/buy", json={}, headers={"X-CSRF-Token": token}).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(buy, clients))
        self.assertEqual(sorted(statuses), [200, 409])
        self.assertEqual(self.get("member01", "/me").json["user"]["balance"], 600)
        self.assertEqual(self.get("member02", "/me").json["user"]["balance"], 1900)
        self.assertIn(5, [item["id"] for item in self.get("member01", "/inventory").json["items"]])
        self.assertNotIn(5, [item["id"] for item in self.get("member02", "/inventory").json["items"]])

    def test_trade_accept_only_one_swap(self):
        trade = self.post("member01", "/trades", {"give_item_id": 1, "want_item_id": 7})
        self.assertEqual(trade.status_code, 201)
        trade_id = trade.json["id"]
        clients = [self.login("member02", fresh=True), self.login("member02", fresh=True)]
        barrier = Barrier(2)
        def accept(pair):
            client, token = pair
            barrier.wait(timeout=5)
            return client.post(f"/api/trades/{trade_id}/action", json={"action": "accept"}, headers={"X-CSRF-Token": token}).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(accept, clients))
        self.assertEqual(sorted(outcomes), [200, 409])
        own = [item["id"] for item in self.get("member01", "/inventory").json["items"]]
        other = [item["id"] for item in self.get("member02", "/inventory").json["items"]]
        self.assertIn(7, own)
        self.assertNotIn(1, own)
        self.assertIn(1, other)
        self.assertNotIn(7, other)

    def test_pending_trade_rechecks_item_listing(self):
        created = self.post("member01", "/trades", {"give_item_id": 1, "want_item_id": 7})
        self.assertEqual(created.status_code, 201)
        listed = self.post("member02", "/listings", {"item_id": 7, "price": 300})
        self.assertEqual(listed.status_code, 201)
        accepted = self.post("member02", f'/trades/{created.json["id"]}/action', {"action": "accept"})
        self.assertEqual(accepted.status_code, 409)
        self.assertIn(1, [item["id"] for item in self.get("member01", "/inventory").json["items"]])

    def test_purchase_retry_is_idempotent(self):
        first = self.post("member01", "/listings/1/buy", key="buy-case-1")
        retry = self.post("member01", "/listings/1/buy", key="buy-case-1")
        self.assertEqual((first.status_code, retry.status_code), (200, 200))
        self.assertEqual(first.json, retry.json)
        self.assertEqual(self.get("member01", "/me").json["user"]["balance"], 600)
        notifications = self.get("member01", "/notifications").json["items"]
        self.assertEqual(sum(n["event_type"] == "BUY" for n in notifications), 1)

    def test_role_and_ownership_are_enforced(self):
        self.assertEqual(self.post("member01", "/listings", {"item_id": 7, "price": 300}).status_code, 403)
        self.assertEqual(self.post("member01", "/listings/1/cancel").status_code, 403)
        self.assertEqual(self.post("moderator01", "/listings/1/buy").status_code, 403)
        self.assertEqual(self.post("admin", "/trades", {"give_item_id": 1, "want_item_id": 7}).status_code, 403)
        self.assertEqual(self.get("member01", "/users").status_code, 403)
        self.assertEqual(self.get("moderator01", "/users").status_code, 403)

    def test_trade_only_recipient_can_accept(self):
        created = self.post("member01", "/trades", {"give_item_id": 1, "want_item_id": 7})
        self.assertEqual(self.post("member01", f'/trades/{created.json["id"]}/action', {"action": "accept"}).status_code, 403)
        self.assertEqual(self.post("member02", f'/trades/{created.json["id"]}/action', {"action": "cancel"}).status_code, 403)

    def test_csrf_and_session_revocation(self):
        client, _token = self.login("member01")
        cookie = client.get_cookie("session").value
        self.assertEqual(client.post("/api/listings/1/buy", json={}).status_code, 403)
        self.assertEqual(self.post("member01", "/logout").status_code, 200)
        client.set_cookie("session", cookie)
        self.assertEqual(client.get("/api/me").status_code, 401)

    def test_lock_revokes_existing_session(self):
        client, _token = self.login("member01")
        administrator, csrf = self.login("admin")
        response = administrator.patch("/api/users/1", json={"active": False}, headers={"X-CSRF-Token": csrf})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get("/api/me").status_code, 401)

    def test_notifications_are_private(self):
        member02_notifications = self.get("member02", "/notifications").json["items"]
        wrong_id = member02_notifications[0]["id"]
        self.assertEqual(self.post("member01", f"/notifications/{wrong_id}/read").status_code, 404)
        self.assertTrue(all(row["recipient_id"] == 1 for row in self.get("member01", "/notifications").json["items"]))

    def test_catalog_filters_bind_query_values(self):
        for path, field, expected in [
            ("/skins?q=redline", "name", "Redline"),
            ("/skins?rarity=Covert", "rarity", "Covert"),
            ("/skins?weapon=AK-47", "weapon", "AK-47"),
        ]:
            with self.subTest(path=path):
                response = self.get("member01", path)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json["items"])
                self.assertTrue(all(item[field] == expected for item in response.json["items"]))

    def test_partial_catalog_patch_preserves_active(self):
        client, csrf = self.login("admin")
        response = client.patch("/api/skins/1", json={"reference_price": 300}, headers={"X-CSRF-Token": csrf})
        self.assertEqual(response.status_code, 200)
        item = self.get("admin", "/skins/1").json["item"]
        self.assertEqual(item["reference_price"], 300)
        self.assertEqual(item["active"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
