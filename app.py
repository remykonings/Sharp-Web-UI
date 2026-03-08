import gradio as gr
import os
import sharp_runner
import zipfile
from urllib.parse import quote, urlencode

# Configuration
ASSETS_DIR = os.path.join(os.getcwd(), "assets")
OUTPUT_DIR = os.path.join(os.getcwd(), "generated_splats")

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
        empty_html = "<div style='height:600px; background:#000; color:#555; display:flex; align-items:center; justify-content:center;'>Select a model to preview</div>"
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
        src="{iframe_src}" 
        width="100%" 
        height="600px" 
        style="border: 1px solid #444; border-radius: 8px; background: #000;"
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
.gradio-container .prose { max-width: 100% !important; }
"""

with gr.Blocks(title="Sharp Web UI", theme=gr.themes.Soft(), css=custom_css) as demo:
    
    gr.Markdown(
        """
        # Sharp Web UI
        **This UI is built in Python using the Gradio framework, which manages the web server and frontend components. The 3D visualization is handled by a custom HTML/JavaScript integration powered by Three.js and the GaussianSplats3D library.**
        **Made by Ivan Tymoshenko** [GitHub Link](https://github.com/IvanTymoshenko)
        """
    )
    
    with gr.Row():
        # --- LEFT COLUMN ---
        with gr.Column(scale=1):
            
            gr.Markdown("### 1. Input")
            with gr.Tabs():
                # Tab 1: Single
                with gr.TabItem("Single Image"):
                    single_input = gr.Image(type="filepath", label="Input Image", container=True)
                    btn_single = gr.Button("Generate Single Splat", variant="primary", size="lg")
                
                # Tab 2: Batch
                with gr.TabItem("Batch Upload"):
                    batch_input = gr.File(file_count="multiple", file_types=["image"], label="Drop Multiple Files Here")
                    btn_batch = gr.Button("Generate Batch", variant="primary", size="lg")
            
            gr.Markdown("### 2. Status")
            status_log = gr.Textbox(label="Log", interactive=False, lines=3)
            
            gr.Markdown("### 3. Results")
            with gr.Group():
                # FIX: Added filterable=False to ensure clicking anywhere opens it
                model_selector = gr.Dropdown(
                    label="Select Splat", 
                    choices=[], 
                    interactive=True,
                    filterable=False 
                )
                
                download_single = gr.File(label="Download Selected .ply", interactive=False, visible=False)
            
            download_zip = gr.File(label="Download All (.zip)", interactive=False, visible=False)

        # --- RIGHT COLUMN ---
        with gr.Column(scale=2):
            viewer_html = gr.HTML(
                label="3D Preview", 
                value="<div style='height:600px; background:#111; color:#555; display:flex; align-items:center; justify-content:center;'>Preview will appear here</div>"
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
