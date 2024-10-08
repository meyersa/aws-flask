from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from math import radians, sin, cos, sqrt, atan2
import pymysql.cursors
import os

db_host = os.getenv("MYSQL_HOST", "localhost")
db_user = os.getenv("MYSQL_USER", "root")
db_password = os.getenv("MYSQL_PASS", "password")
db_db = os.getenv("MYSQL_DB", "db")

# Create Flask
app = Flask(__name__)

# Connect to DB
db = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_db,
    cursorclass=pymysql.cursors.DictCursor,
)


# Calculate distance between lat/long
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of Earth in km

    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
        radians, [lat1, lon1, lat2, lon2])

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance_km = R * c  # Result in km

    # Convert kilometers to miles
    distance_miles = distance_km * 0.621371

    return distance_miles


# Get lat/long (rough) from ip
def get_user_location(user_ip):
    ip_api_url = f"http://ip-api.com/json/{user_ip}"
    try:
        response = requests.get(ip_api_url)
        if response.status_code == 200:
            location_data = response.json()
            city = location_data.get("city")
            country = location_data.get("country")
            user_lat = location_data.get("lat")
            user_lon = location_data.get("lon")
            return city, country, user_lat, user_lon
    except Exception as e:
        print(f"Error fetching user location: {e}")
    return None, None, None, None


# Run through list of locations and compare to find shortest
def nearest_location(user_lat, user_lon, locations):
    return min(
        locations,
        key=lambda loc: calculate_distance(
            user_lat, user_lon, loc["latitude"], loc["longitude"]
        ),
    )


# Home route
@app.route("/")
def home():
    user_ip = None

    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        user_ip = "1.1.1.1"

    else:
        user_ip = request.environ['HTTP_X_FORWARDED_FOR']

    user_city, user_country, user_lat, user_lon = get_user_location(user_ip)
    if user_lat is not None and user_lon is not None:
        try:
            with db.cursor() as cursor:
                # Get featured menu items from the database
                cursor.execute("SELECT * FROM menu_items WHERE featured = 1")
                featured_menu_items = cursor.fetchall()

                print(featured_menu_items)
                # Get other menu items from the database
                cursor.execute("SELECT * FROM menu_items WHERE featured = 0")
                other_menu_items = cursor.fetchall()

                # Get all restaurant locations from the database
                cursor.execute("SELECT * FROM restaurant_locations")
                restaurant_locations = cursor.fetchall()

                # Get the nearest location
                nearest = nearest_location(
                    user_lat, user_lon, restaurant_locations)
                nearest_location_name = nearest["name"]
                nearest_location_distance = round(
                    calculate_distance(
                        user_lat, user_lon, nearest["latitude"], nearest["longitude"]
                    ),
                    2,
                )

                # Calculate distances to all locations and sort by distance
                distances_to_all = [
                    (
                        loc["name"],
                        round(
                            calculate_distance(
                                user_lat, user_lon, loc["latitude"], loc["longitude"]
                            ),
                            2,
                        ),
                    )
                    for loc in restaurant_locations
                ]
                distances_to_all.sort(key=lambda x: x[1])

                # Get the top 3 closest locations
                top_3_closest = distances_to_all[:3]

                return render_template(
                    "index.html",
                    user_location=f"{user_city}, {user_country}",
                    nearest_location_name=nearest_location_name,
                    nearest_location_distance=nearest_location_distance,
                    top_3_closest=top_3_closest,
                    featured_menu_items=featured_menu_items,
                    other_menu_items=other_menu_items,
                    restaurant_locations=restaurant_locations,
                )
        except Exception as e:
            print(f"Error executing SQL query: {e}")

    # Fail case
    return render_template(
        "index.html",
        user_location="Unknown",
        nearest_location_name=None,
        nearest_location_distance=None,
        top_3_closest=None,
        featured_menu_items=[],
        other_menu_items=[],
        restaurant_locations=[],
    )


# Define route to render the menu page
@app.route("/menu")
def menu():
    try:
        with db.cursor() as cursor:
            # Get menu items from the database
            cursor.execute("SELECT * FROM menu_items")
            menu_items = cursor.fetchall()

            return render_template("menu.html", menu_items=menu_items)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return render_template("menu.html", menu_items=[])


# About route
@app.route("/about")
def about():
    return render_template("about.html")


# Priv policy rooute
@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


