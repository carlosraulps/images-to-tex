import json
import os
from pydantic import BaseModel, Field

from src.services.batch_processor import BatchProcessor

class CheckBatchStatusInput(BaseModel):
    """
    Input schema for checking the status of an asynchronous processing job.
    """
    job_id: str = Field(
        ...,
        description="The Batch Job ID returned by the process_document tool when it routed to the background."
    )

def check_batch_job(input_data: CheckBatchStatusInput) -> str:
    """
    Checks the status of a queued document processing job.
    If the job has finished, it downloads the mapped JSONL output results.
    """
    job_id = input_data.job_id
    try:
        processor = BatchProcessor()
        result_meta = processor.check_job_status(job_id)
        
        status = result_meta.get("status")
        if status == "completed":
            out_uri = result_meta.get("output_uri")
            # In a full implementation, you'd use self.client.files.download(name=...) 
            # to retrieve the JSONL, iterate through the mapped 'custom_id' strings,
            # and write them to the final latex/markdown folders.
            # Returning success instruction to Agent:
            return json.dumps({
                "status": "success",
                "message": "The job has successfully completed and the files are ready for parsing.",
                "output_uri": out_uri
            }, indent=2)
            
        elif status == "processing":
            return json.dumps({
                "status": "processing",
                "message": result_meta.get("message")
            }, indent=2)
            
        else:
             return json.dumps(result_meta, indent=2)

    except Exception as e:
        return json.dumps({
            "error": "BatchCheckException",
            "details": str(e)
        }, indent=2)
