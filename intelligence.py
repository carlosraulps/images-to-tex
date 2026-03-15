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
        self.model_name = 'gemini-3.1-pro-preview'

    def transcribe_image(self, image_path: str, mode: str = "both") -> dict:
        """
        Sends the image to Gemini API and returns a dictionary with 'latex' and/or 'markdown' representations.
        """
        import llm_utils

        try:
            # Upload the file using the new SDK's file API or pass directly.
            file_ref = self.client.files.upload(file=image_path)
            
            if mode == "latex":
                prompt = r"""
                You are an expert academic typesetter and AI assistant. 
                Your task is to transcribe the handwritten notes well structure with all the page complete content also trascribed in this image into high-quality LaTeX code.
                Return a JSON object with one key: "latex".

                Rules for LaTeX:
                1. **Content Accuracy**: Transcribe all the content of the page, all the text exactly as written, preserving the original meaning. Do not summarize or alter the content.
                2. **Math Formatting**: Convert all mathematical expressions into valid LaTeX expressions. 
                   - Use standard notation for fractions, superscripts, subscripts, integrals, etc.
                   - Ensure equations are properly delimited (inline $...$ or display \[...\] or \\begin{align}...\\end{align} or \\begin{equation}...\\end{equation}).
                3. **Figures & Diagrams**: 
                   - DO NOT attempt to create ASCII art. 
                   - If you detect a diagram, plot, or figure, insert a placeholder:
                     - with explictly written detailed descriptive caption based on the context of the diagram found in the image its relation and a explic description of the image itself.
                     \\begin{figure}[h!]
                     \\centering
                     %% INSERT IMAGE HERE
                     \\caption{A descriptive caption based on the context of the diagram found in the image its relation and a explic description of the image itself.}
                     \\label{fig:description}
                     \\end{figure}
                4. **Semantic Structure**: Use appropriate LaTeX environments (\\begin{theorem}, \\begin{lemma}, etc.), and section commands.
                5. **Output**: Return ONLY the LaTeX body code in the "latex" value. Do not include preamble (\\documentclass, \\begin{document}, etc.).

                STRICT JSON CONSTRAINTS - CRITICAL:
                - You MUST output ONLY valid, raw, unformatted JSON.
                - DO NOT output any conversational text before or after the JSON.
                - DO NOT wrap the output in markdown code blocks (e.g., no ```json).
                - DO NOT inject pagination markers like "% --- Page 7 ---" or comment lines inside or outside the JSON.
                - The entire response must be parsable by `json.loads()`.
                """
            elif mode == "markdown":
                prompt = r"""
                You are an expert academic typesetter and AI assistant. 
                Your task is to transcribe the handwritten notes well structure with all the page complete content also trascribed in this image into a standard Markdown document.
                Return a JSON object with one key: "markdown".

                Rules for Markdown:
                1. Transcribe the content into standard Markdown format (use # for headings, **bold**, *italics*, equations, \[ \], $ $, etc. ).
                2. Preserve mathematical formulas using standard $ (inline) and $$ (display) delimiters so MathJax can render them.
                3. For figures and diagrams, insert a placeholder like `![A explicitly written detailed descriptive caption based on the context of the diagram found in the image.](image_placeholder.png)with explictly written detailed descriptive caption based on the context of the diagram found in the image its relation and a explic description of the image itself..

                STRICT JSON CONSTRAINTS - CRITICAL:
                - You MUST output ONLY valid, raw, unformatted JSON.
                - DO NOT output any conversational text before or after the JSON.
                - DO NOT wrap the output in markdown code blocks (e.g., no ```json).
                - DO NOT inject pagination markers like "% --- Page 7 ---" or comment lines inside or outside the JSON.
                - The entire response must be parsable by `json.loads()`.
                """
            else:
                prompt = """
                You are an expert academic typesetter and AI assistant. 
                Your task is to transcribe the handwritten notes well structure with all the page complete content also trascribed in this image into both high-quality LaTeX code AND a standard Markdown document.
                Return a JSON object with two keys: "latex" and "markdown".

                Rules for LaTeX:
                1. **Content Accuracy**: Transcribe all the content of the page, all the text exactly as written, preserving the original meaning. Do not summarize or alter the content.
                2. **Math Formatting**: Convert all mathematical expressions into valid LaTeX expressions. 
                   - Use standard notation for fractions, superscripts, subscripts, integrals, etc.
                   - Ensure equations are properly delimited (inline $...$ or display $$...$$ or \\begin{align}...\\end{align} or \\begin{equation}...\\end{equation}).
                3. **Figures & Diagrams**: 
                   - DO NOT attempt to create ASCII art. 
                   - If you detect a diagram, plot, or figure, insert a placeholder:
                     - with explictly written detailed descriptive caption based on the context of the diagram found in the image.
                     \\begin{figure}[h!]
                     \\centering
                     %% INSERT IMAGE HERE
                     \\caption{A descriptive caption based on the context of the diagram found in the image.}
                     \\label{fig:description}
                     \\end{figure}
                4. **Semantic Structure**: Use appropriate LaTeX environments (\\begin{theorem}, \\begin{lemma}, etc.), and section commands.
                5. **Output**: Return ONLY the LaTeX body code in the "latex" value. Do not include preamble (\\documentclass, \\begin{document}, etc.).

                Rules for Markdown:
                1. Transcribe the content into standard Markdown format (use # for headings, **bold**, *italics*, etc.).
                2. Preserve mathematical formulas using standard $ (inline) and $$ (display) delimiters so MathJax can render them.
                3. For figures and diagrams, insert a placeholder like `![A explicitly written detailed descriptive caption based on the context of the diagram found in the image.](image_placeholder.png)`.

                STRICT JSON CONSTRAINTS - CRITICAL:
                - You MUST output ONLY valid, raw, unformatted JSON.
                - DO NOT output any conversational text before or after the JSON.
                - DO NOT wrap the output in markdown code blocks (e.g., no ```json).
                - DO NOT inject pagination markers like "% --- Page 7 ---" or comment lines inside or outside the JSON.
                - The entire response must be parsable by `json.loads()`.
                """

            contents = [file_ref, prompt]
            
            # Delegate parsing and retry logic to llm_utils
            result_dict = llm_utils.generate_json_with_retry(
                client=self.client,
                model_name=self.model_name,
                contents=contents,
                base_prompt=prompt,
                max_retries=3
            )
            return result_dict

        except Exception as e:
            print(f"API Error processing {image_path}: {e}")
            error_msg = f"% Error processing image: {os.path.basename(image_path)}\n% Error details: {str(e)}"
            return {"latex": error_msg, "markdown": error_msg}
