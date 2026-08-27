import os
from flask import Flask, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit.Me - PDF Editor</title>
    <!-- PDF.js & pdf-lib Libraries -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
    <script src="https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>
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
        body { background-color: var(--bg-dark); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; overflow-x: hidden; }

        /* Header Branding */
        header {
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .brand-container { display: flex; align-items: center; gap: 12px; }
        .logo-svg { width: 38px; height: 38px; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5)); }
        .brand-title { font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #818cf8, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .co-brand { font-size: 0.85rem; color: #94a3b8; font-weight: 500; display: flex; align-items: center; gap: 6px; }
        .co-brand span { color: var(--accent); font-weight: 700; }

        /* Main Container */
        main { flex: 1; padding: 2rem; display: flex; flex-direction: column; align-items: center; }

        /* Animated Upload Zone */
        .upload-card {
            background: var(--card-bg);
            border: 2px dashed rgba(99, 102, 241, 0.4);
            border-radius: 20px;
            padding: 4rem 2rem;
            text-align: center;
            max-width: 600px;
            width: 100%;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            animation: fadeIn 0.8s ease-out;
        }

        .upload-card:hover {
            border-color: var(--primary);
            transform: translateY(-4px);
            box-shadow: 0 15px 35px rgba(99, 102, 241, 0.2);
        }

        .upload-icon { font-size: 3.5rem; color: var(--primary); margin-bottom: 1rem; animation: bounce 2s infinite; }
        .btn-upload { background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; padding: 12px 28px; border-radius: 30px; border: none; font-weight: 600; margin-top: 1.5rem; cursor: pointer; transition: 0.2s; }
        .btn-upload:hover { opacity: 0.9; transform: scale(1.03); }

        /* Editor Workspace */
        #editor-workspace { display: none; width: 100%; max-width: 1000px; animation: fadeIn 0.5s ease-in-out; }
        .toolbar {
            background: var(--card-bg);
            padding: 1rem;
            border-radius: 12px;
            display: flex;
            gap: 12px;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
            align-items: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }

        .tool-btn {
            background: #334155;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: 0.2s;
        }
        .tool-btn:hover, .tool-btn.active { background: var(--primary); }

        .action-btn { background: #10b981; margin-left: auto; }
        .action-btn:hover { background: #059669; }

        /* PDF Render Area */
        .pdf-container {
            display: flex;
            flex-direction: column;
            gap: 2rem;
            align-items: center;
        }

        .page-wrapper {
            position: relative;
            background: white;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border-radius: 4px;
            overflow: hidden;
        }

        .text-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
        }

        .editable-text {
            position: absolute;
            background: rgba(255, 255, 255, 0.9);
            border: 1px dashed var(--primary);
            color: #000;
            padding: 2px 4px;
            border-radius: 2px;
            outline: none;
            pointer-events: auto;
            min-width: 20px;
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
    </style>
</head>
<body>

    <!-- Header Section -->
    <header>
        <div class="brand-container">
            <!-- Edit.Me Logo SVG -->
            <svg class="logo-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18.5 2.50001C18.8978 2.10219 19.4374 1.87868 20 1.87868C20.5626 1.87868 21.1022 2.10219 21.5 2.50001C21.8978 2.89784 22.1213 3.43739 22.1213 4.00001C22.1213 4.56263 21.8978 5.10219 21.5 5.50001L12 15L8 16L9 12L18.5 2.50001Z" stroke="#06b6d4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="brand-title">Edit.Me</span>
        </div>
        <div class="co-brand">
            Co-Powered by <span>CareerBoot</span>
        </div>
    </header>

    <!-- Main Content -->
    <main>
        <!-- Step 1: Upload Card -->
        <div class="upload-card" id="upload-card" onclick="document.getElementById('file-input').click()">
            <i class="fa-solid fa-file-pdf upload-icon"></i>
            <h2>Upload your PDF Document</h2>
            <p style="color: #94a3b8; margin-top: 8px;">Click or drag and drop your file here to edit inline</p>
            <button class="btn-upload">Select File</button>
            <input type="file" id="file-input" accept="application/pdf" style="display: none;" onchange="handleFileSelect(event)">
        </div>

        <!-- Step 2: Interactive Editor -->
        <div id="editor-workspace">
            <div class="toolbar">
                <button class="tool-btn active" onclick="setMode('text')"><i class="fa-solid fa-font"></i> Add/Edit Text</button>
                <button class="tool-btn action-btn" onclick="exportPDF()"><i class="fa-solid fa-download"></i> Save & Download</button>
                <button class="tool-btn" onclick="window.print()"><i class="fa-solid fa-print"></i> Print</button>
            </div>
            <div id="pdf-container" class="pdf-container"></div>
        </div>
    </main>

    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
        let pdfBytes = null;
        let pdfDoc = null;
        let annotations = [];

        async function handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;

            pdfBytes = await file.arrayBuffer();
            document.getElementById('upload-card').style.display = 'none';
            document.getElementById('editor-workspace').style.display = 'block';

            renderPDF(pdfBytes);
        }

        async function renderPDF(data) {
            const loadingTask = pdfjsLib.getDocument({ data });
            pdfDoc = await loadingTask.promise;
            const container = document.getElementById('pdf-container');
            container.innerHTML = '';

            for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
                const page = await pdfDoc.getPage(pageNum);
                const viewport = page.getViewport({ scale: 1.5 });

                const wrapper = document.createElement('div');
                wrapper.className = 'page-wrapper';
                wrapper.style.width = `${viewport.width}px`;
                wrapper.style.height = `${viewport.height}px`;

                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                const renderContext = { canvasContext: context, viewport: viewport };
                await page.render(renderContext).promise;

                const overlay = document.createElement('div');
                overlay.className = 'text-overlay';
                overlay.dataset.pageNum = pageNum;

                // Click to add text overlay element directly on the page
                wrapper.onclick = (e) => {
                    if(e.target !== wrapper && e.target !== canvas) return;
                    const rect = wrapper.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;

                    const input = document.createElement('div');
                    input.contentEditable = true;
                    input.className = 'editable-text';
                    input.style.left = `${x}px`;
                    input.style.top = `${y}px`;
                    input.innerText = 'New Text';

                    overlay.appendChild(input);
                    input.focus();

                    annotations.push({ pageNum, x, y, input });
                };

                wrapper.appendChild(canvas);
                wrapper.appendChild(overlay);
                container.appendChild(wrapper);
            }
        }

        async function exportPDF() {
            const { PDFDocument, rgb } = PDFLib;
            const loadedPdf = await PDFDocument.load(pdfBytes);

            for (const item of annotations) {
                const page = loadedPdf.getPage(item.pageNum - 1);
                const { height } = page.getSize();
                
                // Scale factor between Canvas viewport scale (1.5) and PDF coordinates
                const text = item.input.innerText;
                if(text) {
                    page.drawText(text, {
                        x: item.x / 1.5,
                        y: height - (item.y / 1.5) - 10,
                        size: 12,
                        color: rgb(0, 0, 0),
                    });
                }
            }

            const modifiedPdfBytes = await loadedPdf.save();
            const blob = new Blob([modifiedPdfBytes], { type: 'application/pdf' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'edited_document.pdf';
            link.click();
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
