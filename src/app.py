from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from math import radians, sin, cos, sqrt, atan2
import pymysql.cursors

db_host = "localhost"
db_user = "root"
db_password = "password"
db_db = "db"

app = Flask(__name__)

db = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_db,
    cursorclass=pymysql.cursors.DictCursor,
)


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of Earth in km

    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance_km = R * c  # Result in km

    # Convert kilometers to miles
    distance_miles = distance_km * 0.621371

    return distance_miles


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


def nearest_location(user_lat, user_lon, locations):
    return min(
        locations,
        key=lambda loc: calculate_distance(
            user_lat, user_lon, loc["latitude"], loc["longitude"]
        ),
    )


@app.route("/")
def home():
    # user_ip = request.remote_addr
    user_ip = "1.1.1.1"
    user_city, user_country, user_lat, user_lon = get_user_location(user_ip)

    if user_lat is not None and user_lon is not None:
        try:
            with db.cursor() as cursor:
                # Get all restaurant locations from the database
                cursor.execute("SELECT * FROM restaurant_locations")
                restaurant_locations = cursor.fetchall()

                # Get menu items from the database
                cursor.execute("SELECT * FROM menu_items")
                menu_items = cursor.fetchall()

                nearest = nearest_location(user_lat, user_lon, restaurant_locations)
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
                    restaurant_locations=restaurant_locations,
                    menu_items=menu_items,
                )
        except Exception as e:
            print(f"Error executing SQL query: {e}")

    return render_template(
        "index.html",
        user_location="Unknown",
        nearest_location_name=None,
        nearest_location_distance=None,
        top_3_closest=None,
        restaurant_locations=[],
        menu_items=[],
    )


# Route for login page
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

# Route for customer dashboard
@app.route("/customer")
def customer_dashboard():
    # try:
        with db.cursor() as cursor:
            # Get menu items from the database
            cursor.execute("SELECT * FROM menu_items")
            menu_items = cursor.fetchall()

            # Get orders placed by the user
            cursor.execute("SELECT * FROM orders")
            orders = cursor.fetchall()

            # Parse the 'items' field into a list for each order
            for order in orders:
                order['items'] = order['items'].split(', ')
            
            return render_template("dashboard.html", user_role="customer", menu_items=menu_items, orders=orders)
    # except Exception as e:
    #     print(f"Error executing SQL query: {e}")
    #     return render_template("dashboard.html", user_role="customer", menu_items=[], orders=[])


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
                order['items'] = order['items'].split(', ')
            
            return render_template("dashboard.html", user_role="staff", orders=orders)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return render_template("dashboard.html", user_role="staff", orders=[])


# Route for manager dashboard
@app.route("/manager")
def manager_dashboard():
    # try:
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
                order['items'] = order['items'].split(', ')
            
            return render_template("dashboard.html", user_role="manager", menu_items=menu_items, locations=locations, orders=orders, users=users)
    # except Exception as e:
    #     print(f"Error executing SQL query: {e}")
    #     return render_template("dashboard.html", user_role="manager", menu_items=[], locations=[], orders=[], users=[])

# Route for creating an order
@app.route("/create_order", methods=["POST"])
def create_order():
    if request.method == "POST":
        items = ', '.join(request.form.getlist("items"))

        try:
            with db.cursor() as cursor:
                # Insert new order into the database
                cursor.execute("INSERT INTO orders (customer, items, status) VALUES (%s, %s, %s)", ("customer1", items, "placed"))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error creating order: {e}")
            db.rollback()
    
    # Handle invalid form submission or errors
    return "Error creating order"

# Route for updating order status
@app.route("/update_order_status", methods=["POST"])
def update_order_status():
    data = request.get_json()
    order_id = data["orderId"]
    new_status = data["newStatus"]

    try:
        with db.cursor() as cursor:
            # Update the status of the order in the database
            cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
            db.commit()
            return "Success"
    except Exception as e:
        print(f"Error updating order status: {e}")
        db.rollback()
        return "Failed to update order status"

# Route for deleting an order
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

# Route for creating a user
@app.route("/create_user", methods=["POST"])
def create_user():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        try:
            with db.cursor() as cursor:
                # Insert new user into the database
                cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error creating user: {e}")
            db.rollback()
    
    # Handle invalid form submission or errors
    return "Error creating user"

# Route for updating a user's role
@app.route("/update_user_role", methods=["POST"])
def update_user_role():
    if request.method == "POST":
        username = request.form.get("username")
        role = request.form.get("role")

        try:
            with db.cursor() as cursor:
                # Update the role of the user in the database
                cursor.execute("UPDATE users SET role = %s WHERE username = %s", (role, username))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error updating user role: {e}")
            db.rollback()
            return "Error updating user role"

# Route for deleting a user
@app.route("/delete_user", methods=["POST"])
def delete_user():
    if request.method == "POST":
        username = request.form.get("username")

        try:
            with db.cursor() as cursor:
                # Delete the user from the database
                cursor.execute("DELETE FROM users WHERE username = %s", (username,))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error deleting user: {e}")
            db.rollback()
            return "Error deleting user"

# Route for creating a location
@app.route("/create_location", methods=["POST"])
def create_location():
    if request.method == "POST":
        name = request.form.get("name")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        try:
            with db.cursor() as cursor:
                # Insert new location into the database
                cursor.execute("INSERT INTO restaurant_locations (name, latitude, longitude) VALUES (%s, %s, %s)", (name, latitude, longitude))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error creating location: {e}")
            db.rollback()
    
    # Handle invalid form submission or errors
    return "Error creating location"

# Route for deleting a location
@app.route("/delete_location", methods=["POST"])
def delete_location():
    if request.method == "POST":
        name = request.form.get("name")

        try:
            with db.cursor() as cursor:
                # Delete the location from the database
                cursor.execute("DELETE FROM restaurant_locations WHERE name = %s", (name,))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error deleting location: {e}")
            db.rollback()
            return "Error deleting location"

# Route for creating a menu item
@app.route("/create_menu_item", methods=["POST"])
def create_menu_item():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")

        try:
            with db.cursor() as cursor:
                # Insert new menu item into the database
                cursor.execute("INSERT INTO menu_items (name, price) VALUES (%s, %s)", (name, price))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error creating menu item: {e}")
            db.rollback()
    
    # Handle invalid form submission or errors
    return "Error creating menu item"

# Route for updating a menu item
@app.route("/update_menu_item", methods=["POST"])
def update_menu_item():
    if request.method == "POST":
        item_id = request.form.get("id")
        name = request.form.get("name")
        price = request.form.get("price")

        try:
            with db.cursor() as cursor:
                # Update the menu item in the database
                cursor.execute("UPDATE menu_items SET name = %s, price = %s WHERE id = %s", (name, price, item_id))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error updating menu item: {e}")
            db.rollback()
            return "Error updating menu item"

# Route for deleting a menu item
@app.route("/delete_menu_item", methods=["POST"])
def delete_menu_item():
    if request.method == "POST":
        item_id = request.form.get("id")

        try:
            with db.cursor() as cursor:
                # Delete the menu item from the database
                cursor.execute("DELETE FROM menu_items WHERE id = %s", (item_id,))
                db.commit()
                return "Success"
        except Exception as e:
            print(f"Error deleting menu item: {e}")
            db.rollback()
            return "Error deleting menu item"

if __name__ == "__main__":
    app.run(debug=True)