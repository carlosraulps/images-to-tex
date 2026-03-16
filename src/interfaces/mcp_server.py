import os
from mcp.server.fastmcp import FastMCP

from src.tools.process_document import smart_process_document
from src.tools.check_batch_status import check_batch_job
from src.models.tool_schemas import ConvertImageInput # Re-using standard logic, though we use ProcessDocumentInput
from src.tools.process_document import ProcessDocumentInput
from src.tools.check_batch_status import CheckBatchStatusInput

# Initialize FastMCP Server
mcp = FastMCP("images-to-tex")

@mcp.tool()
def process_document(document_path: str, mode: str = "latex", threshold_pages: int = 50) -> str:
    """
    Converts a PDF or image of handwritten notes/equations into LaTeX or Markdown code.
    Automatically handles large volumes via Context Caching or Async Batch Jobs.

    Args:
        document_path: The absolute file path to the PDF or image folder to convert.
        mode: The desired output format ('latex', 'markdown', or 'both'). Defaults to 'latex'.
        threshold_pages: Page count to trigger background processing. Defaults to 50.
    """
    try:
        input_data = ProcessDocumentInput(
            document_path=document_path, 
            mode=mode,
            threshold_pages=threshold_pages
        )
        return smart_process_document(input_data)
        
    except ValueError as val_err:
        import json
        return json.dumps({
            "error": "InputValidationError",
            "details": str(val_err)
        })

@mcp.tool()
def check_document_status(job_id: str) -> str:
    """
    Use this if `process_document` returned a status of 'processing_background'.
    
    Args:
        job_id: The job ID returned by the server.
    """
    try:
        input_data = CheckBatchStatusInput(job_id=job_id)
        return check_batch_job(input_data)
        
    except ValueError as val_err:
        import json
        return json.dumps({
            "error": "InputValidationError",
            "details": str(val_err)
        })

if __name__ == "__main__":
    mcp.run(transport='stdio')
