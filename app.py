from flask import Flask, request, render_template, send_from_directory, jsonify
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
        return "File uploaded successfully!"
    return "No file uploaded."

@app.route('/files/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(UPLOAD_FOLDER)
    return {'files': files}

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'message': f'{filename} deleted successfully!'}), 200
    return jsonify({'error': 'File not found!'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
