import asyncio
import os
import json
import html
import logging
import argparse
from typing import Union
import requests
from dotenv import load_dotenv
from pathlib import Path
from docling.datamodel.document import DoclingDocument
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling_serve.response_preparation import ConvertDocumentResponse
from pydantic_core import from_json

_log = logging.getLogger(__name__)

async def remote_processing(input_file:str,escape_Flag:bool):
    docling_epr = os.environ.get('DOCLING_EPR', None)
    docling_token = os.environ.get('DOCLING_TOKEN', None)
    
    headers = {'Authorization': 'Bearer '+docling_token}
    
    parameters = {
        "from_formats": ["pdf"],
        "to_formats": ["json"],
        "image_export_mode": "placeholder",
        "do_ocr": False,
        "force_ocr": False,
        "ocr_engine": "easyocr",
        "ocr_lang": ["en"],
        "pdf_backend": "dlparse_v2",
        "table_mode": "accurate",
        "abort_on_error": False,
        "return_as_file": False,
        "include_images": False
        }
    
    fileContent = {
        'files': (input_file, open(input_file, 'rb'), 'application/pdf'),
    }   

    url = url=docling_epr+"/v1alpha/convert/file";
    resp = requests.post(url,
                        data=parameters,
                        headers=headers,
                        files=fileContent)  

    json_formatted_str = json.dumps(resp.json(), indent=2)

    ConvertDocumentResponse.model_validate_json(json_formatted_str)
    doc = ConvertDocumentResponse.model_validate(from_json(json_formatted_str))
    process_output(doc.document.json_content,escape_Flag)

def local_processing(input_file:str,escape_Flag:bool):
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_page_images = False
    pipeline_options.generate_table_images = False
    pipeline_options.generate_picture_images = False
    
    doc_converter = (
        DocumentConverter(  
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.IMAGE,
            ],  
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options,
                     backend=PyPdfiumDocumentBackend
                ),
            },
        )
    )
    conv_results = doc_converter.convert(input_file) 
    process_output(conv_results.document,escape_Flag)
    
    
def process_output(converted_doc: DoclingDocument,escape_Flag:bool):
    _log.info(f"Page Count:{len(converted_doc.pages)}")
    
    _log.info(f"Images count:{len(converted_doc.pictures)}") 
    for p in converted_doc.pictures:
        _log.info(f'    Image present on page {p.prov[0].page_no}') 
        
    _log.info(f"Table Count: {len(converted_doc.tables)}")
    for t in converted_doc.tables:
        _log.info(f'    Page:{t.prov[0].page_no} Cell count:{len(t.data.table_cells)} Dimensions:{t.data.num_rows} x {t.data.num_cols}') 
        
    _log.info(f"Texts: {len(converted_doc.texts)}")
    _log.info(f"Groups: {len(converted_doc.groups)}")
    _log.info(f"Document hash: {converted_doc.origin.binary_hash}") 
    
    # for err in conv_results.errors:
    #     _log.info(f"Error {err}")
    
    if escape_Flag is True:
        output_content = html.unescape(converted_doc.export_to_markdown(image_placeholder="",strict_text=False))
    else:
        output_content = converted_doc.export_to_markdown(image_placeholder="",strict_text=False)
        
    f = open(Path(converted_doc.origin.filename).stem+".md", "a")
    f.write(output_content)
    f.close()
    
if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig( level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", help = "Input PDF",type=str)
    parser.add_argument("--ue",  help = "Unescape markdown",action='store_true')
    args = parser.parse_args()
    print(args)
    local_processing(args.input_pdf,args.ue)
    # asyncio.run(remote_processing(args.input_pdf,args.ue))
    