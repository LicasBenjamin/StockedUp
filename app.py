import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g, flash, session
from functools import wraps
from werkzeug.security import check_password_hash 

# ——— Configuration ———
DATABASE = 'stockedup.db'
SECRET_KEY = '887ea39f980e97679e6c20d612bac0fe'

# --->>> INITIALIZE FLASK APP <<<---
app = Flask(__name__)
# -------------------------------------
app.config['DATABASE'] = DATABASE
app.config['SECRET_KEY'] = SECRET_KEY

# ——— Database Helpers ———
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        try:
            db = sqlite3.connect(app.config['DATABASE'])
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            g._database = db
            print("Database connection opened.")
        except sqlite3.Error as e:
            print(f"DATABASE CONNECTION ERROR: {e}")
            flash(f"Database connection error: {e}", "danger")
            return None
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        print("Database connection closed.")

def query_db(query, args=(), one=False):
    db = get_db()
    if not db: return None
    cursor = None
    try:
        cursor = db.cursor()
        print(f"Executing DB query: {query} | args: {args}")
        cursor.execute(query, args)
        is_select_query = query.strip().upper().startswith("SELECT")
        if is_select_query:
            rows = cursor.fetchall()
            print("SELECT query executed.")
        else:
            db.commit(); rows = []
            print("Non-SELECT query executed and committed.")
        result = (rows[0] if rows else None) if one else rows
        return result
    except sqlite3.Error as e:
        print(f"DATABASE QUERY/EXECUTION ERROR: {e}"); print(f"Failed Query: {query} | Args: {args}")
        flash(f"Database operation failed: {e}", "danger")
        return None
    finally:
        if cursor: cursor.close()


# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# ——— CORE Routes (Login, Logout, Index) ———
@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('view_inventory'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session: return redirect(url_for('view_inventory'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_action():
    username_attempt = request.form.get('username')
    password_attempt = request.form.get('password')
    print(f"Login attempt: {username_attempt}")
    if not username_attempt or not password_attempt:
        flash("Username and Password are required.", "danger"); return render_template('login.html')
    user_sql = "SELECT UserID, Username, PasswordHash FROM Users WHERE Username = ?"
    user = query_db(user_sql, [username_attempt], one=True)
    if user and check_password_hash(user['PasswordHash'], password_attempt):
        session.clear()
        session['user_id'] = user['UserID']
        session['username'] = user['Username']
        print(f"Login successful, session created for user ID: {session['user_id']}")
        flash(f"Login successful! Welcome {session.get('username','User')}.", 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('view_inventory'))
    else:
        print("Login failed.")
        flash('Invalid username or password.', 'danger')
        return render_template('login.html')

@app.route('/logout')
def logout_action():
    user_id_logged_out = session.get('user_id', 'Unknown')
    print(f"Logging out user ID: {user_id_logged_out}")
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login_page'))


# --- Item CRUD & View Routes ---
@app.route('/inventory')
@login_required
def view_inventory():
    print(f"Accessing /inventory route as user ID: {session.get('user_id')}")
    search_term = request.args.get('search_term', '').strip()
    category_filter = request.args.get('category_filter', '').strip()
    location_filter = request.args.get('location_filter', '').strip()

    base_query = """ SELECT i.ItemID, i.ItemName, i.Quantity, i.PurchaseDate, i.ExpirationDate, i.Notes, c.CategoryName, l.LocationName, i.CategoryID, i.LocationID, i.UserID FROM Items i LEFT JOIN Category c ON i.CategoryID = c.CategoryID LEFT JOIN Location l ON i.LocationID = l.LocationID """
    args = []; where_clauses = []
    if search_term: where_clauses.append("(i.ItemName LIKE ? OR i.Notes LIKE ?)"); term_wc = f"%{search_term}%"; args.extend([term_wc, term_wc])
    if category_filter and category_filter.isdigit(): where_clauses.append("i.CategoryID = ?"); args.append(int(category_filter))
    if location_filter and location_filter.isdigit(): where_clauses.append("i.LocationID = ?"); args.append(int(location_filter))
    where_section = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    order_clause = " ORDER BY i.ItemName ASC"
    final_query = base_query + where_section + order_clause

    items = query_db(final_query, args) or []
    print(f"Fetched {len(items)} items for inventory.")
    return render_template('view_inventory.html', items=items)

@app.route('/add', methods=['GET'])
@login_required
def add_item_form():
    print(f"Accessing /add route (GET) as user ID: {session.get('user_id')}")
    categories = query_db("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName") or []
    locations  = query_db("SELECT LocationID, LocationName FROM Location ORDER BY LocationName") or []
    return render_template('add_item.html', categories=categories, locations=locations)

@app.route('/add', methods=['POST'])
@login_required
def add_item_action():
    print(f"Accessing /add route (POST) as user ID: {session.get('user_id')}")
    user_id = session.get('user_id')
    if not user_id: flash("Your session has expired.", "warning"); return redirect(url_for('login_page'))
    item_name = request.form.get('item_name', '').strip(); category_id = request.form.get('category_id')
    location_id = request.form.get('location_id'); quantity_str = request.form.get('quantity')
    purchase_date = request.form.get('purchase_date') or None; expiration_date = request.form.get('expiration_date') or None
    notes = request.form.get('notes', '').strip() or None
    errors = []; quantity = None
    if not item_name: errors.append("Item Name is required.")
    if not category_id: errors.append("Category must be selected.")
    if not location_id: errors.append("Location must be selected.")
    if quantity_str:
        try: quantity = int(quantity_str); assert quantity >= 0
        except: errors.append("Quantity must be a non-negative integer.")
    else: errors.append("Quantity is required.")
    if errors:
        for e in errors: flash(e, 'danger')
        cats = query_db("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName") or []
        locs = query_db("SELECT LocationID, LocationName FROM Location ORDER BY LocationName") or []
        return render_template('add_item.html', categories=cats, locations=locs, submitted=request.form)
    try: cid = int(category_id); lid = int(location_id)
    except: flash("Invalid ID selected.", "danger"); return redirect(url_for('add_item_form'))
    sql = "INSERT INTO Items (ItemName, Quantity, PurchaseDate, ExpirationDate, CategoryID, LocationID, UserID, Notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    args = [item_name, quantity, purchase_date, expiration_date, cid, lid, user_id, notes]
    if query_db(sql, args) is not None: flash(f"Item '{item_name}' added successfully!", "success")
    return redirect(url_for('view_inventory'))

@app.route('/item/<int:item_id>')
@login_required
def view_item_details(item_id):
    print(f"Viewing details for item ID: {item_id} as user {session.get('user_id')}")
    sql = """SELECT i.*, c.CategoryName, l.LocationName, u.Username FROM Items i LEFT JOIN Category c ON i.CategoryID = c.CategoryID LEFT JOIN Location l ON i.LocationID = l.LocationID LEFT JOIN Users u ON i.UserID = u.UserID WHERE i.ItemID = ?"""
    item = query_db(sql, [item_id], one=True)
    if item: return render_template('view_item_details.html', item=item)
    else: flash(f"Item with ID {item_id} not found.", "danger"); return redirect(url_for('view_inventory'))

@app.route('/edit/<int:item_id>', methods=['GET'])
@login_required
def edit_item_form(item_id):
    print(f"Accessing /edit/{item_id} route (GET) as user ID: {session.get('user_id')}")
    item = query_db("SELECT * FROM Items WHERE ItemID = ?", [item_id], one=True)
    categories = query_db("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName") or []
    locations  = query_db("SELECT LocationID, LocationName FROM Location ORDER BY LocationName") or []
    if item: return render_template('edit_item.html', item=item, categories=categories, locations=locations)
    else: flash(f"Item ID {item_id} not found.", "danger"); return redirect(url_for('view_inventory'))

@app.route('/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_item_action(item_id):
    print(f"Accessing /edit/{item_id} route (POST) as user ID: {session.get('user_id')}")
    item_name = request.form.get('item_name', '').strip(); category_id = request.form.get('category_id')
    location_id = request.form.get('location_id'); quantity_str = request.form.get('quantity')
    purchase_date = request.form.get('purchase_date') or None; expiration_date = request.form.get('expiration_date') or None
    notes = request.form.get('notes', '').strip() or None
    errors = []; quantity = None
    if not item_name: errors.append("Item Name is required.")
    if not category_id: errors.append("Category must be selected.")
    if not location_id: errors.append("Location must be selected.")
    if quantity_str:
        try: quantity = int(quantity_str); assert quantity >= 0
        except: errors.append("Quantity must be a non-negative integer.")
    else: errors.append("Quantity is required.")
    if errors:
         for e in errors: flash(e, 'danger')
         item = query_db("SELECT * FROM Items WHERE ItemID = ?", [item_id], one=True)
         cats = query_db("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName") or []
         locs = query_db("SELECT LocationID, LocationName FROM Location ORDER BY LocationName") or []
         if not item: flash("Item not found.", "danger"); return redirect(url_for('view_inventory'))
         return render_template('edit_item.html', item=item, categories=cats, locations=locs, submitted=request.form)
    try: cid = int(category_id); lid = int(location_id)
    except: flash("Invalid ID selected.", "danger"); return redirect(url_for('edit_item_form', item_id=item_id))
    sql = "UPDATE Items SET ItemName = ?, Quantity = ?, PurchaseDate = ?, ExpirationDate = ?, CategoryID = ?, LocationID = ?, Notes = ? WHERE ItemID = ?"
    args = [item_name, quantity, purchase_date, expiration_date, cid, lid, notes, item_id]
    if query_db(sql, args) is not None: flash(f"Item '{item_name}' updated successfully!", "success")
    return redirect(url_for('view_inventory'))

@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item_action(item_id):
    print(f"Accessing /delete/{item_id} route (POST) as user ID: {session.get('user_id')}")
    item = query_db("SELECT ItemName FROM Items WHERE ItemID = ?", [item_id], one=True)
    name = f"'{item['ItemName']}' (ID: {item_id})" if item else f"ID {item_id}"
    sql = "DELETE FROM Items WHERE ItemID = ?"
    args = [item_id]
    if query_db(sql, args) is not None: flash(f"Item {name} deleted successfully!", "success")
    return redirect(url_for('view_inventory'))

@app.route('/search', methods=['GET'])
@login_required
def search_items_form():
    print(f"Accessing /search route (GET) as user ID: {session.get('user_id')}")
    categories = query_db("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName") or []
    locations  = query_db("SELECT LocationID, LocationName FROM Location ORDER BY LocationName") or []
    return render_template('search_items.html', categories=categories, locations=locations)


# --- Category Management Routes ---
@app.route('/categories')
@login_required
def manage_categories():
    print("Accessing /categories route")
    categories = query_db("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName") or []
    return render_template('manage_categories.html', categories=categories)

@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    category_name = request.form.get('category_name', '').strip()
    if not category_name: flash("Category Name cannot be empty.", "danger"); return redirect(url_for('manage_categories'))
    existing = query_db("SELECT CategoryID FROM Category WHERE LOWER(CategoryName) = LOWER(?)", [category_name], one=True)
    if existing: flash(f"Category '{category_name}' already exists.", "warning")
    else:
        sql = "INSERT INTO Category (CategoryName) VALUES (?)"
        if query_db(sql, [category_name]) is not None: flash(f"Category '{category_name}' added successfully.", "success")
    return redirect(url_for('manage_categories'))

@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    print(f"Attempting to delete category ID: {category_id}")
    category = query_db("SELECT CategoryName FROM Category WHERE CategoryID = ?", [category_id], one=True)
    name = f"'{category['CategoryName']}' (ID: {category_id})" if category else f"ID {category_id}"
    sql = "DELETE FROM Category WHERE CategoryID = ?"
    if query_db(sql, [category_id]) is not None: flash(f"Category {name} deleted. Associated items are now uncategorized.", "success")
    return redirect(url_for('manage_categories'))
# --- End Category Management ---

# --- Location Management Routes (Corrected - Single block) ---
@app.route('/locations')
@login_required
def manage_locations():
    print("Accessing /locations route")
    locations = query_db("SELECT LocationID, LocationName FROM Location ORDER BY LocationName") or []
    return render_template('manage_locations.html', locations=locations)

@app.route('/add_location', methods=['POST'])
@login_required
def add_location():
    location_name = request.form.get('location_name', '').strip()
    if not location_name: flash("Location Name cannot be empty.", "danger"); return redirect(url_for('manage_locations'))
    existing = query_db("SELECT LocationID FROM Location WHERE LOWER(LocationName) = LOWER(?)", [location_name], one=True)
    if existing: flash(f"Location '{location_name}' already exists.", "warning")
    else:
        sql = "INSERT INTO Location (LocationName) VALUES (?)"
        if query_db(sql, [location_name]) is not None: flash(f"Location '{location_name}' added successfully.", "success")
    return redirect(url_for('manage_locations'))

@app.route('/delete_location/<int:location_id>', methods=['POST'])
@login_required
def delete_location(location_id):
    print(f"Attempting to delete location ID: {location_id}")
    location = query_db("SELECT LocationName FROM Location WHERE LocationID = ?", [location_id], one=True)
    name = f"'{location['LocationName']}' (ID: {location_id})" if location else f"ID {location_id}"
    sql = "DELETE FROM Location WHERE LocationID = ?"
    if query_db(sql, [location_id]) is not None: flash(f"Location {name} deleted. Associated items location is now unassigned.", "success")
    return redirect(url_for('manage_locations'))
# --- End Location Management ---


# --- Main execution ---
if __name__ == '__main__':
    # Minimal check for werkzeug at runtime
    try:
        from werkzeug.security import check_password_hash
        print("Werkzeug security functions loaded.")
    except ImportError:
        print("!!! WARNING: werkzeug.security not found or import failed. Login password checking will fail. !!!")
        # Consider exiting if login is critical: import sys; sys.exit(1)
    app.run(debug=True, port=5000)