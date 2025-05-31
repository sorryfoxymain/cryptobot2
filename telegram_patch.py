import os
from PIL import Image
from typing import Optional, Union, BinaryIO

def is_image(file_path: str) -> Optional[str]:
    """
    Check if file is an image using Pillow instead of imghdr.
    Returns the image format if it's an image, None otherwise.
    """
    try:
        with Image.open(file_path) as img:
            return img.format.lower()
    except:
        return None

class PatchedInputFile:
    def __init__(
        self,
        obj: Union[str, BinaryIO],
        filename: Optional[str] = None,
        attach: bool = True,
    ):
        self.attach = attach
        self.filename = None
        self.input_file_content = None

        if isinstance(obj, str):
            if os.path.exists(obj):
                self.filename = os.path.basename(obj) if filename is None else filename
                self.input_file_content = open(obj, 'rb')
                # Check if it's an image using Pillow
                if is_image(obj):
                    self.mimetype = f'image/{is_image(obj)}'
                else:
                    self.mimetype = 'application/octet-stream'
            else:
                self.filename = filename or "file.txt"
                self.input_file_content = obj.encode('utf-8')
                self.mimetype = 'text/plain'
        else:
            self.filename = filename or "file"
            self.input_file_content = obj
            self.mimetype = 'application/octet-stream'

    def __del__(self):
        if hasattr(self.input_file_content, 'close'):
            self.input_file_content.close()

# Monkey patch the telegram.InputFile
def apply_patch():
    import telegram.files.inputfile
    telegram.files.inputfile.InputFile = PatchedInputFile 