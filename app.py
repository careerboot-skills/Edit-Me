import os
from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
import fitz  # PyMuPDF engine

app = Flask(__name__)
CORS(app)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit.Me - Professional PDF Editor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/js/all.min.js"></script>
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --bg-dark: #0f172a;
            --card-bg: #1e293b;
            --accent: #06b6d4;
            --text: #f8fafc;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background-color: var(--bg-dark); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; }

        header {
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding: 0.8rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .brand-container { display: flex; align-items: center; gap: 12px; }
        .logo-svg { width: 34px; height: 34px; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5)); }
        .brand-title { font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, #818cf8, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .co-brand { font-size: 0.85rem; color: #94a3b8; font-weight: 500; }
        .co-brand span { color: var(--accent); font-weight: 700; }

        main { flex: 1; padding: 2rem; display: flex; flex-direction: column; align-items: center; }

        .upload-card {
            background: var(--card-bg);
            border: 2px dashed rgba(99, 102, 241, 0.4);
            border-radius: 20px;
            padding: 4rem 2rem;
            text-align: center;
            max-width: 550px;
            width: 100%;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-top: 2rem;
        }

        .upload-card:hover { border-color: var(--primary); transform: translateY(-3px); }
        .upload-icon { font-size: 3.5rem; color: var(--primary); margin-bottom: 1rem; }
        .btn-upload { background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; padding: 12px 28px; border-radius: 30px; border: none; font-weight: 600; margin-top: 1.5rem; cursor: pointer; }

        #editor-workspace { display: none; width: 100%; max-width: 1100px; }
        .toolbar {
            background: var(--card-bg);
            padding: 0.8rem 1.2rem;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            align-items: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            position: sticky;
            top: 65px;
            z-index: 90;
        }

        .pdf-container { display: flex; flex-direction: column; gap: 2rem; align-items: center; }
        .page-wrapper { position: relative; background: white; box-shadow: 0 10px 30px rgba(0,0,0,0.4); }

        .text-layer { position: absolute; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; }
        .text-layer span {
            position: absolute;
            color: transparent;
            cursor: text;
            white-space: pre;
            transform-origin: 0% 0%;
            border: 1px transparent dashed;
            border-radius: 2px;
            pointer-events: auto;
        }

        .text-layer span:hover {
            border-color: #6366f1;
            background: rgba(99, 102, 241, 0.15);
        }

        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(4px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 2rem;
            width: 90%;
            max-width: 450px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .modal h3 { margin-bottom: 1rem; color: var(--text); }
        .modal input { width: 100%; padding: 10px; margin-bottom: 1rem; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; }
        .modal-buttons { display: flex; gap: 10px; justify-content: flex-end; }
        .btn-cancel { background: #334155; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; }
        .btn-save { background: var(--primary); color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; }
    </style>
</head>
<body>

    <header>
        <div class="brand-container">
            <svg class="logo-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18.5 2.50001C18.8978 2.10219 19.4374 1.87868 20 1.87868C20.5626 1.87868 21.1022 2.10219 21.5 2.50001C21.8978 2.89784 22.1213 3.43739 22.1213 4.00001C22.1213 4.56263 21.8978 5.10219 21.5 5.50001L12 15L8 16L9 12L18.5 2.50001Z" stroke="#06b6d4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="brand-title">Edit.Me</span>
        </div>
        <div class="co-brand">Co-Powered by <span>CareerBoot</span></div>
    </header>

    <main>
        <div class="upload-card" id="upload-card" onclick="document.getElementById('file-input').click()">
            <i class="fa-solid fa-file-pdf upload-icon"></i>
            <h2>Upload PDF to Edit</h2>
            <p style="color: #94a3b8; margin-top: 8px;">Click any text element on your PDF to update it precisely</p>
            <button class="btn-upload">Select PDF Document</button>
            <input type="file" id="file-input" accept="application/pdf" style="display: none;" onchange="handleFileSelect(event)">
        </div>

        <div id="editor-workspace">
            <div class="toolbar">
                <span style="font-weight: 600; color: #94a3b8;">Click on any text on the page to modify</span>
                <button class="btn-save" onclick="applyBackendEdit()">Export & Download PDF</button>
            </div>
            <div id="pdf-container" class="pdf-container"></div>
        </div>
    </main>

    <div class="modal-overlay" id="edit-modal">
        <div class="modal">
            <h3>Edit Text Element</h3>
            <label style="font-size: 0.85rem; color: #94a3b8;">Target Original Text:</label>
            <input type="text" id="modal-old-text" readonly style="opacity: 0.7;">
            
            <label style="font-size: 0.85rem; color: #94a3b8;">Replacement Text:</label>
            <input type="text" id="modal-new-text">
            
            <div class="modal-buttons">
                <button class="btn-cancel" onclick="closeModal()">Cancel</button>
                <button class="btn-save" onclick="saveElementEdit()">Update Element</button>
            </div>
        </div>
    </div>

    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
        let currentFile = null;
        let activeTargetElement = null;
        let editsQueue = [];

        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (!file) return;

            currentFile = file;
            document.getElementById('upload-card').style.display = 'none';
            document.getElementById('editor-workspace').style.display = 'block';

            const reader = new FileReader();
            reader.onload = function() {
                renderPDF(new Uint8Array(this.result));
            };
            reader.readAsArrayBuffer(file);
        }

        async function renderPDF(data) {
            const loadingTask = pdfjsLib.getDocument({ data });
            const pdfDoc = await loadingTask.promise;
            const container = document.getElementById('pdf-container');
            container.innerHTML = '';

            for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
                const page = await pdfDoc.getPage(pageNum);
                const scale = 1.5;
                const viewport = page.getViewport({ scale });

                const wrapper = document.createElement('div');
                wrapper.className = 'page-wrapper';
                wrapper.style.width = `${viewport.width}px`;
                wrapper.style.height = `${viewport.height}px`;

                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                await page.render({ canvasContext: context, viewport: viewport }).promise;

                const textLayerDiv = document.createElement('div');
                textLayerDiv.className = 'text-layer';

                const textContent = await page.getTextContent();
                textContent.items.forEach((item) => {
                    if (!item.str.trim()) return;

                    const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
                    const fontHeight = Math.sqrt(tx[2] * tx[2] + tx[3] * tx[3]);

                    const span = document.createElement('span');
                    span.textContent = item.str;
                    span.style.left = `${tx[4]}px`;
                    span.style.top = `${tx[5] - fontHeight}px`;
                    span.style.fontSize = `${fontHeight}px`;

                    // Store precise coordinates for PyMuPDF Engine (Normalized to original scale)
                    span.dataset.pageNum = pageNum - 1;
                    span.dataset.oldText = item.str;
                    span.dataset.pdfX = tx[4] / scale;
                    span.dataset.pdfY = (tx[5] - fontHeight) / scale;
                    span.dataset.fontSize = fontHeight / scale;
                    span.dataset.width = (item.width * scale) / scale;
                    span.dataset.height = fontHeight / scale;

                    span.onclick = () => {
                        activeTargetElement = span;
                        document.getElementById('modal-old-text').value = span.textContent;
                        document.getElementById('modal-new-text').value = span.textContent;
                        document.getElementById('edit-modal').style.display = 'flex';
                    };

                    textLayerDiv.appendChild(span);
                });

                wrapper.appendChild(canvas);
                wrapper.appendChild(textLayerDiv);
                container.appendChild(wrapper);
            }
        }

        function closeModal() {
            document.getElementById('edit-modal').style.display = 'none';
        }

        function saveElementEdit() {
            if (!activeTargetElement) return;

            const newText = document.getElementById('modal-new-text').value;
            const oldText = activeTargetElement.dataset.oldText;

            // Update UI preview visually
            activeTargetElement.textContent = newText;
            activeTargetElement.style.color = '#000';
            activeTargetElement.style.background = '#ffffff';

            editsQueue.push({
                page_num: parseInt(activeTargetElement.dataset.pageNum),
                old_text: oldText,
                new_text: newText,
                x: parseFloat(activeTargetElement.dataset.pdfX),
                y: parseFloat(activeTargetElement.dataset.pdfY),
                width: parseFloat(activeTargetElement.dataset.width),
                font_size: parseFloat(activeTargetElement.dataset.fontSize)
            });

            closeModal();
        }

        async function applyBackendEdit() {
            if (editsQueue.length === 0) {
                alert("No changes made to export!");
                return;
            }

            const formData = new FormData();
            formData.append('pdf', currentFile);
            formData.append('edits', JSON.stringify(editsQueue));

            const response = await fetch('/edit-pdf', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const downloadUrl = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = 'edited_output.pdf';
                a.click();
            } else {
                alert('Error updating PDF text');
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/edit-pdf', methods=['POST'])
def edit_pdf():
    try:
        import json

        if 'pdf' not in request.files:
            return jsonify({"error": "PDF file missing"}), 400

        file = request.files['pdf']
        edits_json = request.form.get('edits', '[]')
        edits = json.loads(edits_json)

        doc = fitz.open(stream=file.read(), filetype="pdf")

        for edit in edits:
            page_num = edit['page_num']
            old_text = edit['old_text']
            new_text = edit['new_text']
            font_size = edit['font_size']

            if page_num < len(doc):
                page = doc[page_num]
                rects = page.search_for(old_text)

                if rects:
                    # Select precise bounding box targeting target position
                    target_rect = rects[0]
                    page.add_redact_annot(target_rect, fill=(1, 1, 1))
                    page.apply_redactions()

                    if new_text:
                        # Baseline adjustment for vector text placement
                        baseline_point = fitz.Point(target_rect.x0, target_rect.y1 - 1.5)
                        page.insert_text(
                            baseline_point, 
                            new_text, 
                            fontsize=font_size if font_size > 0 else 10, 
                            color=(0, 0, 0)
                        )

        output_path = "edited_output.pdf"
        doc.save(output_path)
        return send_file(output_path, as_attachment=True, download_name="edited.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
