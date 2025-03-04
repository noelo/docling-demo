import httpx
import os
import json


async_client = httpx.Client(timeout=60.0)
url = "https://docling-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1alpha/convert/file"
headers = {'Authorization': 'Bearer 15bf5c52e409f655989f0450bc575eba'}
parameters = {
"from_formats": ["docx", "pptx", "html", "image", "pdf", "asciidoc", "md", "xlsx"],
"to_formats": ["md", "json", "html", "text", "doctags"],
"image_export_mode": "placeholder",
"do_ocr": True,
"force_ocr": False,
"ocr_engine": "easyocr",
"ocr_lang": ["en"],
"pdf_backend": "dlparse_v2",
"table_mode": "fast",
"abort_on_error": False,
"return_as_file": False
}

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, '2206.01062.pdf')

files = {
    'files': ('2206.01062v1.pdf', open(file_path, 'rb'), 'application/pdf'),
}

response = async_client.post(url, files=files, headers=headers,data={"parameters": json.dumps(parameters)})
assert response.status_code == 200, "Response should be 200 OK"

data = response.json()