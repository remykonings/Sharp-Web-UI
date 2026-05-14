import gradio as gr
import os
import sharp_runner
import zipfile
from urllib.parse import quote, urlencode

# Configuration
ASSETS_DIR = os.path.join(os.getcwd(), "assets")
OUTPUT_DIR = os.path.join(os.getcwd(), "generated_splats")


def build_empty_preview_html(title, subtitle):
    return f"""
    <div class="preview-empty">
        <div class="preview-empty-title">{title}</div>
        <div class="preview-empty-subtitle">{subtitle}</div>
    </div>
    """

# --- Helper: Zip Creator ---
def create_zip_of_files(file_paths):
    if not file_paths: return None
    zip_path = os.path.join(OUTPUT_DIR, "batch_results.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in file_paths:
            zipf.write(file, os.path.basename(file))
    return zip_path

# --- Logic: Viewer & Single Downloader ---
def load_selected_model(ply_path):
    if not ply_path:
        empty_html = build_empty_preview_html(
            "Select a model to preview",
            "Generate a splat or choose one from the list to render it here."
        )
        return empty_html, None
    
    viewer_abs_path = os.path.join(ASSETS_DIR, "viewer.html")
    viewer_abs_path = viewer_abs_path.replace("\\", "/")
    web_ply_path = ply_path.replace("\\", "/") 
    
    # Gradio 5+ serves local files under /gradio_api/file=
    viewer_file_url = f"/gradio_api/file={quote(viewer_abs_path)}"
    ply_file_url = f"/gradio_api/file={quote(web_ply_path)}"
    iframe_src = f"{viewer_file_url}?{urlencode({'url': ply_file_url})}"
    
    viewer_html = f"""
    <iframe 
        class="viewer-frame"
        src="{iframe_src}" 
        width="100%" 
        height="620px"
        style="border:0; border-radius:14px; background:#111214;"
        allow="camera; microphone; fullscreen; accelerometer; gyroscope; magnetometer"
    ></iframe>
    """
    
    return viewer_html, ply_path

# --- Logic: Core Generator ---
def core_generation_logic(image_paths):
    if not image_paths:
        return (
            "Please upload an image.", 
            gr.update(visible=False), 
            gr.update(choices=[], value=None), 
            None, 
            gr.update(visible=False)
        )

    generated_files = []
    log_messages = []

    for i, path in enumerate(image_paths):
        msg_prefix = f"[{i+1}/{len(image_paths)}] Processing {os.path.basename(path)}..."
        print(msg_prefix)
        
        ply_path, message = sharp_runner.run_sharp_generation(path)
        
        if ply_path:
            generated_files.append(ply_path)
            log_messages.append(f"{os.path.basename(path)}: Success")
        else:
            log_messages.append(f"{os.path.basename(path)}: Failed ({message})")

    full_log = "\n".join(log_messages)
    
    if not generated_files:
        return full_log, gr.update(visible=False), gr.update(choices=[], value=None), None, gr.update(visible=False)

    if len(generated_files) > 1:
        zip_path = create_zip_of_files(generated_files)
        zip_update = gr.update(value=zip_path, visible=True)
    else:
        zip_update = gr.update(value=None, visible=False)

    dropdown_choices = [(os.path.basename(p), p) for p in generated_files]
    
    first_model = generated_files[0]
    first_viewer_html, first_download_path = load_selected_model(first_model)
    
    return (
        full_log, 
        zip_update, 
        gr.update(choices=dropdown_choices, value=first_model), 
        first_viewer_html, 
        gr.update(value=first_download_path, visible=True)
    )

# --- Wrappers for UI Buttons ---
def process_single(image_path):
    if not image_path: return core_generation_logic([])
    return core_generation_logic([image_path])

def process_batch(file_objs):
    if not file_objs: return core_generation_logic([])
    paths = [f.name for f in file_objs]
    return core_generation_logic(paths)


# --- Layout ---
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --app-bg: #f2f2f3;
    --panel-bg: rgba(255, 255, 255, 0.92);
    --panel-border: #d8d9dd;
    --text-strong: #17181a;
    --text-muted: #5f636a;
    --brand: #3b3f45;
    --brand-strong: #2e3136;
}

.gradio-container {
    font-family: "Manrope", "Segoe UI", sans-serif !important;
    background:
        radial-gradient(1200px 460px at 18% -8%, #f9f9fa 0%, transparent 62%),
        radial-gradient(850px 380px at 100% -18%, #ebecef 0%, transparent 60%),
        var(--app-bg);
    min-height: 100vh;
    padding: 22px 22px 30px !important;
}

.gradio-container .prose { max-width: 100% !important; }

#app-shell {
    max-width: 1240px;
    margin: 0 auto;
    gap: 14px;
}

.hero {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 20px;
    padding: 20px 24px;
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.06);
}

.hero-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}

.hero-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: #eeeff1;
    color: var(--brand);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.hero-link {
    color: #4f535a;
    text-decoration: none;
    font-weight: 600;
    font-size: 13px;
}

.hero h1 {
    margin: 0;
    color: var(--text-strong);
    font-size: 32px;
    line-height: 1.1;
    letter-spacing: -0.02em;
}

