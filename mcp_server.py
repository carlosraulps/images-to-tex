import os
from mcp.server.fastmcp import FastMCP

import vision
import intelligence

# Initialize FastMCP Server
mcp = FastMCP("images-to-tex")

@mcp.tool()
def convert_image_to_latex(image_path: str, mode: str = "latex") -> str:
    """
    Converts an image of handwritten notes or equations into LaTeX or Markdown code.
    
    Args:
        image_path: The absolute file path to the image to convert.
        mode: The desired output format ('latex', 'markdown', or 'both'). Defaults to 'latex'.
    """
    if not os.path.exists(image_path):
        return f"Error: File not found: {image_path}"
        
    valid_modes = ["latex", "markdown", "both"]
    if mode not in valid_modes:
        return f"Error: Invalid mode '{mode}'. Must be one of {valid_modes}"

    try:
        # Enhance image for better OCR
        enhanced_path = vision.enhance_image(image_path)
        
        # Transcribe using Gemini API
        intel = intelligence.Intelligence()
        content = intel.transcribe_image(enhanced_path, mode=mode)

        # Cleanup enhanced temp file
        if enhanced_path != image_path and "_enhanced" in enhanced_path:
            try:
                os.remove(enhanced_path)
            except Exception:
                pass

        # Format output
        if isinstance(content, dict):
            if mode == "latex":
                return content.get("latex", "Error: No LaTeX output generated.")
            elif mode == "markdown":
                return content.get("markdown", "Error: No Markdown output generated.")
            else:
                latex_out = content.get("latex", "")
                md_out = content.get("markdown", "")
                return f"LaTeX:\n{latex_out}\n\nMarkdown:\n{md_out}"
        else:
            return str(content)

    except Exception as e:
        return f"Error processing image: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
