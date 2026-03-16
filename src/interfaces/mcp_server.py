import os
from mcp.server.fastmcp import FastMCP

from src.tools.convert_image import convert_image_to_latex_markdown
from src.models.tool_schemas import ConvertImageInput

# Initialize FastMCP Server
mcp = FastMCP("images-to-tex")

@mcp.tool()
def convert_image_to_latex(image_path: str, mode: str = "latex") -> str:
    """
    Converts an image of handwritten notes or equations into LaTeX or Markdown code.
    This tool extracts the base printed text and categorizes human annotations.
    
    Args:
        image_path: The absolute file path to the image to convert.
        mode: The desired output format ('latex', 'markdown', or 'both'). Defaults to 'latex'.
    """
    try:
        # Pydantic validation handles constraint enforcement
        input_data = ConvertImageInput(image_path=image_path, mode=mode)
        # Execution is fully encapsulated in the tools layer
        return convert_image_to_latex_markdown(input_data)
        
    except ValueError as val_err:
        # Pydantic validation failures caught and returned generically to Agent
        import json
        return json.dumps({
            "error": "InputValidationError",
            "details": str(val_err)
        })

if __name__ == "__main__":
    mcp.run(transport='stdio')
