from flask import Flask, render_template, request, redirect, url_for
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
    try:
        with db.cursor() as cursor:
            # Get menu items from the database
            cursor.execute("SELECT * FROM menu_items")
            menu_items = cursor.fetchall()

            # Get orders placed by the user
            cursor.execute("SELECT * FROM orders")
            cursor.execute("SELECT * FROM orders WHERE customer = %s", ("customer1",))  # Replace "customer1" with actual username
            orders = cursor.fetchall()

            return render_template("dashboard.html", user_role="customer", menu_items=menu_items, orders=orders)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return render_template("dashboard.html", user_role="customer", menu_items=[], orders=[])


# Route for staff dashboard
@app.route("/staff")
def staff_dashboard():
    try:
        with db.cursor() as cursor:
            # Get all orders
            cursor.execute("SELECT * FROM orders")
            orders = cursor.fetchall()

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

            return render_template("dashboard.html", user_role="manager", menu_items=menu_items, locations=locations, orders=orders, users=users)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return render_template("dashboard.html", user_role="manager", menu_items=[], locations=[], orders=[], users=[])

# Route for creating an order
@app.route("/create_order", methods=["POST"])
def create_order():
    if request.method == "POST":
        items = request.form.getlist("items")
        status = request.form["status"]
        
        try:
            with db.cursor() as cursor:
                # Insert new order into the database
                cursor.execute("INSERT INTO orders (items, status) VALUES (%s, %s)", (items, status))
                db.commit()
                return redirect(url_for("home"))
        except Exception as e:
            print(f"Error creating order: {e}")
            db.rollback()
    
    # Handle invalid form submission or errors
    return "Error creating order"


if __name__ == "__main__":
    app.run(debug=True)