# Route for customer dashboard
@app.route("/customer")
def customer_dashboard():
    try:
        with db.cursor() as cursor:
            # Get menu items from the database
            cursor.execute("SELECT * FROM menu_items")
            menu_items = cursor.fetchall()

            # Get orders placed by the user
            cursor.execute("SELECT * FROM orders")
            orders = cursor.fetchall()

            # Parse the 'items' field into a list for each order
            for order in orders:
                order["items"] = order["items"].split(", ")

            return render_template(
                "dashboard.html",
                user_role="customer",
                menu_items=menu_items,
                orders=orders,
            )
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return render_template(
            "dashboard.html", user_role="customer", menu_items=[], orders=[]
        )


# Route for staff dashboard
@app.route("/staff")
def staff_dashboard():
    try:
        with db.cursor() as cursor:
            # Get all orders
            cursor.execute("SELECT * FROM orders")
            orders = cursor.fetchall()

            # Parse the 'items' field into a list for each order
            for order in orders:
                order["items"] = order["items"].split(", ")

            return render_template("dashboard.html", user_role="staff", orders=orders)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return render_template("dashboard.html", user_role="staff", orders=[])


# Route for manager dashboard
@app.route("/manager")
def manager_dashboard():
    try:
        with db.cursor() as cursor:
            # Get menu items from the database
            cursor.execute("SELECT * FROM menu_items")
            menu_items = cursor.fetchall()

            # Get all restaurant locations
            cursor.execute("SELECT * FROM restaurant_locations")
            locations = cursor.fetchall()

            # Get all orders
            cursor.execute("SELECT * FROM orders")
            orders = cursor.fetchall()

            # Get all users
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()

            # Parse the 'items' field into a list for each order
            for order in orders:
                order["items"] = order["items"].split(", ")

            return render_template(
                "dashboard.html",
                user_role="manager",
                menu_items=menu_items,
                locations=locations,
                orders=orders,
                users=users,
            )
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return render_template(
            "dashboard.html",
            user_role="manager",
            menu_items=[],
            locations=[],
            orders=[],
            users=[],
        )


# Route for login page (api)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            with db.cursor() as cursor:
                # Check if user exists and credentials are correct
                cursor.execute(
                    "SELECT * FROM users WHERE username = %s AND password = %s",
                    (username, password),
                )
                user = cursor.fetchone()
                if user:
                    role = user["role"]
                    # Redirect to appropriate page based on role
                    if role == "customer":
                        return redirect(url_for("customer_dashboard"))
                    elif role == "staff":
                        return redirect(url_for("staff_dashboard"))
                    elif role == "manager":
                        return redirect(url_for("manager_dashboard"))
        except Exception as e:
            print(f"Error executing SQL query: {e}")

        # If credentials are incorrect or user doesn't exist, reload login page
        return render_template(
            "login.html", message="Invalid credentials. Please try again."
        )

    # For GET request, render the login page
    return render_template("login.html")


# Route for creating an order (api)
@app.route("/create_order", methods=["POST"])
def create_order():
    if request.method == "POST":
        items = ", ".join(request.form.getlist("items"))

        try:
            with db.cursor() as cursor:
                # Insert new order into the database
                cursor.execute(
                    "INSERT INTO orders (customer, items, status) VALUES (%s, %s, %s)",
                    ("customer1", items, "placed"),
                )
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error creating order: {e}")
            db.rollback()

    # Handle invalid form submission or errors
    return "Error creating order"


# Route for updating order status (api)
@app.route("/update_order_status", methods=["POST"])
def update_order_status():
    data = request.get_json()
    order_id = data["orderId"]
    new_status = data["newStatus"]

    try:
        with db.cursor() as cursor:
            # Update the status of the order in the database
            cursor.execute(
                "UPDATE orders SET status = %s WHERE id = %s", (
                    new_status, order_id)
            )
            db.commit()
            return "Success"
    except Exception as e:
        print(f"Error updating order status: {e}")
        db.rollback()
        return "Failed to update order status"


# Route for deleting an order (api)
@app.route("/delete_order", methods=["POST"])
def delete_order():
    order_id = request.form["orderId"]

    try:
        with db.cursor() as cursor:
            # Delete the order from the database
            cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            db.commit()
            return "Success"
    except Exception as e:
        print(f"Error deleting order: {e}")
        db.rollback()
        return "Error deleting order"


# Route for creating a user (api)
@app.route("/create_user", methods=["POST"])
def create_user():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        try:
            with db.cursor() as cursor:
                # Insert new user into the database
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    (username, password, role),
                )
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error creating user: {e}")
            db.rollback()

    # Handle invalid form submission or errors
    return "Error creating user"


