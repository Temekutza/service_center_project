import unittest
import sqlite3
import tempfile
import os
import json
import csv
from unittest.mock import patch


SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "database", "schema.sql")


class TestBase(unittest.TestCase):
    """Базовый класс: поднимает временную SQLite БД перед каждым тестом."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.close()

        def make_conn():
            c = sqlite3.connect(self.db_path)
            c.execute("PRAGMA foreign_keys = ON")
            return c

        self._patches = [
            patch("crud.clients.get_connection", side_effect=make_conn),
            patch("crud.devices.get_connection", side_effect=make_conn),
            patch("crud.repairs.get_connection", side_effect=make_conn),
            patch("utils.export.get_connection", side_effect=make_conn),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        os.unlink(self.db_path)


# ---------------------------------------------------------------------------
# Клиенты
# ---------------------------------------------------------------------------

class TestClients(TestBase):

    def test_add_client_returns_in_list(self):
        from crud.clients import add_client, get_clients
        add_client("Иван", "71234567890", "ivan@mail.ru")
        rows = get_clients()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Иван")
        self.assertEqual(rows[0][2], "71234567890")
        self.assertEqual(rows[0][3], "ivan@mail.ru")

    def test_add_multiple_clients(self):
        from crud.clients import add_client, get_clients
        add_client("Анна", "70000000001", "anna@mail.ru")
        add_client("Борис", "70000000002", "boris@mail.ru")
        self.assertEqual(len(get_clients()), 2)

    def test_get_clients_empty(self):
        from crud.clients import get_clients
        self.assertEqual(get_clients(), [])

    def test_delete_client_removes_record(self):
        from crud.clients import add_client, get_clients, delete_client
        add_client("Удаляемый", "70000000000", "del@mail.ru")
        client_id = get_clients()[0][0]
        delete_client(client_id)
        self.assertEqual(get_clients(), [])

    def test_delete_nonexistent_client_no_error(self):
        from crud.clients import delete_client
        delete_client(9999)  # не должно бросать исключение

    def test_client_id_autoincrement(self):
        from crud.clients import add_client, get_clients
        add_client("А", "1", "a@a.ru")
        add_client("Б", "2", "b@b.ru")
        ids = [r[0] for r in get_clients()]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(set(ids)), 2)


# ---------------------------------------------------------------------------
# Устройства
# ---------------------------------------------------------------------------

class TestDevices(TestBase):

    def _add_client(self, name="Клиент"):
        from crud.clients import add_client, get_clients
        add_client(name, "70000000000", "test@test.ru")
        return get_clients()[-1][0]

    def test_add_device_appears_in_list(self):
        from crud.devices import add_device, get_devices
        cid = self._add_client()
        add_device(cid, "Ноутбук", "Lenovo", "IdeaPad 3")
        rows = get_devices()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "Ноутбук")
        self.assertEqual(rows[0][3], "Lenovo")
        self.assertEqual(rows[0][4], "IdeaPad 3")

    def test_device_links_to_client_name(self):
        from crud.devices import add_device, get_devices
        cid = self._add_client("Мария")
        add_device(cid, "Телефон", "Samsung", "Galaxy S21")
        rows = get_devices()
        self.assertEqual(rows[0][1], "Мария")

    def test_multiple_devices_for_one_client(self):
        from crud.devices import add_device, get_devices
        cid = self._add_client()
        add_device(cid, "Ноутбук", "HP", "Pavilion")
        add_device(cid, "Телефон", "Apple", "iPhone 14")
        self.assertEqual(len(get_devices()), 2)

    def test_get_devices_empty(self):
        from crud.devices import get_devices
        self.assertEqual(get_devices(), [])

    def test_cascade_delete_removes_devices(self):
        from crud.clients import add_client, get_clients, delete_client
        from crud.devices import add_device, get_devices
        cid = self._add_client()
        add_device(cid, "ПК", "Asus", "ROG")
        delete_client(cid)
        self.assertEqual(get_devices(), [])


# ---------------------------------------------------------------------------
# Ремонты
# ---------------------------------------------------------------------------

class TestRepairs(TestBase):

    def _setup_device(self):
        from crud.clients import add_client, get_clients
        from crud.devices import add_device, get_devices
        add_client("Тест", "70000000000", "t@t.ru")
        cid = get_clients()[-1][0]
        add_device(cid, "Ноутбук", "Dell", "XPS 15")
        return get_devices()[-1][0]

    def test_add_repair_appears_in_list(self):
        from crud.repairs import add_repair, get_repairs
        did = self._setup_device()
        add_repair(did, "Не включается", 1500.0)
        rows = get_repairs()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "Не включается")
        self.assertEqual(rows[0][4], 1500.0)

    def test_default_status_is_accepted(self):
        from crud.repairs import add_repair, get_repairs
        did = self._setup_device()
        add_repair(did, "Сломан экран", 3000.0)
        status = get_repairs()[0][3]
        self.assertEqual(status, "Принят")

    def test_update_status_changes_value(self):
        from crud.repairs import add_repair, get_repairs, update_status
        did = self._setup_device()
        add_repair(did, "Проблема", 500.0)
        repair_id = get_repairs()[0][0]
        update_status(repair_id, "Выполнен")
        self.assertEqual(get_repairs()[0][3], "Выполнен")

    def test_update_status_nonexistent_no_error(self):
        from crud.repairs import update_status
        update_status(9999, "Выполнен")  # не должно бросать исключение

    def test_repair_contains_device_model(self):
        from crud.repairs import add_repair, get_repairs
        did = self._setup_device()
        add_repair(did, "Медленно работает", 800.0)
        self.assertEqual(get_repairs()[0][1], "XPS 15")

    def test_multiple_repairs(self):
        from crud.repairs import add_repair, get_repairs
        did = self._setup_device()
        add_repair(did, "Проблема 1", 100.0)
        add_repair(did, "Проблема 2", 200.0)
        self.assertEqual(len(get_repairs()), 2)

    def test_repair_price_stored_correctly(self):
        from crud.repairs import add_repair, get_repairs
        did = self._setup_device()
        add_repair(did, "Замена батареи", 2499.99)
        self.assertAlmostEqual(get_repairs()[0][4], 2499.99, places=2)

    def test_date_created_not_empty(self):
        from crud.repairs import add_repair, get_repairs
        did = self._setup_device()
        add_repair(did, "Диагностика", 0.0)
        date_created = get_repairs()[0][5]
        self.assertIsNotNone(date_created)
        self.assertRegex(date_created, r"\d{4}-\d{2}-\d{2}")


# ---------------------------------------------------------------------------
# Экспорт
# ---------------------------------------------------------------------------

class TestExport(TestBase):

    def _add_clients(self):
        from crud.clients import add_client
        add_client("Экспорт1", "71111111111", "exp1@mail.ru")
        add_client("Экспорт2", "72222222222", "exp2@mail.ru")

    def test_export_csv_creates_file(self):
        from utils.export import export_clients_csv
        self._add_clients()
        path = os.path.join(tempfile.gettempdir(), "test_clients.csv")
        export_clients_csv(path)
        self.assertTrue(os.path.exists(path))
        os.unlink(path)

    def test_export_csv_header_and_rows(self):
        from utils.export import export_clients_csv
        self._add_clients()
        path = os.path.join(tempfile.gettempdir(), "test_clients.csv")
        export_clients_csv(path)
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(rows[0], ["ID", "Name", "Phone", "Email"])
        self.assertEqual(len(rows), 3)  # заголовок + 2 клиента
        os.unlink(path)

    def test_export_csv_correct_values(self):
        from utils.export import export_clients_csv
        self._add_clients()
        path = os.path.join(tempfile.gettempdir(), "test_clients.csv")
        export_clients_csv(path)
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        names = [r[1] for r in rows[1:]]
        self.assertIn("Экспорт1", names)
        self.assertIn("Экспорт2", names)
        os.unlink(path)

    def test_export_json_creates_file(self):
        from utils.export import export_clients_json
        self._add_clients()
        path = os.path.join(tempfile.gettempdir(), "test_clients.json")
        export_clients_json(path)
        self.assertTrue(os.path.exists(path))
        os.unlink(path)

    def test_export_json_structure(self):
        from utils.export import export_clients_json
        self._add_clients()
        path = os.path.join(tempfile.gettempdir(), "test_clients.json")
        export_clients_json(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)
        self.assertIn("id", data[0])
        self.assertIn("name", data[0])
        self.assertIn("phone", data[0])
        self.assertIn("email", data[0])
        os.unlink(path)

    def test_export_json_correct_values(self):
        from utils.export import export_clients_json
        self._add_clients()
        path = os.path.join(tempfile.gettempdir(), "test_clients.json")
        export_clients_json(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        names = [d["name"] for d in data]
        self.assertIn("Экспорт1", names)
        self.assertIn("Экспорт2", names)
        os.unlink(path)

    def test_export_empty_db_csv(self):
        from utils.export import export_clients_csv
        path = os.path.join(tempfile.gettempdir(), "test_empty.csv")
        export_clients_csv(path)
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(rows[0], ["ID", "Name", "Phone", "Email"])
        self.assertEqual(len(rows), 1)  # только заголовок
        os.unlink(path)

    def test_export_empty_db_json(self):
        from utils.export import export_clients_json
        path = os.path.join(tempfile.gettempdir(), "test_empty.json")
        export_clients_json(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, [])
        os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
