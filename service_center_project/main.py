from database.db import init_db
from crud.clients import *
from crud.devices import *
from crud.repairs import *
from utils.export import *

print("Первая неделя практики — изменения внесены")

def menu():
    while True:
        print("\n=== Сервисный центр ===")
        print("1. Добавить клиента")
        print("2. Показать клиентов")
        print("3. Добавить устройство")
        print("4. Показать устройства")
        print("5. Создать заявку на ремонт")
        print("6. Показать ремонты")
        print("7. Изменить статус ремонта")
        print("8. Экспорт клиентов в CSV")
        print("9. Экспорт клиентов в JSON")
        print("0. Выход")

        choice = input("Выберите действие: ")

        if choice == "1":
            name = input("Имя: ")
            phone = input("Телефон: ")
            email = input("Email: ")
            add_client(name, phone, email)

        elif choice == "2":
            for row in get_clients():
                print(row)

        elif choice == "3":
            client_id = int(input("ID клиента: "))
            device_type = input("Тип устройства: ")
            brand = input("Бренд: ")
            model = input("Модель: ")
            add_device(client_id, device_type, brand, model)

        elif choice == "4":
            for row in get_devices():
                print(row)

        elif choice == "5":
            device_id = int(input("ID устройства: "))
            problem = input("Описание проблемы: ")
            price = float(input("Стоимость: "))
            add_repair(device_id, problem, price)

        elif choice == "6":
            for row in get_repairs():
                print(row)

        elif choice == "7":
            repair_id = int(input("ID ремонта: "))
            status = input("Новый статус: ")
            update_status(repair_id, status)

        elif choice == "8":
            export_clients_csv("clients.csv")
            print("Экспорт выполнен: clients.csv")

        elif choice == "9":
            export_clients_json("clients.json")
            print("Экспорт выполнен: clients.json")

        elif choice == "0":
            break

if __name__ == "__main__":
    init_db()
    menu()
