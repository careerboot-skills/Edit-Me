import os
from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
import fitz  # PyMuPDF engine

app = Flask(__name__)
CORS(app)

# HTML interface for testing directly in the browser
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Text Replacer</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px; }
        h2 { text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], input[type="file"] { width: 100%; padding: 8px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <h2>PDF Text Replacer</h2>
    <form action="/edit-pdf" method="post" enctype="multipart/form-data">
        <div class="form-group">
            <label for="pdf">Select PDF File:</label>
            <input type="file" id="pdf" name="pdf" accept=".pdf" required>
        </div>
        <div class="form-group">
            <label for="old_text">Text to Replace:</label>
            <input type="text" id="old_text" name="old_text" placeholder="Enter target text" required>
        </div>
        <div class="form-group">
            <label for="new_text">New Text:</label>
            <input type="text" id="new_text" name="new_text" placeholder="Enter replacement text">
        </div>
        <button type="submit">Process & Download PDF</button>
    </form>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/edit-pdf', methods=['POST'])
def edit_pdf():
    try:
        if 'pdf' not in request.files:
            return jsonify({"error": "PDF file missing"}), 400
            
        file = request.files['pdf']
        old_text = request.form.get('old_text', '')
        new_text = request.form.get('new_text', '')

        if not old_text:
            return jsonify({"error": "Old text is required"}), 400

        doc = fitz.open(stream=file.read(), filetype="pdf")

        for page in doc:
            text_instances = page.search_for(old_text)
            for inst in text_instances:
                # 1. Vector level Redaction
                page.add_redact_annot(inst, fill=(1, 1, 1))
                page.apply_redactions()

                # 2. Insert new text at exact same coordinates
                if new_text:
                    page.insert_text(inst.tl, new_text, fontsize=9, color=(0, 0, 0))

        output_path = "edited_output.pdf"
        doc.save(output_path)
        return send_file(output_path, as_attachment=True, download_name="edited.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
