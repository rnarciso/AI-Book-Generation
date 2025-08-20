import gradio as gr
import httpx
import sys

print("--- [DEBUG] Starting ui.py ---", flush=True)

# Configuration
BACKEND_API_URL = "http://localhost:8003/api/generate"
MODELS = [
    "qwen/qwen3-coder:free",
    "z-ai/glm-4.5-air:free",
    "openai/gpt-oss-20b:free",
    "google/gemini-2.0-flash-exp:free",
]

def generate_text(model, prompt):
    """
    Function to be called by the Gradio interface.
    It makes a POST request to the FastAPI backend.
    """
    if not model or not prompt:
        return "Error: Model and prompt are required."

    payload = {
        "model": model,
        "prompt": prompt
    }

    try:
        with httpx.Client() as client:
            response = client.post(BACKEND_API_URL, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            # Extract the content from the response, assuming OpenRouter's structure
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        # Extract detail from the backend's HTTPException response
        error_detail = e.response.json().get("detail", str(e))
        return f"Error from backend: {error_detail}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# Define the Gradio interface
print("--- [DEBUG] Before gr.Blocks() ---", flush=True)
with gr.Blocks(theme=gr.themes.Soft(), title="AI Book Creator") as demo:
    print("--- [DEBUG] Inside gr.Blocks() ---", flush=True)
    gr.Markdown("# 📚 AI Book Creator")
    gr.Markdown("Select a model and enter a prompt to generate text.")

    with gr.Row():
        model_dropdown = gr.Dropdown(
            label="Select Model",
            choices=MODELS,
            value=MODELS[0]
        )

    prompt_textbox = gr.Textbox(
        label="Your Prompt",
        lines=10,
        placeholder="Enter your book idea, chapter outline, or any text prompt here..."
    )

    submit_button = gr.Button("Generate", variant="primary")

    output_textbox = gr.Textbox(
        label="Generated Text",
        lines=20,
        interactive=False
    )

    submit_button.click(
        fn=generate_text,
        inputs=[model_dropdown, prompt_textbox],
        outputs=[output_textbox]
    )

if __name__ == "__main__":
    # To run this, you would run `python backend/ui.py`
    # Make sure the FastAPI backend is running first in a separate terminal.
    print("--- [DEBUG] Before demo.launch() ---", flush=True)
    demo.launch()
    print("--- [DEBUG] After demo.launch() ---", flush=True)
