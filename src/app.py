from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    menu_items = [
        {"name": "Pasta Carbonara", "price": "$15"},
        {"name": "Tiramisu", "price": "$8"},
        # Add more menu items here
    ]
    special_of_the_day = "Try our Chef's Special Seafood Risotto!"

    return render_template("index.html", menu_items=menu_items, special_of_the_day=special_of_the_day)

if __name__ == "__main__":
    app.run(debug=True)
