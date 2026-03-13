import json
import re
from google.genai import types

def sanitize_json_string(raw_str: str) -> str:
    """
    Cleans the raw LLM output before parsing to remove common hallucinated artifacts
    that break JSON decoders (e.g., Markdown blocks, pagination markers, conversational text).
    """
    # 1. Remove Markdown code block wrappers
    raw_str = re.sub(r'^```json\s*', '', raw_str, flags=re.MULTILINE)
    raw_str = re.sub(r'^```\s*', '', raw_str, flags=re.MULTILINE)
    
    # 2. Remove annoying pagination markers often injected by the model (e.g., % --- Page X ---)
    raw_str = re.sub(r'%\s*---\s*Page\s*\d+\s*---\s*', '', raw_str, flags=re.IGNORECASE)
    
    # 3. Strip any weird leading/trailing whitespace or text outside the main JSON braces
    # Find the position of the first '{' and the last '}'
    start_idx = raw_str.find('{')
    end_idx = raw_str.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        raw_str = raw_str[start_idx : end_idx + 1]
    
    return raw_str.strip()

def generate_json_with_retry(client, model_name: str, contents: list, base_prompt: str, max_retries: int = 3) -> dict:
    """
    Wraps the Gemini generation call. Attempts to parse the JSON output. 
    If a JSONDecodeError occurs, it passes the error and the failed output 
    back to the model for self-correction up to `max_retries` times.
    """
    import logging
    
    current_contents = contents.copy()
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=current_contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            raw_text = response.text
            sanitized_text = sanitize_json_string(raw_text)
            
            # Attempt to parse
            data = json.loads(sanitized_text)
            return data
            
        except json.JSONDecodeError as e:
            print(f"[Warning] JSON Parsing Error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                # Construct the feedback loop prompt as per requirements
                error_feedback = f"""
Context: You are tasked with converting the provided image into strict JSON and LaTeX. However, a previous attempt to process this exact image resulted in a critical application failure.

Historical Error Report:

Previous Failed Output:
{raw_text}

System Error Caused:
JSONDecodeError: {str(e)}

Task:
1. Analyze the 'Historical Error Report' to understand exactly why the system crashed last time (e.g., hallucinated markdown, unescaped characters, or injected pagination like '% --- Page 7 ---').
2. Re-evaluate the attached image.
3. Generate a new, fully corrected output that strictly avoids the previous formatting mistakes.

Strict Constraints: You must output ONLY valid, raw JSON. Do not include apologies, explanations of your fix, or markdown formatting. If you repeat the previous error, the system will crash again.
"""
                # Update the prompt in the contents list (assuming prompt is the last string item)
                # Ensure we retain the original image reference but replace the text prompt
                # with our feedback appended to the base instruction.
                current_contents = [c for c in contents if not isinstance(c, str)]
                current_contents.append(base_prompt + "\n\n" + error_feedback)
            else:
                print(f"[Error] Max retries ({max_retries}) reached. Returning error payload.")
                return {
                    "latex": f"% Fatal Error: Could not generate valid JSON after {max_retries} attempts.\n% Details: {str(e)}",
                    "markdown": f"**Fatal Error:** Could not generate valid JSON after {max_retries} attempts.\n\nDetails: {str(e)}"
                }
        except Exception as e:
            # For network or API quota errors, fail immediately or retry based on a different logic. 
            # We're focusing strictly on JSON parse failures here.
            print(f"[Error] API/Network Error formatting request: {e}")
            return {
                "latex": f"% API Error: {str(e)}",
                "markdown": f"**API Error:** {str(e)}"
            }
            
    return {"latex": "% Unknown failure", "markdown": "Unknown failure"}
