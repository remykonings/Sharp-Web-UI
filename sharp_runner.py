import subprocess
import os
import shutil
import sys

# --- CONFIGURATION ---
OUTPUT_DIR = os.path.join(os.getcwd(), "generated_splats")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# How many generation folders to keep before deleting the oldest ones
MAX_GENERATIONS = 50 


def resolve_sharp_executable():
    """
    Resolves the SHARP CLI executable in environments where PATH may not be
    initialized (e.g. app launched from Finder).
    """
    sharp_from_env = os.environ.get("SHARP_EXECUTABLE")
    if sharp_from_env:
        return sharp_from_env

    in_path = shutil.which("sharp")
    if in_path:
        return in_path

    # If launched with a venv Python binary, try sibling "sharp" script.
    sibling_sharp = os.path.join(os.path.dirname(sys.executable), "sharp")
    if os.path.exists(sibling_sharp):
        return sibling_sharp

    return "sharp"

def cleanup_old_generations():
    """
    Checks the output folder. If there are more than MAX_GENERATIONS folders,
    it deletes the oldest ones to save space.
    """
    try:
        # 1. Get a list of all folders in the output directory
        folders = [
            os.path.join(OUTPUT_DIR, d) 
            for d in os.listdir(OUTPUT_DIR) 
            if os.path.isdir(os.path.join(OUTPUT_DIR, d))
        ]
        
        # 2. Sort them by creation time (Oldest first)
        folders.sort(key=os.path.getctime)
        
        # 3. Check if we need to delete any
        if len(folders) >= MAX_GENERATIONS:
            num_to_delete = len(folders) - MAX_GENERATIONS + 1
            print(f"--- Cleanup: Deleting {num_to_delete} old generations... ---")
            
            for i in range(num_to_delete):
                folder_to_remove = folders[i]
                print(f"Removing: {folder_to_remove}")
                shutil.rmtree(folder_to_remove)
                
    except Exception as e:
        print(f"Warning: Cleanup failed. {e}")

def run_sharp_generation(input_image_path):
    """
    Runs SHARP on a single image.
    """
    if not input_image_path:
        return None, "Error: You didn't provide an input image."

    # --- STEP 0: Run Cleanup ---
    cleanup_old_generations()

    # 1. Setup the workspace
    filename = os.path.basename(input_image_path)
    base_name = os.path.splitext(filename)[0]
    
    # Create the folder if it doesn't exist
    job_dir = os.path.join(OUTPUT_DIR, base_name)
    os.makedirs(job_dir, exist_ok=True)

    print(f"--- Starting Generation for {base_name} ---")

    # 2. Build the Command
    command = [
        resolve_sharp_executable(), "predict",
        "-i", input_image_path,
        "-o", job_dir
    ]

    try:
        # 3. Execute
        subprocess.run(
            command, 
            check=True,
            capture_output=True,
            text=True
        )
        
        # 4. Find the prize
        found_ply = None
        for root, dirs, files in os.walk(job_dir):
            for file in files:
                if file.endswith(".ply"):
                    found_ply = os.path.join(root, file)
                    break
        
        if found_ply:
            return found_ply, f"Success! Generated {base_name}.ply"
        else:
            return None, f"Error: SHARP finished, but I couldn't find a .ply file in {base_name}."

    except subprocess.CalledProcessError as e:
        error_msg = f"Error running SHARP:\n{e.stderr}"
        print(error_msg)
        return None, error_msg

    except FileNotFoundError:
        return None, (
            "Error: SHARP CLI was not found. Ensure ml-sharp is installed in the "
            "same Python environment, or set SHARP_EXECUTABLE to the full path."
        )
        
    except Exception as e:
        return None, f"System Error: {str(e)}"
