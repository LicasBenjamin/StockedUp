# StockedUp

**StockedUp** is a powerful household inventory management web app built to simplify organization. Track items by name, category, location, quantity, expiration or purchase date,
add custom notes, and search or update everything effortlessly in one place.

![StockedUpDemo](https://github.com/user-attachments/assets/2c564736-d279-41d9-b40d-e4406d8cf2c9)

## Features

- **Inventory view** - Browse items with search and filters (category, location)
- **Item management** - Add, edit, view details, and delete items
- **Categories & locations** - Manage categories and storage locations
- **Search** - Find items by name or notes, filter by category/location

## Project Structure

```
StockedUp/
├── app.py              # Flask app, routes, and database helpers
├── init_db.py          # Creates/resets the SQLite database from create.sql
├── create.sql          # Database schema (Users, Category, Location, Items)
├── stockedup.db       # SQLite database (created by init_db.py)
├── static/            # CSS, JS, images
├── templates/         # HTML templates
└── venv/              # Virtual environment (create with python -m venv venv)
```

## Prerequisites

- **Python 3.8+**
- **pip** (Python package installer)

## App Setup

### 1. Clone or open the project

```bash
cd /path/to/StockedUp
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install flask
```

### 4. (Optional) Initialize the database

The following can be skipped if you wish to use the default values in the current stockedup.db file.
The following command creates `stockedup.db` and the tables from `create.sql`. **Warning:** If `stockedup.db` already exists, it will be removed and recreated.

```bash
python init_db.py
```

### 5. Start the application

```bash
python app.py
```

## Using the App

1) Open the app at **http://127.0.0.1:5000** in your browser
2) log in with the default credentials
    - Username: admin
    - Password: password
3) Add designated categories and locations before adding items.
4) Start managing your inventory with ease.

## Quick Reference

| Action        | Command / URL              |
|---------------|----------------------------|
| Run app       | `python app.py`            |
| Reset DB      | `python init_db.py`        |
| App URL       | http://127.0.0.1:5000      |
| Login         | `/login`                   |
| Inventory     | `/inventory` (after login) |
| Add item      | `/add`                     |
| Categories    | `/categories`              |
| Locations     | `/locations`               |

## Notes

- **Debug mode:** The app runs with `debug=True` on port 5000. Do not use this in production.
- **Database:** All data is stored in `stockedup.db`. Back it up if you need to preserve your inventory.