.hero p {
    margin: 10px 0 0;
    color: var(--text-muted);
    font-size: 15px;
}

.panel {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 20px;
    padding: 16px;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.05);
    backdrop-filter: blur(4px);
}

.section-title {
    margin: 0 0 10px !important;
}

.section-title h4 {
    margin: 0 !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #5b6068 !important;
}

.primary-btn button {
    width: 100%;
    min-height: 46px !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, var(--brand), #2f3238) !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.24);
}

.primary-btn button:hover {
    background: linear-gradient(135deg, var(--brand-strong), var(--brand)) !important;
}

#status-log textarea {
    font-family: "SF Mono", ui-monospace, Menlo, monospace !important;
    font-size: 12px !important;
    background: #f6f6f7 !important;
    border-radius: 12px !important;
}

#status-log label {
    color: #5b6068 !important;
    font-weight: 600 !important;
}

.result-group {
    border: 1px solid #e1e2e6 !important;
    border-radius: 14px !important;
    padding: 10px !important;
    background: #fcfcfc;
}

.preview-empty {
    height: 620px;
    border-radius: 14px;
    border: 1px solid #232529;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #eceef2;
    background:
        radial-gradient(circle at 20% 12%, rgba(255, 255, 255, 0.08), transparent 40%),
        linear-gradient(145deg, #111214 0%, #17181b 45%, #202226 100%);
}

.preview-empty-title {
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.01em;
}

.preview-empty-subtitle {
    margin-top: 8px;
    max-width: 420px;
    color: #cfd2d8;
    font-size: 13px;
}

#viewer-html iframe {
    border: 1px solid #d2d3d7 !important;
    border-radius: 14px !important;
    box-shadow: inset 0 0 0 1px #202226;
}

@media (max-width: 900px) {
    .gradio-container {
        padding: 12px !important;
    }

    .hero {
        padding: 16px;
    }

    .hero h1 {
        font-size: 26px;
    }

    .preview-empty {
        height: 420px;
    }
}
"""

with gr.Blocks(title="Sharp Web UI", theme=gr.themes.Monochrome(), css=custom_css) as demo:
    with gr.Column(elem_id="app-shell"):
        gr.HTML(
            """
            <section class="hero">
                <div class="hero-top">
                    <span class="hero-badge">SHARP · Monocular View Synthesis</span>
                    <a class="hero-link" href="https://github.com/apple/ml-sharp" target="_blank" rel="noopener noreferrer">ml-sharp</a>
                </div>
                <h1>Sharp Web UI</h1>
                <p>Generate 3D Gaussian splats from single images and inspect them instantly in your browser.</p>
            </section>
            """
        )

        with gr.Row(equal_height=True):
            with gr.Column(scale=1, elem_classes=["panel", "controls-panel"]):
                gr.Markdown("#### Input", elem_classes="section-title")
                with gr.Tabs():
                    with gr.TabItem("Single Image"):
                        single_input = gr.Image(type="filepath", label="Input Image", container=True)
                        btn_single = gr.Button(
                            "Generate Single Splat",
                            variant="primary",
                            size="lg",
                            elem_classes="primary-btn"
                        )

                    with gr.TabItem("Batch Upload"):
                        batch_input = gr.File(
                            file_count="multiple",
                            file_types=["image"],
                            label="Drop Multiple Files Here"
                        )
                        btn_batch = gr.Button(
                            "Generate Batch",
                            variant="primary",
                            size="lg",
                            elem_classes="primary-btn"
                        )

                gr.Markdown("#### Status", elem_classes="section-title")
                status_log = gr.Textbox(label="Generation Log", interactive=False, lines=4, elem_id="status-log")

                gr.Markdown("#### Exports", elem_classes="section-title")
                with gr.Group(elem_classes="result-group"):
                    model_selector = gr.Dropdown(
                        label="Select Splat",
                        choices=[],
                        interactive=True,
                        filterable=False
                    )
                    download_single = gr.File(label="Download Selected .ply", interactive=False, visible=False)

                download_zip = gr.File(label="Download All (.zip)", interactive=False, visible=False)

            with gr.Column(scale=2, elem_classes=["panel", "preview-panel"]):
                gr.Markdown("#### Live Preview", elem_classes="section-title")
                viewer_html = gr.HTML(
                    value=build_empty_preview_html(
                        "Preview will appear here",
                        "Generate a splat on the left and interact with it in real time."
                    ),
                    elem_id="viewer-html"
                )

    # --- Event Wiring ---
    btn_single.click(
        fn=process_single,
        inputs=single_input,
        outputs=[status_log, download_zip, model_selector, viewer_html, download_single]
    )
    
    btn_batch.click(
        fn=process_batch,
        inputs=batch_input,
        outputs=[status_log, download_zip, model_selector, viewer_html, download_single]
    )
    
    model_selector.change(
        fn=load_selected_model,
        inputs=model_selector,
        outputs=[viewer_html, download_single]
    )

if __name__ == "__main__":
    print("App launching...")
    demo.launch(
        server_name="127.0.0.1", 
        server_port=7880,
        allowed_paths=[ASSETS_DIR, OUTPUT_DIR, "/"]
    )
