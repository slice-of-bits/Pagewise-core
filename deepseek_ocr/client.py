"""
Ollama client for DeepSeek OCR.
"""
import os
import ollama


def run_ollama_ocr(
    image_path: str,
    prompt: str = "<|grounding|>Convert the document to markdown.",
    model: str = "deepseek-ocr",
    host: str = None
) -> str:
    """
    Run Ollama deepseek-ocr model on an image.
    
    Args:
        image_path: Path to the image file
        prompt: The prompt to send to the model
        model: The model name to use (default: deepseek-ocr)
        host: Ollama host URL (if None, uses OLLAMA_HOST env var or default)
        
    Returns:
        The model's response as a string
    """
    # Get host from parameter, environment variable, or use default
    if host is None:
        host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
    
    # Create client with custom host
    client = ollama.Client(host=host)
    
    # Use the ollama client to run the model
    response = client.chat(
        model=model,
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [image_path]
        }]
    )
    
    return response['message']['content']
