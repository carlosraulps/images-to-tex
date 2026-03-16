from pydantic import BaseModel, Field
from typing import Literal

class ConvertImageInput(BaseModel):
    """
    Input schema for the image-to-tex conversion tool.
    Constrains the inputs the agent can provide, strictly defining expected format.
    """
    image_path: str = Field(
        ...,
        description="The absolute file path to the image of handwritten notes or equations intended for conversion."
    )
    mode: Literal["latex", "markdown", "both"] = Field(
        default="both",
        description="The desired textual output format. Valid options: 'latex', 'markdown', or 'both'."
    )
