import os
import requests
import zipfile
from tqdm import tqdm

# Setup output directory
output_dir = "data/raw"
os.makedirs(output_dir, exist_ok=True)

def download_selected_files():
    """Only important files download karta hai - 100-200 matches max"""
    selected_links = [
        "https://cricsheet.org/downloads/ipl_json.zip",    # IPL (limited matches)
        "https://cricsheet.org/downloads/t20s_json.zip",   # T20 International (recent ones)
    ]
    
    print(f"Downloading only {len(selected_links)} important files...")
    
    for link in tqdm(selected_links, desc="Downloading files"):
        try:
            filename = link.split("/")[-1]
            filepath = os.path.join(output_dir, filename)
            
            response = requests.get(link, stream=True, timeout=30)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Extract ZIP file
                try:
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        # Only extract first 50 files from each ZIP
                        all_files = zip_ref.namelist()
                        files_to_extract = all_files[:50]  # PEHLE 50 FILES HI
                        
                        for file in files_to_extract:
                            zip_ref.extract(file, output_dir)
                    
                    print(f"✓ Extracted {len(files_to_extract)} files from {filename}")
                    
                except zipfile.BadZipFile:
                    print(f"✗ Error: {filename} is not a valid ZIP file")
                
                # ZIP file delete karo
                os.remove(filepath)
                print(f"✓ Deleted ZIP file: {filename}")
            else:
                print(f"✗ Failed to download {filename}")
                
        except Exception as e:
            print(f"✗ Error downloading {link}: {e}")
            continue

def cleanup_extra_files():
    """Extra JSON files delete karta hai, only 100 keep karta hai"""
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    
    if len(json_files) > 100:
        # Pehle 100 files hi rakhlo
        files_to_keep = json_files[:100]
        files_to_delete = json_files[100:]
        
        for file in files_to_delete:
            os.remove(os.path.join(output_dir, file))
        
        print(f"✓ Deleted {len(files_to_delete)} extra files, kept {len(files_to_keep)}")

if __name__ == "__main__":
    download_selected_files()
    cleanup_extra_files()
    print("Download complete! Files data/raw/ mein save hui.")