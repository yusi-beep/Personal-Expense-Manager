from flask import Flask
from routes.home import home_bp
from routes.records import records_bp
from routes.categories import categories_bp

app = Flask(__name__)
app.secret_key = "supersecret"

# Blueprint regs
app.register_blueprint(home_bp)
app.register_blueprint(records_bp)
app.register_blueprint(categories_bp)

if __name__ == "__main__":
    app.run(debug=True)