from flask import Flask, render_template, request, redirect, url_for
import requests
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)

# Filler data for menu items (to be replaced with database)
menu_items = [
    {
        "name": "Pasta Carbonara",
        "price": "$15",
        "description": "Delicious pasta with creamy sauce.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Tiramisu",
        "price": "$8",
        "description": "Classic Italian dessert made with coffee and mascarpone.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Margherita Pizza",
        "price": "$12",
        "description": "Traditional Italian pizza topped with tomatoes, mozzarella, and basil.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Caesar Salad",
        "price": "$10",
        "description": "Fresh romaine lettuce with Caesar dressing, croutons, and Parmesan cheese.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Grilled Salmon",
        "price": "$18",
        "description": "Fresh grilled salmon served with seasonal vegetables.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Chicken Alfredo",
        "price": "$14",
        "description": "Creamy Alfredo sauce with grilled chicken served over pasta.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Cheeseburger",
        "price": "$11",
        "description": "Classic cheeseburger with lettuce, tomato, onion, and choice of cheese.",
        "image_url": "/static/food.png",
    },
    {
        "name": "Sushi Platter",
        "price": "$20",
        "description": "Assortment of fresh sushi rolls and sashimi.",
        "image_url": "/static/food.png",
    },
]

# Filler data for restaurant locations (to be replaced with database)
restaurant_locations = [
    {"name": "Restaurant A", "latitude": 40.7128, "longitude": -74.0060},
    {"name": "Restaurant B", "latitude": 34.0522, "longitude": -118.2437},
    {"name": "Restaurant C", "latitude": 51.5074, "longitude": -0.1278},
]

# Filler data for users
users = [
    {"username": "customer1", "password": "password1", "role": "customer"},
    {"username": "staff1", "password": "password1", "role": "staff"},
    {"username": "manager1", "password": "password1", "role": "manager"},
]

# Filler data for orders (for demonstration, just a list of dictionaries)
orders = [
    {
        "order_id": 1,
        "customer": "customer1",
        "items": ["Pasta Carbonara", "Margherita Pizza"],
        "status": "placed",
    },
    {
        "order_id": 2,
        "customer": "customer2",
        "items": ["Tiramisu", "Caesar Salad"],
        "status": "delivered",
    },
    {
        "order_id": 3,
        "customer": "customer3",
        "items": ["Grilled Salmon", "Chicken Alfredo"],
        "status": "in_progress",
    },
]


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
    user_ip = request.remote_addr
    user_city, user_country, user_lat, user_lon = get_user_location(user_ip)

    if user_lat is not None and user_lon is not None:
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

        print(top_3_closest)
        return render_template(
            "index.html",
            menu_items=menu_items,
            user_location=f"{user_city}, {user_country}",
            nearest_location_name=nearest_location_name,
            nearest_location_distance=nearest_location_distance,
            top_3_closest=top_3_closest,
            restaurant_locations=restaurant_locations,
        )

    return render_template(
        "index.html",
        menu_items=menu_items,
        user_location="Unknown",
        nearest_location_name=None,
        nearest_location_distance=None,
        top_3_closest=None,
        restaurant_locations=restaurant_locations,
    )


# Route for login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if user exists and credentials are correct
        for user in users:
            if user["username"] == username and user["password"] == password:
                role = user["role"]
                # Redirect to appropriate page based on role
                if role == "customer":
                    return redirect(url_for("customer_dashboard"))
                elif role == "staff":
                    return redirect(url_for("staff_dashboard"))
                elif role == "manager":
                    return redirect(url_for("manager_dashboard"))

        # If credentials are incorrect or user doesn't exist, reload login page
        return render_template(
            "login.html", message="Invalid credentials. Please try again."
        )

    # For GET request, render the login page
    return render_template("login.html")


# Route for customer dashboard
@app.route("/customer")
def customer_dashboard():
    # Here you can pass any necessary data for the customer dashboard
    return render_template("dashboard.html", role="customer")


# Route for staff dashboard
@app.route("/staff")
def staff_dashboard():
    # Here you can pass any necessary data for the staff dashboard
    return render_template("dashboard.html", role="staff")


# Route for manager dashboard
@app.route("/manager")
def manager_dashboard():
    # Here you can pass any necessary data for the manager dashboard
    return render_template("dashboard.html", role="manager")


if __name__ == "__main__":
    app.run(debug=True)
