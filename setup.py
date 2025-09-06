from setuptools import setup, find_packages

setup(
    name="image-tagger",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'gui_scripts': [
            'image-tagger = image_tagger.main:main',
        ],
    },
    install_requires=[
        "google-cloud-vision",
        "piexif",
    ],
)
