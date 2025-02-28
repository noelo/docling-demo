import html
import logging
import argparse
from pathlib import Path
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)

_log = logging.getLogger(__name__)

def main(input_file:str,escape_Flag:bool):
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
    _log.info(f"Page Count:{len(conv_results.pages)}")
    
    _log.info(f"Images count:{len(conv_results.document.pictures)}") 
    for p in conv_results.document.pictures:
        _log.info(f'    Image present on page {p.prov[0].page_no}') 
        
    _log.info(f"Table Count: {len(conv_results.document.tables)}")
    for t in conv_results.document.tables:
        _log.info(f'    Page:{t.prov[0].page_no} Cell count:{len(t.data.table_cells)} Dimensions:{t.data.num_rows} x {t.data.num_cols}') 
        
    _log.info(f"Texts: {len(conv_results.document.texts)}")
    _log.info(f"Groups: {len(conv_results.document.groups)}")
    _log.info(f"Document hash: {conv_results.input.document_hash}") 
    
    for err in conv_results.errors:
        _log.info(f"Error {err}")
    
    if escape_Flag is True:
        output = html.unescape(conv_results.document.export_to_markdown(image_placeholder="",strict_text=False))
    else:
        output = conv_results.document.export_to_markdown(image_placeholder="",strict_text=False)
        
    f = open(Path(input_file).stem+".md", "a")
    f.write(output)
    f.close()
        
    print(output) 
    
if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", help = "Input PDF",type=str)
    parser.add_argument("--ue",  help = "Unescape markdown",action='store_true')
    args = parser.parse_args()
    print(args)
    main(args.input_pdf,args.ue)