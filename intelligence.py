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

    def transcribe_image(self, image_path: str) -> str:
        """
        Sends the image to Gemini API and returns the LaTeX content.
        """
        try:
            # Upload the file using the new SDK's file API or pass directly.
            # For simplicity and reliability with the new SDK, let's use the file upload if it persists,
            # or simpler: pass the file path or bytes if permitted.
            # The google-genai SDK 0.x/1.x supports uploading.
             
            # Method 1: UploadFile (Good for large context or reuse, though we use it once here)
            file_ref = self.client.files.upload(file=image_path)
            
            # Method 2: PIL Image (Simpler for single calls, but let's stick to file ref as it effectively handles formats)
            # image = PIL.Image.open(image_path)

            prompt = """
            You are an expert academic typesetter and AI assistant. 
            Your task is to transcribe the handwritten notes in this image into high-quality LaTeX code.

            Rules:
            1. **Content Accuracy**: Transcribe the text exactly as written, preserving the original meaning. Do not summarize or alter the content.
            2. **Math Formatting**: Convert all mathematical expressions into valid LaTeX. 
               - Use standard notation for fractions, superscripts, subscripts, integrals, etc.
               - Ensure equations are properly delimited (inline $...$ or display $$...$$ or \\begin{aling}...\\end{aling} or \\begin{equation}...\\end{equation}).
            3. **Figures & Diagrams**: 
               - DO NOT attempt to create ASCII art. 
               - If you detect a diagram, plot, or figure, insert a placeholder using the following format:
                 \\begin{figure}[h!]
                 \\centering
                 %% INSERT IMAGE HERE
                 \\caption{A descriptive caption based on the context of the diagram found in the image.}
                 \\label{fig:description}
                 \\end{figure}
            4. **Semantic Structure**: Use appropriate LaTeX environments.
               - If you see a theorem, lemma, or proof, use \\begin{theorem}, \\begin{lemma}, \\begin{proof}, etc.
               - Use section commands (\\section, \\subsection) if there are clear headings.
            5. **Output**: Return ONLY the LaTeX body code. Do not include the document preamble (\\documentclass, \\begin{document}, etc.).
            """

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[file_ref, prompt]
            )
            
            text = response.text
            
            # Clean up the response (remove potential markdown code blocks)
            if text.startswith("```latex"):
                text = text.replace("```latex", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")
            
            return text.strip()

        except Exception as e:
            print(f"API Error processing {image_path}: {e}")
            return f"% Error processing image: {os.path.basename(image_path)}\n% Error details: {str(e)}"
