import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF engine

app = Flask(__name__)
CORS(app)

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
                # 1. Vector level Redaction (Text permanent erase karna)
                page.add_redact_annot(inst, fill=(1, 1, 1))
                page.apply_redactions()

                # 2. Exact same location par naya text print karna
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
