import os
import zipfile
import io
import pandas as pd
import openai
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Set the OpenAI API key (make sure to replace this with your actual API key)

openai.api_key = os.getenv("OPENAI_API_KEY")
# Define file upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'zip', 'csv'}

# Set up the upload folder
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract ZIP and read the CSV file
def extract_zip(file):
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(UPLOAD_FOLDER)
        # Assuming only one file in the zip archive and it's a CSV
        extracted_files = zip_ref.namelist()
        csv_file = [f for f in extracted_files if f.endswith('.csv')][0]
        return os.path.join(UPLOAD_FOLDER, csv_file)

# Function to process the CSV file and get the answer
def process_csv(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    # Assuming there is a column named 'answer' to extract data from
    if 'answer' in df.columns:
        return df['answer'].iloc[0]
    else:
        return "No 'answer' column found in the CSV file."

# Function to get answer from OpenAI API
def get_answer_from_openai(question):
    response = openai.Completion.create(
        engine="text-davinci-003",  # or GPT-4 if available
        prompt=question,
        max_tokens=150
    )
    return response.choices[0].text.strip()

@app.route('/api/', methods=['POST'])
def answer_question():
    if 'question' not in request.form:
        return jsonify({"error": "Question is required"}), 400
    
    question = request.form['question']
    file = request.files.get('file')

    # If a file is uploaded, process it
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # If it's a ZIP file, extract it and process the CSV
        if filename.endswith('.zip'):
            extracted_file = extract_zip(file_path)
            answer = process_csv(extracted_file)
        else:
            # Handle other file types (if needed)
            answer = "Only ZIP files with CSV inside are supported."
    else:
        # If no file is provided, ask GPT-3 to answer the question directly
        answer = get_answer_from_openai(question)

    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True)
