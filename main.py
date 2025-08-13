from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS
from config import get_settings
from app.storage.database import create_db, engine
from app.storage.models import Admin, Category
from app.crud.admin import get_admin
from app.core.utils import get_password_hash
from sqlmodel import Session, select

settings = get_settings()


app = Flask(__name__)

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
app.register_blueprint(auth.auth_bp, url_prefix="/auth", strict_slashes=False)
app.register_blueprint(admin.admin_bp, url_prefix="/admin", strict_slashes=False)
app.register_blueprint(video.video_bp, url_prefix="/tvs", strict_slashes=False)
app.register_blueprint(update.update_bp, url_prefix="/updates", strict_slashes=False)
app.register_blueprint(event.event_bp, url_prefix="/events", strict_slashes=False)
app.register_blueprint(like.like_bp, url_prefix="/likes", strict_slashes=False)
app.register_blueprint(category.category_bp, url_prefix="/categories", strict_slashes=False)


# Startup logic
create_db()

# Create default admin
with Session(engine) as db:
    admin_user = get_admin(db, settings.admin_user)
    if not admin_user:
        admin_user = Admin(
            username=settings.admin_user,
            password=get_password_hash(settings.admin_pwd)
        )
        db.add(admin_user)

    # Create categories
    for name in settings.video_categories:
        if not db.exec(select(Category).where(Category.name == name)).first():
            db.add(Category(name=name))

    db.commit()


# Status route
@app.route("/")
def app_status():
    return jsonify({"status": "active"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
