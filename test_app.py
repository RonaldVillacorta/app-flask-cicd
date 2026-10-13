import unittest
from app import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

    def test_home_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Panel de Control", response.data)

    def test_items_route(self):
        response = self.client.get("/items")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cat\xc3\xa1logo de Servicios", response.data)

    def test_runtime_route(self):
        response = self.client.get("/runtime")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Runtime", response.data)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "UP")

if __name__ == "__main__":
    unittest.main()
