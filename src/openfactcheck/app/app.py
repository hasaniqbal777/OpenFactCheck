import gradio as gr

def greet(name):
    """
    Returns a greeting to the user provided name.

    Parameters:
    name (str): The name of the person to greet.

    Returns:
    str: A greeting string.
    """
    return f"Hello, {name}! Welcome to Gradio."

js_func = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.href = url.href;
    }
}
"""

with gr.Blocks(js=js_func) as demo:
    gr.Interface(
    fn=greet,  # Function to call
    inputs=gr.Textbox(placeholder="Enter your name here...", label="Name"),  # Input component
    outputs="text",  # Output component type
    title="Hello World App",  # Title of the app
    description="A simple Gradio app that greets you."  # Description of the app
    )

# Run the interface
if __name__ == "__main__":
    demo.launch()