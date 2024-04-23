from flask import Flask, render_template

app = Flask(__name__)

# Define menu items dynamically
menu_items = [
    {"name": "Pasta Carbonara", "price": "$15", "description": "Delicious pasta with creamy sauce.", "image_url": "/static/food.png"},
    {"name": "Tiramisu", "price": "$8", "description": "Classic Italian dessert made with coffee and mascarpone.", "image_url": "/static/food.png"},
    {"name": "Margherita Pizza", "price": "$12", "description": "Traditional Italian pizza topped with tomatoes, mozzarella, and basil.", "image_url": "/static/food.png"},
    {"name": "Caesar Salad", "price": "$10", "description": "Fresh romaine lettuce with Caesar dressing, croutons, and Parmesan cheese.", "image_url": "/static/food.png"},
    {"name": "Grilled Salmon", "price": "$18", "description": "Fresh grilled salmon served with seasonal vegetables.", "image_url": "/static/food.png"},
    {"name": "Chicken Alfredo", "price": "$14", "description": "Creamy Alfredo sauce with grilled chicken served over pasta.", "image_url": "/static/food.png"},
    {"name": "Cheeseburger", "price": "$11", "description": "Classic cheeseburger with lettuce, tomato, onion, and choice of cheese.", "image_url": "/static/food.png"},
    {"name": "Sushi Platter", "price": "$20", "description": "Assortment of fresh sushi rolls and sashimi.", "image_url": "/static/food.png"},
    # Add more menu items here
]

@app.route("/")
def home():
    special_of_the_day = "Try our Chef's Special Seafood Risotto!"
    return render_template("index.html", menu_items=menu_items, special_of_the_day=special_of_the_day)

if __name__ == "__main__":
    app.run(debug=True)
