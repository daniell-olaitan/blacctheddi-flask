from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS
from config import get_settings
from app.storage.database import create_db
from app.storage.models import Admin, Category
from app.crud.admin import get_admin
from app.core.utils import get_password_hash
from app.core.dependencies import safe_db_operation
from sqlmodel import select, Session

settings = get_settings()


app = Flask(__name__)
app.url_map.strict_slashes = False

# Load config
app.config["SECRET_KEY"] = settings.secret_key

# Enable CORS
CORS(app, origins=[
    'https://tvandlivepost.vercel.app',
    'https://blacctheddipost.madeinblacc.net',
    'http://localhost:3000',
], supports_credentials=True)

# Register Blueprints (auth, admin, etc.)
from app.blueprints import auth, admin, video, update, event, like, category

app.register_blueprint(auth.auth_bp,  strict_slashes=False)
app.register_blueprint(admin.admin_bp, strict_slashes=False)
app.register_blueprint(video.video_bp, strict_slashes=False)
app.register_blueprint(update.update_bp, strict_slashes=False)
app.register_blueprint(event.event_bp, strict_slashes=False)
app.register_blueprint(like.like_bp, strict_slashes=False)
app.register_blueprint(category.category_bp, strict_slashes=False)


# Startup logic
create_db()


def create_defaults(db: Session):
    if not get_admin(db, settings.admin_user):
        admin_user = Admin(
            username=settings.admin_user,
            password=get_password_hash(settings.admin_pwd)
        )
        db.add(admin_user)

    # Create categories
    for name in settings.video_categories:
        if not db.exec(select(Category).where(Category.name == name)).first():
            db.add(Category(name=name))


safe_db_operation(create_defaults)

# Status route
@app.route("/")
def app_status():
    return jsonify({"status": "active"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
