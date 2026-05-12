from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from pathlib import Path
import os
import shutil
import json
import logging
import PyPDF2
import hashlib
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import magic
from datetime import datetime
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ai-file-organizer-secret-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Google OAuth Configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=True) # Nullable for Google auth
    auth_provider = db.Column(db.String(50), default='local') # To track login method

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database
with app.app_context():
    db.create_all()

logging.basicConfig(filename='file_organizer.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

BASE_BROWSE_PATH = Path.home().resolve()

CATEGORIES = {
    "Documents": {
        "keywords": ["report", "invoice", "letter", "contract", "business"],
        "extensions": ["doc", "docx", "pdf", "txt"],
        "mime_types": ["application/pdf", "text/plain", "application/msword"]
    },
    "Images": {
        "keywords": ["photo", "image", "picture", "graphic"],
        "extensions": ["jpg", "png", "jpeg", "gif", "webp"],
        "mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp"]
    },
    "Media": {
        "keywords": ["video", "audio", "movie", "music", "song"],
        "extensions": ["mp4", "mp3", "wav", "avi", "mkv"],
        "mime_types": ["video/mp4", "audio/mpeg", "audio/wav", "video/x-msvideo"]
    },
    "Code": {
        "keywords": ["script", "code", "program", "source"],
        "extensions": ["py", "js", "html", "cpp", "java", "ts", "jsx"],
        "mime_types": ["text/x-python", "application/javascript", "text/html", "text/x-c++"]
    },
    "Archives": {
        "keywords": ["archive", "compressed", "backup"],
        "extensions": ["zip", "rar", "7z", "tar", "gz"],
        "mime_types": ["application/zip", "application/x-rar", "application/x-7z-compressed"]
    }
}

RESTORE_LOG = "restore_log.json"
mime = magic.Magic(mime=True)

# Store organization state
org_state = {
    'organizing': False,
    'logs': [],
    'progress': 0,
    'total': 0
}

def get_file_hash(file_path):
    try:
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Error hashing {file_path}: {e}")
        return None

def extract_text_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.lower()
    except Exception as e:
        logging.error(f"Error reading PDF {file_path}: {e}")
        return ""

def analyze_content(text):
    tokens = word_tokenize(text[:2000])
    tagged = pos_tag(tokens)
    nouns = [word for word, pos in tagged if pos.startswith('NN')]
    return nouns

