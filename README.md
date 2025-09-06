Project Specification: Python Image Tagger with Google Cloud Vision

1. Overview
This document outlines the project specification for a Python application that automatically tags image files using the Google Cloud Vision API. The application will provide a graphical user interface (GUI) to select a base folder, display the images to be processed, and show the progress of the tagging operation. The generated tags will be written to the EXIF metadata of each image file.

2. Features
- GUI: A user-friendly graphical interface built with Tkinter.
- Recursive Image Discovery: The application will scan a user-specified directory and all its subdirectories for image files.
- Supported Image Formats: The application will support common image formats like JPEG, PNG, and GIF.
- Image List View: A list view will display all the discovered images waiting to be tagged. As images are processed, they will be removed from this list.
- Google Cloud Vision Integration: The application will use the Google Cloud Vision API to detect labels (tags) for each image.
- Metadata Writing: The retrieved tags will be written to the image's EXIF metadata (specifically, the ImageDescription or UserComment fields).
- Progress Indication: The UI will provide clear feedback to the user about the current operation, including which image is being processed and the remaining count.
- Error Handling: The application will handle potential errors, such as invalid file paths, images without EXIF support, and API authentication issues.
- Google Cloud Project Setup Instructions: The user will be guided on how to set up a Google Cloud project and enable the Vision API.

3. Technical Stack
- Language: Python 3.x
- GUI Framework: Tkinter (standard library)
- Google Cloud Vision API: google-cloud-vision client library
- Image Metadata Handling: piexif library
- Packaging: setuptools

4. User Interface (UI) Design
The main window of the application will consist of the following components:
- Folder Selection:
  - A "Browse" button to open a directory chooser dialog.
  - A text field to display the selected folder path.
- Image List:
  - A listbox or treeview widget to display the file paths of the images to be processed.
- Action Button:
  - A "Start Tagging" button to begin the image processing workflow.
- Status Area:
  - A label or status bar to display progress information, such as "Processing image.jpg..." or "Tagging complete."
- Setup Instructions:
  - A text area or label providing clear, step-by-step instructions for setting up the Google Cloud project and authentication (See Section 8 for details).

5. Workflow
- Initialization: The user launches the application. The main window appears.
- Folder Selection: The user clicks the "Browse" button and selects a base folder containing images.
- Image Discovery: The application recursively scans the selected folder and its subfolders for files with .jpg, .jpeg, .png, and .gif extensions. The found image paths are populated into the list view.
- Start Tagging: The user clicks the "Start Tagging" button.
- API Authentication: The application authenticates with the Google Cloud Vision API using the credentials specified in the GOOGLE_APPLICATION_CREDENTIALS environment variable.
- Image Processing Loop: The application iterates through the list of images. For each image:
  - The status bar is updated to indicate which file is being processed.
  - The image file is read and sent to the Cloud Vision API's label_detection feature.
  - The API returns a list of labels (tags) with confidence scores.
  - The application extracts the descriptions of the labels.
  - These descriptions are concatenated into a single string.
  - The piexif library is used to write this tag string to the ImageDescription field in the image's EXIF data.
  - The processed image is removed from the list view.
- Completion: Once all images have been processed, a "Done" or "Completed" message is displayed in the status area.

6. Error Handling
- Invalid Path: If the user selects an invalid directory, a message box will be shown.
- No Images Found: If the selected directory contains no supported image files, a message will be displayed.
- API Errors: If there is an authentication error or another issue with the Vision API, a descriptive error message will be displayed.
- Metadata Errors: If an image does not support EXIF metadata or an error occurs while writing metadata, the error will be logged, and the application will proceed to the next image.

7. Project Structure
```
image-tagger/
│
├── image_tagger/
│   ├── __init__.py
│   └── main.py         # Main application logic and GUI
│
├── setup.py            # Project setup script
├── requirements.txt    # Python dependencies
└── README.md           # This project specification
```

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
  ```
  # Create the project
  gcloud projects create YOUR_UNIQUE_PROJECT_ID

  # Set the project as default
  gcloud config set project YOUR_UNIQUE_PROJECT_ID

  # List billing accounts
  gcloud billing accounts list

  # Link billing account
  gcloud billing projects link YOUR_UNIQUE_PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT_ID
  ```
- Enable the Cloud Vision API:
  ```
  gcloud services enable vision.googleapis.com
  ```
- Create a Service Account:
  ```
  gcloud iam service-accounts create image-tagger-sa --display-name="Image Tagger SA"
  ```
- Grant Permissions:
  ```
  gcloud projects add-iam-policy-binding YOUR_UNIQUE_PROJECT_ID \
    --member="serviceAccount:image-tagger-sa@YOUR_UNIQUE_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/vision.user"
  ```
- Create and Download the JSON Key:
  ```
  gcloud iam service-accounts keys create credentials.json \
    --iam-account="image-tagger-sa@YOUR_UNIQUE_PROJECT_ID.iam.gserviceaccount.com"
  ```
  This creates credentials.json in your current directory.
- Set the Environment Variable:
  - macOS/Linux: `export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"`
  - Windows: `setx GOOGLE_APPLICATION_CREDENTIALS "%cd%\credentials.json"`
