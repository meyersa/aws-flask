import pymysql.cursors

# Database connection details
db_host = "localhost"
db_user = "root"
db_password = "password"
db_name = "db"

# Data to insert into tables
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

restaurant_locations = [
    {"name": "Restaurant A", "latitude": 40.7128, "longitude": -74.0060},
    {"name": "Restaurant B", "latitude": 34.0522, "longitude": -118.2437},
    {"name": "Restaurant C", "latitude": 51.5074, "longitude": -0.1278},
]

users = [
    {"username": "customer1", "password": "password1", "role": "customer"},
    {"username": "staff1", "password": "password1", "role": "staff"},
    {"username": "manager1", "password": "password1", "role": "manager"},
]

orders = [
    {"customer": "customer1", "items": ["Pasta Carbonara", "Margherita Pizza"], "status": "placed"},
    {"customer": "customer2", "items": ["Tiramisu", "Caesar Salad"], "status": "delivered"},
    {"customer": "customer3", "items": ["Grilled Salmon", "Chicken Alfredo"], "status": "in_progress"},
]

# Connect to the database
connection = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name, cursorclass=pymysql.cursors.DictCursor)

# Function to execute SQL queries
# Execute a SQL query with optional data values
# Function to execute SQL queries
def execute_query(sql, data=None):
    try:
        with connection.cursor() as cursor:
            if data:
                cursor.execute(sql, data)
            else:
                cursor.execute(sql)
        connection.commit()
    except Exception as e:
        print(f"Error executing SQL query: {e}", data)
        connection.rollback()



# Create tables
create_menu_items_table = """
CREATE TABLE IF NOT EXISTS menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price VARCHAR(10) NOT NULL,
    description TEXT,
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
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer VARCHAR(255) NOT NULL,
    items TEXT NOT NULL,
    status VARCHAR(50) NOT NULL
);
"""

# Insert data into tables
def insert_data(table_name, data):
    for item in data:
        columns = ', '.join(item.keys())
        values_template = ', '.join(['%s'] * len(item))
        
        # Convert list of items to a single string
        if 'items' in item:
            item['items'] = ', '.join(item['items'])

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values_template})"
        execute_query(sql, list(item.values()))


# Execute table creation queries
execute_query(create_menu_items_table)
execute_query(create_restaurant_locations_table)
execute_query(create_users_table)
execute_query(create_orders_table)

# Insert data into tables
insert_data("menu_items", menu_items)
insert_data("restaurant_locations", restaurant_locations)
insert_data("users", users)
insert_data("orders", orders)

# Close database connection
connection.close()
