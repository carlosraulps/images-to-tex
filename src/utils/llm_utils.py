import json
import re
from google.genai import types
from pydantic import BaseModel
from typing import Optional, Type, Dict, Any

def sanitize_json_string(raw_str: str) -> str:
    """
    Cleans the raw LLM output before parsing to remove common hallucinated artifacts
    that break JSON decoders (e.g., Markdown blocks, pagination markers, conversational text).
    """
    # 1. Remove Markdown code block wrappers
    raw_str = re.sub(r'^```(?:json)?\s*', '', raw_str, flags=re.MULTILINE)
    raw_str = re.sub(r'^```\s*', '', raw_str, flags=re.MULTILINE)
    
    # 2. Remove annoying pagination markers often injected by the model (e.g., % --- Page X ---)
    raw_str = re.sub(r'%\s*---\s*Page\s*\d+\s*---\s*', '', raw_str, flags=re.IGNORECASE)
    
    # 3. Strip any weird leading/trailing whitespace or text outside the main JSON braces
    start_idx = raw_str.find('{')
    end_idx = raw_str.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        raw_str = raw_str[start_idx : end_idx + 1]
    
    return raw_str.strip()

def generate_pydantic_with_retry(
        client, 
        model_name: str, 
        contents: list, 
        base_prompt: str, 
        response_schema: Type[BaseModel],
        max_retries: int = 3
    ) -> Dict[str, Any]:
    """
    Wraps the Gemini generation call, enforcing a Pydantic response schema.
    Attempts to parse the JSON output into the defined Pydantic model. 
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
                    response_schema=response_schema
                )
            )
            
            raw_text = response.text
            sanitized_text = sanitize_json_string(raw_text)
            
            # Attempt to parse into the required model automatically validates it
            parsed_data = response_schema.model_validate_json(sanitized_text)
            return parsed_data.model_dump()
            
        except Exception as e:
            print(f"[Warning] Parsing/Validation Error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                # Construct the feedback loop prompt
                error_feedback = f"""
Context: You are tasked with converting the provided image into strict JSON according to the schema. However, a previous attempt to process this exact image resulted in a critical application failure.

Historical Error Report:

Previous Failed Output:
{locals().get('raw_text', 'No output generated')}

System Error Caused:
Error: {str(e)}

Task:
1. Analyze the 'Historical Error Report' to understand exactly why the system crashed last time.
2. Re-evaluate the attached image.
3. Generate a new, fully corrected output that strictly adheres to the requested JSON Schema and avoids previous formatting mistakes.

Strict Constraints: You must output ONLY valid, raw JSON. Do not include apologies, explanations of your fix, or markdown formatting.
"""
                current_contents = [c for c in contents if not isinstance(c, str)]
                current_contents.append(base_prompt + "\n\n" + error_feedback)
            else:
                print(f"[Error] Max retries ({max_retries}) reached. Returning error payload.")
                # Fallback to a synthetic empty dict structure if nothing works
                return {}
            
    return {}
