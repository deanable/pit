import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Since the main script is in a subdirectory, we need to add it to the path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from image_tagger.image_tagger.main import ImageProcessor
from google.cloud import vision
import piexif


@pytest.fixture
def image_processor():
    return ImageProcessor()

@pytest.fixture
def temp_image_dir():
    temp_dir = tempfile.mkdtemp()
    # Create some dummy image files
    open(os.path.join(temp_dir, "test1.jpg"), "w").close()
    open(os.path.join(temp_dir, "test2.png"), "w").close()
    os.makedirs(os.path.join(temp_dir, "subdir"))
    open(os.path.join(temp_dir, "subdir", "test3.gif"), "w").close()
    open(os.path.join(temp_dir, "not_an_image.txt"), "w").close()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_discover_images(image_processor, temp_image_dir):
    discovered_images, error = image_processor.discover_images(temp_image_dir)

    assert error is None
    assert len(discovered_images) == 3
    # Sort for consistent order
    discovered_images.sort()
    expected_images = [
        os.path.join(temp_image_dir, "test1.jpg"),
        os.path.join(temp_image_dir, "test2.png"),
        os.path.join(temp_image_dir, "subdir", "test3.gif")
    ]
    expected_images.sort()

    assert discovered_images == expected_images

def test_discover_images_no_images(image_processor, tmpdir):
    p = tmpdir.mkdir("sub")
    open(os.path.join(p, "test.txt"), "w").close()
    images, err = image_processor.discover_images(str(p))
    assert err == "No images found in the selected directory."
    assert images == []

def test_discover_images_invalid_path(image_processor):
    images, err = image_processor.discover_images("/a/b/c/nonexistent/path")
    assert err == "Invalid directory path."
    assert images is None

@patch('image_tagger.image_tagger.main.vision.ImageAnnotatorClient')
def test_get_tags_from_vision_api(mock_vision_client, image_processor, temp_image_dir):
    # Setup mock for Vision API
    mock_client_instance = mock_vision_client.return_value
    mock_label = MagicMock()
    mock_label.description = "test_tag"
    mock_response = MagicMock()
    mock_response.label_annotations = [mock_label, MagicMock(description="another_tag")]
    mock_client_instance.label_detection.return_value = mock_response

    image_path = os.path.join(temp_image_dir, "test1.jpg")
    tags = image_processor.get_tags_from_vision_api(image_path, mock_client_instance)

    assert tags == "test_tag, another_tag"
    mock_client_instance.label_detection.assert_called_once()


@patch.object(piexif, 'insert')
@patch.object(piexif, 'dump')
@patch.object(piexif, 'load')
def test_write_exif_tags(mock_load, mock_dump, mock_insert, image_processor, temp_image_dir):
    # The dictionary that piexif.load will return.
    exif_data = {'0th': {}, 'Exif': {}}
    mock_load.return_value = exif_data

    image_path = os.path.join(temp_image_dir, "test1.jpg")
    tags = "tag1, tag2"

    result = image_processor.write_exif_tags(image_path, tags)

    assert result is True
    mock_load.assert_called_once_with(image_path)
    mock_dump.assert_called_once_with(exif_data)
    mock_insert.assert_called_once()

    # Check that the '0th' dictionary was modified.
    assert exif_data['0th'][piexif.ImageIFD.ImageDescription] == tags.encode('utf-8')
    # Check that the 'Exif' dictionary was NOT modified.
    assert piexif.ExifIFD.UserComment not in exif_data['Exif']
