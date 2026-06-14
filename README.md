# Little Lemon Restaurant API

A modern, robust, and fully featured REST API for the **Little Lemon Restaurant** built with **Django**, **Django REST Framework (DRF)**, and **Djoser** (Token-based Authentication).

This API handles user management, restaurant menu item cataloging, shopping carts, order creation, and role-based order routing for managers and delivery crew members.

---

## 🛠️ Tech Stack

* **Core Framework:** [Django](https://www.djangoproject.com/)
* **API Toolkit:** [Django REST Framework (DRF)](https://www.django-rest-framework.org/)
* **Authentication:** [Djoser](https://djoser.readthedocs.io/) (Token Authentication)
* **Package Management:** Pipenv
* **Database:** SQLite (Default for development)
* **Python Version:** 3.13

---

## 📂 Project Structure

* `LittleLemon/` - Main project configuration, settings, and root URL routing.
* `LittleLemonAPI/` - Core application containing models, serializers, views, permissions, and API endpoints.
* `setup_db.py` - Database seeding script that prepares the database with groups, default accounts, and categories/menu items.
* `notes.txt` - Developer reference sheet for pre-configured credentials.
* `Pipfile` & `Pipfile.lock` - Dependency files.

---

## 🚀 Getting Started & Setup

Follow these steps to run the project locally on your machine.

### 1. Prerequisites
Ensure you have **Python 3.13+** and **Pipenv** installed on your system.

### 2. Install Dependencies
Run the following command in the project root to install the packages:
```bash
pipenv install
```

### 3. Activate the Environment
Enter the virtual environment shell:
```bash
pipenv shell
```

### 4. Database Migrations
Create and apply database migrations to initialize the SQLite database:
```bash
python manage.py migrate
```

### 5. Seed the Database
Run the pre-configured database setup script to create administrative/roles groups, default users, categories, and initial menu items:
```bash
python setup_db.py
```

### 6. Run the Development Server
Start the local server:
```bash
python manage.py runserver
```
Once the server is running, the API will be available at: **`http://127.0.0.1:8000/`**

---

## 🔐 Pre-configured User Accounts

The seeding script generates four default users mapping to different roles. You can use these credentials to authenticate and test role-based access policies:

| Role | Username | Password | Assigned Group | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Superuser/Admin** | `admin` | `adminpassword123` | *Superuser privileges* | Full access, manages the Manager group |
| **Manager** | `manageruser` | `managerpassword123` | `Manager` | Manages menu items, categories, orders, and Delivery Crew |
| **Delivery Crew** | `crewuser` | `crewpassword123` | `Delivery crew` | Views assigned orders, updates status to completed |
| **Customer** | `customeruser` | `customerpassword123` | *None* | Views menu, adds items to cart, places and views orders |

---

## 📡 API Endpoints & Permissions Matrix

All API endpoints are prefixed with `/api/`.

### 1. User Registration & Authentication (Token Auth)

| Endpoint | Method | Permission | Description |
| :--- | :--- | :--- | :--- |
| `/api/users/` | `POST` | Public | Register a new user account |
| `/api/users/me/` | `GET` | Authenticated | View authenticated user profile |
| `/api/token/login/` | `POST` | Public | Login with username and password to retrieve token |
| `/api/token/logout/` | `POST` | Authenticated | Logout and destroy auth token |

> **Header format for authenticated requests:**  
> `Authorization: Token <your_auth_token_here>`

---

### 2. Category & Menu Item Management

| Endpoint | Method | Permission | Description |
| :--- | :--- | :--- | :--- |
| `/api/categories` | `GET` | Authenticated | Retrieve all categories |
| `/api/categories` | `POST` | Manager / Admin | Create a new category |
| `/api/menu-items` | `GET` | Authenticated | Retrieve all menu items (Supports search, filtering, ordering) |
| `/api/menu-items` | `POST` | Manager / Admin | Create a new menu item |
| `/api/menu-items/<id>` | `GET` | Authenticated | Retrieve a single menu item details |
| `/api/menu-items/<id>` | `PUT` / `PATCH` | Manager / Admin | Update a menu item |
| `/api/menu-items/<id>` | `DELETE` | Manager / Admin | Delete a menu item |

#### 🔍 Menu Item Query Parameters:
* **Filtering by category slug:** `/api/menu-items?category=mains`
* **Filtering by maximum price:** `/api/menu-items?to_price=10.00`
* **Searching by title:** `/api/menu-items?search=Hummus`
* **Ordering by price/title:** `/api/menu-items?ordering=price` or `/api/menu-items?ordering=-price`

---

### 3. User Group & Role Management

| Endpoint | Method | Permission | Description |
| :--- | :--- | :--- | :--- |
| `/api/groups/manager/users` | `GET` | Admin | List all Managers |
| `/api/groups/manager/users` | `POST` | Admin | Add user to Manager group (expects `{"username": "<name>"}`) |
| `/api/groups/manager/users/<id>` | `DELETE` | Admin | Remove user from Manager group |
| `/api/groups/delivery-crew/users` | `GET` | Manager / Admin | List all Delivery Crew members |
| `/api/groups/delivery-crew/users` | `POST` | Manager / Admin | Add user to Delivery Crew group (expects `{"username": "<name>"}`) |
| `/api/groups/delivery-crew/users/<id>` | `DELETE` | Manager / Admin | Remove user from Delivery Crew group |

---

### 4. Cart Management (Customers Only)

| Endpoint | Method | Permission | Description |
| :--- | :--- | :--- | :--- |
| `/api/cart/menu-items` | `GET` | Customer | Retrieve items currently in the user's cart |
| `/api/cart/menu-items` | `POST` | Customer | Add a menu item to the cart (expects `{"menuitem": <id>, "quantity": <qty>}`) |
| `/api/cart/menu-items` | `DELETE` | Customer | Clear/empty the cart |

---

### 5. Order Management

| Endpoint | Method | Permission | Description |
| :--- | :--- | :--- | :--- |
| `/api/orders` | `GET` | Authenticated | **Customer:** View own orders<br>**Delivery Crew:** View assigned orders<br>**Manager:** View all orders in the system |
| `/api/orders` | `POST` | Customer | Place an order. Converts current cart items into order items and clears cart. |
| `/api/orders/<id>` | `GET` | Authenticated | View details of a specific order (if authorized) |
| `/api/orders/<id>` | `PUT` / `PATCH` | Manager | Assign delivery crew to order, update status, or update order fields |
| `/api/orders/<id>` | `PATCH` | Delivery Crew | Update order `status` (completed or not). Other updates are forbidden. |
| `/api/orders/<id>` | `DELETE` | Manager | Delete/cancel order |
