import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import PIL.Image

# Load environment variables
load_dotenv()

class Intelligence:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set it in environment variables or .env file.")
        
        self.client = genai.Client(api_key=self.api_key)
        # Using Gemini 2.0 Flash as recommended for new SDK, or fallback to 1.5 if 2.0 not available to user yet.
        # User requested "newest models (like Gemini 2.0)".
        self.model_name = 'gemini-3-pro-preview'

    def transcribe_image(self, image_path: str) -> dict:
        """
        Sends the image to Gemini API and returns a dictionary with 'latex' and 'markdown' representations.
        """
        import json
        try:
            # Upload the file using the new SDK's file API or pass directly.
            file_ref = self.client.files.upload(file=image_path)
            
            prompt = """
            You are an expert academic typesetter and AI assistant. 
            Your task is to transcribe the handwritten notes in this image into both high-quality LaTeX code AND a standard Markdown document.
            Return a JSON object with two keys: "latex" and "markdown".

            Rules for LaTeX:
            1. **Content Accuracy**: Transcribe the text exactly as written, preserving the original meaning. Do not summarize or alter the content.
            2. **Math Formatting**: Convert all mathematical expressions into valid LaTeX expressions. 
               - Use standard notation for fractions, superscripts, subscripts, integrals, etc.
               - Ensure equations are properly delimited (inline $...$ or display $$...$$ or \\begin{align}...\\end{align} or \\begin{equation}...\\end{equation}).
            3. **Figures & Diagrams**: 
               - DO NOT attempt to create ASCII art. 
               - If you detect a diagram, plot, or figure, insert a placeholder:
                -  with explictly written detailed descriptive caption based on the context of the diagram found in the image.
                 \\begin{figure}[h!]
                 \\centering
                 %% INSERT IMAGE HERE
                 \\caption{A descriptive caption based on the context of the diagram found in the image.}
                 \\label{fig:description}
                 \\end{figure}
            4. **Semantic Structure**: Use appropriate LaTeX environments (\\begin{theorem}, \\begin{lemma}, etc.), and section commands.
            5. **Output**: Return ONLY the LaTeX body code in the "latex" value. Do not include preamble (\\documentclass, \\begin{document}, etc.).

            Rules for Markdown:
            1. Transcribe the text into standard Markdown format (use # for headings, **bold**, *italics*, etc.).
            2. Preserve mathematical formulas using standard $ (inline) and $$ (display) delimiters so MathJax can render them.
            3. For figures and diagrams, insert a placeholder like `![A explicitly written detailed descriptive caption based on the context of the diagram found in the image.](image_placeholder.png)`.
            """

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[file_ref, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            text = response.text
            
            # Since we forced application/json, it should be valid JSON
            try:
                result_dict = json.loads(text)
                return result_dict
            except json.JSONDecodeError:
                print(f"Failed to parse JSON for {image_path}: {text}")
                return {"latex": "% Error parsing JSON", "markdown": "Error parsing JSON"}

        except Exception as e:
            print(f"API Error processing {image_path}: {e}")
            error_msg = f"% Error processing image: {os.path.basename(image_path)}\n% Error details: {str(e)}"
            return {"latex": error_msg, "markdown": error_msg}