# Route for updating a user's role (api)
@app.route("/update_user_role", methods=["POST"])
def update_user_role():
    if request.method == "POST":
        username = request.form.get("username")
        role = request.form.get("role")

        try:
            with db.cursor() as cursor:
                # Update the role of the user in the database
                cursor.execute(
                    "UPDATE users SET role = %s WHERE username = %s", (
                        role, username)
                )
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error updating user role: {e}")
            db.rollback()
            return "Error updating user role"


# Route for deleting a user (api)
@app.route("/delete_user", methods=["POST"])
def delete_user():
    if request.method == "POST":
        username = request.form.get("username")

        try:
            with db.cursor() as cursor:
                # Delete the user from the database
                cursor.execute(
                    "DELETE FROM users WHERE username = %s", (username,))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error deleting user: {e}")
            db.rollback()
            return "Error deleting user"


# Route for creating a location (api)
@app.route("/create_location", methods=["POST"])
def create_location():
    if request.method == "POST":
        name = request.form.get("name")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        try:
            with db.cursor() as cursor:
                # Insert new location into the database
                cursor.execute(
                    "INSERT INTO restaurant_locations (name, latitude, longitude) VALUES (%s, %s, %s)",
                    (name, latitude, longitude),
                )
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error creating location: {e}")
            db.rollback()

    # Handle invalid form submission or errors
    return "Error creating location"


# Route for deleting a location (api)
@app.route("/delete_location", methods=["POST"])
def delete_location():
    if request.method == "POST":
        name = request.form.get("name")

        try:
            with db.cursor() as cursor:
                # Delete the location from the database
                cursor.execute(
                    "DELETE FROM restaurant_locations WHERE name = %s", (name,)
                )
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error deleting location: {e}")
            db.rollback()
            return "Error deleting location"


# Route for creating a menu item (api)
@app.route("/create_menu_item", methods=["POST"])
def create_menu_item():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        featured = int(request.form.get("featured", 0))  # Convert to integer
        featured_reason = request.form.get("featured_reason")
        image_url = request.form.get(
            "image_url", "/static/food.png")  # Default value

        try:
            with db.cursor() as cursor:
                # Insert new menu item into the database
                cursor.execute(
                    "INSERT INTO menu_items (name, price, featured, featured_reason, image_url) VALUES (%s, %s, %s, %s, %s)",
                    (name, price, featured, featured_reason, image_url),
                )
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error creating menu item: {e}")
            db.rollback()

    # Handle invalid form submission or errors
    return "Error creating menu item"

# Route for updating a menu item (api)


@app.route("/update_menu_item", methods=["POST"])
def update_menu_item():
    data = request.form.to_dict()
    item_id = data.pop("id")  # Remove the id from the data

    try:
        with db.cursor() as cursor:
            # Construct the SET part of the SQL query dynamically
            set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
            # Append the id to the data values list
            data_values = list(data.values())
            data_values.append(item_id)

            # Update the menu item in the database
            cursor.execute(
                f"UPDATE menu_items SET {set_clause} WHERE id = %s", tuple(
                    data_values)
            )
            db.commit()
            return "Success"
    except Exception as e:
        print(f"Error updating menu item: {e}")
        db.rollback()
        return "Error updating menu item"


# Route for deleting a menu item (api)
@app.route("/delete_menu_item", methods=["POST"])
def delete_menu_item():
    if request.method == "POST":
        item_id = request.form.get("id")

        try:
            with db.cursor() as cursor:
                # Delete the menu item from the database
                cursor.execute(
                    "DELETE FROM menu_items WHERE id = %s", (item_id,))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error deleting menu item: {e}")
            db.rollback()
            return "Error deleting menu item"


# Function to execute SQL queries
def execute_query(sql, data=None):
    try:
        with db.cursor() as cursor:
            if data:
                cursor.execute(sql, data)
            else:
                cursor.execute(sql)
        db.commit()
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        db.rollback()


# Check if a table is empty
def is_table_empty(table_name):
    try:
        with db.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            result = cursor.fetchone()
            return result["count"] == 0
    except Exception as e:
        print(f"Error checking if table is empty: {e}")
        return True


# Insert data into tables
def insert_data(table_name, data):
    for item in data:
        columns = ", ".join(item.keys())
        values_template = ", ".join(["%s"] * len(item))

        # Convert list of items to a single string
        if "items" in item:
            item["items"] = ", ".join(item["items"])

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values_template})"
        execute_query(sql, list(item.values()))


