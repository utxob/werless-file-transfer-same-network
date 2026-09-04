from flask import Flask, request, render_template, send_from_directory, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import mimetypes

app = Flask(__name__)
CORS(app)
# Remove the file size limit by setting it to None or a very large value
# Using None disables the limit entirely
app.config['MAX_CONTENT_LENGTH'] = None  # No size limit
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'zip', 'mp4', 'mp3', 'webm', 'avi', 'mov', 'wmv', 'flv',
    'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp',
    'xml', 'json', 'csv', 'log', 'py', 'js', 'html', 'css',
    'svg', 'ico', 'webp', 'bmp', 'tiff', 'psd', 'ai', 'eps',
    'rar', '7z', 'tar', 'gz', 'bz2', 'iso', 'dmg', 'exe', 'msi',
    'apk', 'ipa', 'deb', 'rpm', 'sh', 'bat', 'cmd'
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_unique_filename(filename):
    name, ext = os.path.splitext(filename)
    unique_id = str(uuid.uuid4())[:8]
    return f"{name}_{unique_id}{ext}"

def get_file_info(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return None
    
    stats = os.stat(file_path)
    mime_type, _ = mimetypes.guess_type(filename)
    
    return {
        'name': filename,
        'size': stats.st_size,
        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
        'mime_type': mime_type or 'application/octet-stream'
    }

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        files = request.files.getlist('file')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No selected files'}), 400
        
        uploaded_files = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                errors.append(f"{file.filename}: File type not allowed")
                continue
            
            # Get the file size before saving
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            filename = secure_filename(file.filename)
            unique_filename = get_unique_filename(filename)
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # Save in chunks for large files to prevent memory issues
            with open(file_path, 'wb') as f:
                while True:
                    chunk = file.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    f.write(chunk)
            
            uploaded_files.append({
                'original_name': filename,
                'stored_name': unique_filename,
                'size': file_size
            })
        
        if uploaded_files:
            return jsonify({
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                'files': uploaded_files,
                'errors': errors if errors else None
            }), 200
        else:
            return jsonify({
                'error': 'No files were uploaded successfully',
                'details': errors
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files/<filename>')
def download_file(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/files', methods=['GET'])
def list_files():
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            file_info = get_file_info(filename)
            if file_info:
                files.append(file_info)
        
        # Sort by modified date (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': files}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        safe_filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found!'}), 404
            
        os.remove(file_path)
        return jsonify({'message': f'{filename} deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview/<filename>')
def preview_file(filename):
    try:
        safe_filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and mime_type.startswith('image/'):
            return send_from_directory(UPLOAD_FOLDER, safe_filename)
        else:
            return jsonify({'error': 'Not an image file'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
