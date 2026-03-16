import os
import json
from src.services import vision
from src.services.intelligence import Intelligence
from src.models.tool_schemas import ConvertImageInput

def convert_image_to_latex_markdown(input_data: ConvertImageInput) -> str:
    """
    Core tool implementation encapsulated specifically for the Agent.
    Strictly accepts a validated Pydantic model (`ConvertImageInput`)
    and strictly returns a JSON string, ensuring robust error handling
    and never crashing the Agent.
    """
    try:
        image_path = input_data.image_path
        mode = input_data.mode

        if not os.path.exists(image_path):
            return json.dumps({
                "error": "FileNotAccessible",
                "details": f"The file at path '{image_path}' does not exist or is not readable."
            })
            
        # Enhance image for better OCR
        enhanced_path = vision.enhance_image(image_path)
        
        # Determine transcribing instance
        try:
            intel = Intelligence()
        except ValueError as api_err:
             return json.dumps({
                "error": "ConfigurationError",
                "details": str(api_err)
             })

        # Transcribe using Gemini API
        content = intel.transcribe_image(enhanced_path, mode=mode)

        # Cleanup enhanced temp file
        if enhanced_path != image_path and "_enhanced" in enhanced_path:
            try:
                os.remove(enhanced_path)
            except Exception:
                pass

        # Format output
        if isinstance(content, dict):
            # Includes base_latex_md and annotations_metadata
            return json.dumps(content, indent=2)
        else:
            # Fallback if content was just a string
            return json.dumps({"raw_content": str(content)})

    except Exception as e:
        # Prevent the tool from crashing the Agent's runtime.
        # Send a formatted error payload to prompt the Agent to self-correct.
        return json.dumps({
            "error": "ToolExecutionException",
            "details": str(e)
        })