# Create tables if they don't exist
create_menu_items_table = """
CREATE TABLE IF NOT EXISTS menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    featured INT DEFAULT 0,
    featured_reason TEXT,
    image_url VARCHAR(255)
);
"""

create_restaurant_locations_table = """
CREATE TABLE IF NOT EXISTS restaurant_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL
);
"""

create_users_table = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL
);
"""

create_orders_table = """
CREATE TABLE IF NOT EXISTS orders (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    customer VARCHAR(255) NOT NULL,
    items TEXT NOT NULL,
    status VARCHAR(50) NOT NULL
);
"""

menu_items = [
    {
        "name": "Cheeseburger",
        "price": "$80",
        "description": "A juicy burger with cheddar cheese.",
        "featured": 1,
        "featured_reason": "On sale, buy half get half off!",
        "image_url": "/static/food.png",
    },
    {
        "name": "Bacon Cheeseburger",
        "price": "$90",
        "description": "Classic cheeseburger with crispy bacon.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Chicken Tenders",
        "price": "$45",
        "description": "Frozen tenders, microwaved.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Grilled Chicken Salad",
        "price": "$40",
        "description": "Fresh iceburg lettuce with ranch dressing, croutons, and colby jack cheese.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Hot Dogs",
        "price": "$20",
        "description": "HOT DOG! GETCHA HOT DOG!",
        "image_url": "/static/food.png",
    },
    {
        "name": "Mozzarella Sticks",
        "price": "$30",
        "description": "Also microwaved",
        "image_url": "/static/food.png",
    },
    {
        "name": "Onion Rings",
        "price": "$35",
        "description": "Battered white onions, deep fried in 100% peanut oil.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Mashed Potatos",
        "price": "$35",
        "description": "Russets, mashed",
        "featured": 1,
        "featured_reason": "We expected a famine and bought too many!",
        "image_url": "/static/food.png",
    },
    {
        "name": "Mac and Cheese",
        "price": "$35",
        "description": "Gooey cheese poured overtop noodles.",
        "image_url": "/static/food.png",
    },
    {
        "name": "French Fries",
        "price": "$40",
        "description": "Russets, fried",
        "featured": 1,
        "featured_reason": "They surrendered.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Chocolate Cake",
        "price": "$35",
        "description": "Like vanilla cake, but chocolate",
        "image_url": "/static/food.png",
    },
    {
        "name": "Churros",
        "price": "$20",
        "description": "Deep fried batter covered in cinnamon sugar.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Cookies",
        "price": "$15",
        "description": "Oatmeal raisin only.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Cannoli",
        "price": "$35",
        "description": "This Italian dessert is crunchy and delicious.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Cupcakes",
        "price": "$25",
        "description": "Like the chocolate cake, but smaller.",
        "featured": 1,
        "featured_reason": "Like the normal price, but smaller",
        "image_url": "/static/food.png",
    },
]
restaurant_locations = [
    {"name": "Mount Pleasant", "latitude": 43.606950, "longitude": -84.768160},
    {"name": "Big Rapids", "latitude": 43.689480, "longitude": -85.485321},
    {"name": "Birch Run", "latitude": 43.247390, "longitude": -83.768930},
    {"name": "East Lansing", "latitude": 42.749360, "longitude": -84.448150},
]

users = [
    {"username": "customer1", "password": "password1", "role": "customer"},
    {"username": "staff1", "password": "password1", "role": "staff"},
    {"username": "manager1", "password": "password1", "role": "manager"},
]
orders = [
    {"customer": "customer1", "items": [
        "Cheeseburger", "Mac and Cheese", "Cookies"], "status": "placed"},
    {"customer": "customer2", "items": [
        "Chicken Tenders", "Onion Rings", "Churros"], "status": "delivered"},
    {"customer": "customer3", "items": ["Bacon Cheeseburger", "Chicken Tenders",
                                        "Hot Dogs", "Mozzarella Sticks", "Cannoli", "Cupcakes"], "status": "in_progress"},
]

# Execute table creation queries
execute_query(create_menu_items_table)
execute_query(create_restaurant_locations_table)
execute_query(create_users_table)
execute_query(create_orders_table)

# Insert data into tables if they are empty
if is_table_empty("menu_items"):
    insert_data("menu_items", menu_items)

if is_table_empty("restaurant_locations"):
    insert_data("restaurant_locations", restaurant_locations)

if is_table_empty("users"):
    insert_data("users", users)

if is_table_empty("orders"):
    insert_data("orders", orders)

if __name__ == "__main__":
    app.run(debug=True)