def categorize_file(file_path):
    file_name = file_path.name.lower()
    file_ext = file_path.suffix[1:].lower()
    try:
        mime_type = mime.from_file(str(file_path))
    except:
        mime_type = ""

    for category, props in CATEGORIES.items():
        if mime_type in props["mime_types"]:
            return category

    for category, props in CATEGORIES.items():
        if file_ext in props["extensions"]:
            return category

    if mime_type in ["application/pdf", "text/plain"]:
        text = extract_text_from_pdf(file_path) if file_ext == "pdf" else ""
        if not text:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read().lower()
            except:
                return "Uncategorized"
        
        nouns = analyze_content(text)
        for category, props in CATEGORIES.items():
            if any(keyword in nouns for keyword in props["keywords"]):
                return category

    return "Uncategorized"

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"
    org_state['logs'].append(log_entry)
    logging.info(msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if not user or user.auth_provider != 'local' or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        return redirect(url_for('index'))

    return render_template('auth.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if password != confirm_password:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists', 'error')
        return redirect(url_for('login'))

    new_user = User(email=email, password=generate_password_hash(password, method='pbkdf2:sha256'))
    db.session.add(new_user)
    db.session.commit()

    flash('Account created successfully! Please login.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        token = serializer.dumps(email, salt='password-reset-salt')
        reset_url = url_for('reset_password', token=token, _external=True)
        
        try:
            msg = Message("Password Reset Request", 
                          sender=app.config['MAIL_USERNAME'], 
                          recipients=[email])
            msg.body = f"Please click the following link to reset your password: {reset_url}\n\nIf you did not make this request, simply ignore this email."
            mail.send(msg)
            flash('A password reset link has been sent to your email.', 'info')
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            flash('Failed to send email. Please check your SMTP configuration in .env.', 'error')
    else:
        flash('If that email exists in our system, a password reset link has been sent.', 'info')
    return redirect(url_for('login'))

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600) # 1 hour expiry
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('reset_password', token=token))

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password, method='pbkdf2:sha256')
            db.session.commit()
            flash('Your password has been updated! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def authorize_google():
    try:
        token = google.authorize_access_token()
        resp = google.get('https://openidconnect.googleapis.com/v1/userinfo')
        user_info = resp.json()
        email = user_info['email']
    except Exception as e:
        logging.error(f"Google Auth failed: {e}")
        flash('Failed to authenticate with Google. Please make sure your Client Secret is in .env.', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()

    if not user:
        # Create a new user for this Google account
        user = User(email=email, auth_provider='google')
        db.session.add(user)
        db.session.commit()
    elif user.auth_provider == 'local':
        # If they already signed up manually, maybe link the accounts
        user.auth_provider = 'google'
        db.session.commit()

    login_user(user)
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', categories=list(CATEGORIES.keys()), user=current_user)

@app.route('/api/select-directory', methods=['POST'])
@login_required
def select_directory():
    data = request.json
    directory = data.get('path')
    
    try:
        path = Path(directory)
        if not path.is_absolute():
            path = (BASE_BROWSE_PATH / path).resolve()
        if BASE_BROWSE_PATH not in path.parents and path != BASE_BROWSE_PATH:
            return jsonify({'success': False, 'error': 'Directory selection must stay within the home directory.'})
        if not path.exists():
            return jsonify({
                'success': False,
                'error': (
                    f'Directory does not exist: {directory}. '\
                    'This server can only access folders inside its own filesystem '
                    f'({BASE_BROWSE_PATH}). If you want to organize a local machine folder, '
                    'run the app locally on that machine.'
                )
            })
        
        if not path.is_dir():
            return jsonify({'success': False, 'error': f'Path is not a directory: {directory}'})
        
        files = sorted([f for f in path.iterdir() if f.is_file()], key=lambda f: f.name.lower())
        session['selected_dir'] = str(path)
        
        return jsonify({
            'success': True,
            'path': str(path),
            'file_count': len(files),
            'files': [{'name': f.name, 'size': f.stat().st_size, 'type': f.suffix} for f in files]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/browser', methods=['POST'])
@login_required
def browser():
    data = request.json or {}
    rel_path = data.get('path', '')
    try:
        target = (BASE_BROWSE_PATH / rel_path).resolve() if rel_path else BASE_BROWSE_PATH
        if BASE_BROWSE_PATH not in target.parents and target != BASE_BROWSE_PATH:
            return jsonify({'success': False, 'error': 'Path outside home directory not allowed.'})
        if not target.exists() or not target.is_dir():
            return jsonify({'success': False, 'error': 'Directory not found.'})

        entries = []
        for entry in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.is_dir():
                entries.append({
                    'name': entry.name,
                    'path': str(entry.relative_to(BASE_BROWSE_PATH)),
                    'is_dir': True
                })
        return jsonify({
            'success': True,
            'path': str(target),
            'relative_path': str(target.relative_to(BASE_BROWSE_PATH)),
            'base_path': str(BASE_BROWSE_PATH),
            'entries': entries
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/organize', methods=['POST'])
@login_required
def organize():
    if org_state['organizing']:
        return jsonify({'success': False, 'error': 'Organization already in progress'})
    
    data = request.json
    source_dir = data.get('path')
    skip_duplicates = data.get('skip_duplicates', False)
    selected_files = data.get('selected_files', [])
    
    if not source_dir or not os.path.exists(source_dir):
        return jsonify({'success': False, 'error': 'Invalid directory'})
    
    def do_organize():
        org_state['organizing'] = True
        org_state['logs'] = []
        
        try:
            source_path = Path(source_dir)
            if selected_files:
                files = []
                for filename in selected_files:
                    candidate = source_path / filename
                    if candidate.exists() and candidate.is_file() and candidate.parent == source_path:
                        files.append(candidate)
                add_log(f"📁 Selected {len(files)} file(s) to organize")
            else:
                files = [f for f in source_path.iterdir() if f.is_file()]

            org_state['total'] = len(files)
            org_state['progress'] = 0
            
            add_log(f"🚀 Starting organization of {org_state['total']} file(s)...")
            
            move_log = {}
            seen_hashes = {}
            
            for i, file_path in enumerate(files):
                file_hash = get_file_hash(file_path) if skip_duplicates else None
                if skip_duplicates and file_hash and file_hash in seen_hashes:
                    add_log(f"⏭️  Skipping duplicate: {file_path.name}")
                    org_state['progress'] = i + 1
                    continue
                
                category = categorize_file(file_path)
                target_dir = source_path / category
                target_dir.mkdir(exist_ok=True)
                target_path = target_dir / file_path.name
                
                try:
                    shutil.move(str(file_path), str(target_path))
                    move_log[str(target_path)] = str(file_path)
                    if skip_duplicates and file_hash:
                        seen_hashes[file_hash] = target_path
                    add_log(f"✅ {file_path.name} → {category}/")
                except Exception as e:
                    add_log(f"❌ Error moving {file_path.name}: {e}")
                
                org_state['progress'] = i + 1
            
            with open(RESTORE_LOG, 'w') as f:
                json.dump(move_log, f)
            
            add_log(f"✨ Organization complete! {org_state['progress']} files organized.")
            org_state['organizing'] = False
            
        except Exception as e:
            add_log(f"💥 Fatal error: {e}")
            org_state['organizing'] = False
    
    thread = threading.Thread(target=do_organize)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Organization started'})

@app.route('/api/restore', methods=['POST'])
@login_required
def restore():
    if org_state['organizing']:
        return jsonify({'success': False, 'error': 'Organization in progress'})
    
    data = request.json
    cleanup_empty = data.get('cleanup_empty', True)
    
    if not os.path.exists(RESTORE_LOG):
        return jsonify({'success': False, 'error': 'No restore log found'})
    
    def do_restore():
        org_state['organizing'] = True
        org_state['logs'] = []
        
        try:
            with open(RESTORE_LOG, 'r') as f:
                move_log = json.load(f)
            
            org_state['total'] = len(move_log)
            org_state['progress'] = 0
            
            add_log(f"🔄 Restoring {org_state['total']} files to original locations...")
            
            for i, (target_path, original_path) in enumerate(move_log.items()):
                if os.path.exists(target_path):
                    try:
                        os.makedirs(os.path.dirname(original_path), exist_ok=True)
                        shutil.move(target_path, original_path)
                        add_log(f"✅ Restored {Path(target_path).name}")
                    except Exception as e:
                        add_log(f"❌ Error restoring {Path(target_path).name}: {e}")
                else:
                    add_log(f"⏭️  {Path(target_path).name} not found")
                
                org_state['progress'] = i + 1
            
            if cleanup_empty:
                source_path = Path(list(move_log.values())[0]).parent if move_log else None
                if source_path:
                    for subdir in source_path.iterdir():
                        if subdir.is_dir():
                            try:
                                if not any(subdir.iterdir()):
                                    os.rmdir(subdir)
                                    add_log(f"🗑️  Removed empty folder: {subdir.name}")
                            except:
                                pass
            
            os.remove(RESTORE_LOG)
            add_log("✨ Restore complete!")
            org_state['organizing'] = False
            
        except Exception as e:
            add_log(f"💥 Error: {e}")
            org_state['organizing'] = False
    
    thread = threading.Thread(target=do_restore)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Restore started'})

@app.route('/api/logs')
@login_required
def get_logs():
    return jsonify({
        'logs': org_state['logs'],
        'progress': org_state['progress'],
        'total': org_state['total'],
        'organizing': org_state['organizing'],
        'can_restore': os.path.exists(RESTORE_LOG)
    })

@app.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    return jsonify(CATEGORIES)

@app.route('/api/categories', methods=['POST'])
@login_required
def update_categories():
    data = request.json
    global CATEGORIES
    CATEGORIES = data
    return jsonify({'success': True})

if __name__ == '__main__':
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        nltk.download('averaged_perceptron_tagger', quiet=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
