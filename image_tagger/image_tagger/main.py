import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from google.cloud import vision
import piexif

class ImageProcessor:
    """Handles the business logic of finding, tagging, and updating images."""
    def discover_images(self, base_path):
        if not os.path.isdir(base_path):
            return None, "Invalid directory path."

        supported_formats = ('.jpg', '.jpeg', '.png', '.gif')
        image_paths = []
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith(supported_formats):
                    image_paths.append(os.path.join(root, file))

        if not image_paths:
            return [], "No images found in the selected directory."

        return image_paths, None

    def get_tags_from_vision_api(self, image_path, vision_client):
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = vision_client.label_detection(image=image)
        labels = response.label_annotations

        if labels:
            return ', '.join([label.description for label in labels])
        return ""

    def write_exif_tags(self, image_path, tags):
        try:
            exif_dict = piexif.load(image_path)
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = tags.encode('utf-8')
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, image_path)
        except Exception as e:
            print(f"Could not write EXIF data to {image_path}: {e}")
            # If writing to ImageDescription fails, try UserComment
            try:
                exif_dict = piexif.load(image_path)
                exif_dict['Exif'][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(tags, encoding="unicode")
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, image_path)
            except Exception as e2:
                print(f"Could not write EXIF UserComment to {image_path}: {e2}")
                return False
        return True


class ImageTaggerApp:
    def __init__(self, root, image_processor):
        self.root = root
        self.root.title("Image Tagger")
        self.image_processor = image_processor

        # Folder selection
        self.folder_frame = tk.Frame(root)
        self.folder_frame.pack(pady=5)

        self.browse_button = tk.Button(self.folder_frame, text="Browse", command=self.browse_folder)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        self.folder_path = tk.StringVar()
        self.folder_entry = tk.Entry(self.folder_frame, textvariable=self.folder_path, width=50)
        self.folder_entry.pack(side=tk.LEFT)

        # Image list
        self.image_list_frame = tk.Frame(root)
        self.image_list_frame.pack(pady=5)

        self.image_list_label = tk.Label(self.image_list_frame, text="Images to be tagged:")
        self.image_list_label.pack()

        self.image_listbox = tk.Listbox(self.image_list_frame, width=80, height=15)
        self.image_listbox.pack()

        # Action button
        self.start_button = tk.Button(root, text="Start Tagging", command=self.start_tagging_thread)
        self.start_button.pack(pady=5)

        # Status area
        self.status_label = tk.Label(root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        # Setup instructions
        self.setup_frame = tk.LabelFrame(root, text="Google Cloud Setup Instructions")
        self.setup_frame.pack(pady=10, padx=10, fill=tk.X)

        self.setup_text = scrolledtext.ScrolledText(self.setup_frame, height=10, wrap=tk.WORD)
        self.setup_text.pack(expand=True, fill=tk.X)
        self.setup_text.insert(tk.INSERT, self.get_setup_instructions())
        self.setup_text.config(state=tk.DISABLED)

        self.vision_client = None

    def get_setup_instructions(self):
        return """
8. Google Cloud Setup
8.1 Using the Google Cloud Console (GUI)
- Create a new Google Cloud Project:
  - Go to the Google Cloud Console: https://console.cloud.google.com/
  - Create a new project.
- Enable the Cloud Vision API:
  - In your project, go to "APIs & Services" > "Library".
  - Search for "Cloud Vision API" and enable it. This requires linking a billing account.
- Create a Service Account:
  - Go to "APIs & Services" > "Credentials".
  - Click "Create Credentials" > "Service account".
  - Give it a name, and grant it the "Cloud Vision AI User" role.
  - Click "Done".
  - Under "Service Accounts", find your new account, click the three dots under "Actions", and select "Manage keys".
  - Click "Add Key" > "Create new key", choose JSON, and click "Create".
  - A JSON file will be downloaded. Keep it secure.
- Set Environment Variable:
  - You need to tell the application where to find your credentials file. Set an environment variable named GOOGLE_APPLICATION_CREDENTIALS to the full path of the downloaded JSON file.

8.2 Using the gcloud Command-Line Tool (CLI)
- Install and Initialize gcloud: Install the Google Cloud SDK and run gcloud init.
- Create a New Project & Link Billing:
  - # Create the project
    gcloud projects create YOUR_UNIQUE_PROJECT_ID
  - # Set the project as default
    gcloud config set project YOUR_UNIQUE_PROJECT_ID
  - # List billing accounts
    gcloud billing accounts list
  - # Link billing account
    gcloud billing projects link YOUR_UNIQUE_PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT_ID
- Enable the Cloud Vision API:
  - gcloud services enable vision.googleapis.com
- Create a Service Account:
  - gcloud iam service-accounts create image-tagger-sa --display-name="Image Tagger SA"
- Grant Permissions:
  - gcloud projects add-iam-policy-binding YOUR_UNIQUE_PROJECT_ID \\
    --member="serviceAccount:image-tagger-sa@YOUR_UNIQUE_PROJECT_ID.iam.gserviceaccount.com" \\
    --role="roles/vision.user"
- Create and Download the JSON Key:
  - gcloud iam service-accounts keys create credentials.json \\
    --iam-account="image-tagger-sa@YOUR_UNIQUE_PROJECT_ID.iam.gserviceaccount.com"
  - This creates credentials.json in your current directory.
- Set the Environment Variable:
  - macOS/Linux: export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"
  - Windows: setx GOOGLE_APPLICATION_CREDENTIALS "%cd%\\credentials.json"
"""

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            self.populate_image_list()

    def populate_image_list(self):
        self.image_listbox.delete(0, tk.END)
        base_path = self.folder_path.get()

        image_paths, error_message = self.image_processor.discover_images(base_path)

        if error_message:
            if image_paths is None: # Invalid path
                messagebox.showerror("Error", error_message)
            else: # No images found
                messagebox.showinfo("Info", error_message)
            return

        for path in image_paths:
            self.image_listbox.insert(tk.END, path)

    def start_tagging_thread(self):
        if not self.image_listbox.get(0, tk.END):
            messagebox.showinfo("Info", "No images to tag.")
            return

        self.start_button.config(state=tk.DISABLED)
        self.status_label.config(text="Starting...")

        thread = threading.Thread(target=self.start_tagging_process)
        thread.start()

    def start_tagging_process(self):
        try:
            if not self.vision_client:
                self.vision_client = vision.ImageAnnotatorClient()
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to authenticate with Google Cloud Vision API: {e}")
            self.start_button.config(state=tk.NORMAL)
            self.status_label.config(text="Authentication failed.")
            return

        images_to_process = list(self.image_listbox.get(0, tk.END))
        total_images = len(images_to_process)

        for i, image_path in enumerate(images_to_process):
            self.status_label.config(text=f"Processing image {i+1}/{total_images}: {os.path.basename(image_path)}")
            self.root.update_idletasks()

            try:
                tags = self.image_processor.get_tags_from_vision_api(image_path, self.vision_client)
                if tags:
                    self.image_processor.write_exif_tags(image_path, tags)

                self.image_listbox.delete(0)
                self.root.update_idletasks()

            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                continue

        self.status_label.config(text="Tagging complete.")
        self.start_button.config(state=tk.NORMAL)
        messagebox.showinfo("Success", "All images have been tagged.")


def main():
    root = tk.Tk()
    image_processor = ImageProcessor()
    app = ImageTaggerApp(root, image_processor)
    root.mainloop()

if __name__ == "__main__":
    main()
