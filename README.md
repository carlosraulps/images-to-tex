# OCR-to-LaTeX Converter

A modular Python application that transforms handwritten notes (PDFs or Images) into editable, semantic LaTeX code using the **Google Gemini 2.0** API.

## Features

- **Automated Workflow**: Splits PDFs, processes images, and generates LaTeX automatically.
- **Smart Vision**: Enhances images (denoising, deskewing) with OpenCV before processing.
- **Incremental Processing**: Skips already processed images to save time and API tokens.
- **Semantic Understanding**: Uses Gemini 2.0 to interpret equations, theorems, and proofs correctly.
- **Figure Handling**: Detected diagrams are captioned and placed in proper `figure` environments (no ASCII art).

## Installation

### Prerequisites

- Python 3.9+
- [Poppler](https://github.com/check-repos/poppler) (Required for PDF processing)
  - macOS: `brew install poppler`
  - Linux: `sudo apt-get install poppler-utils`

### Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd img-to-tex
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key**:
    Get your API key from [Google AI Studio](https://aistudio.google.com/).
    
    Create a `.env` file in the root directory:
    ```bash
    GOOGLE_API_KEY=your_api_key_here
    ```

## Usage

Run the `app.py` script pointing to your source directory:

```bash
python3 app.py /path/to/your/notes/folder
```

### Folder Structure & Naming
- The script looks for **PDFs** (which it splits automatically) or **Images**.
- Images are grouped by title using the pattern: `TitleNameXImageNumber.png`.
  - Example: `Calculus_Ch1XImage1.png`, `Calculus_Ch1XImage2.png`.

### Output
- A `.tex` file is generated for each title (e.g., `Calculus_Ch1.tex`).
- A `processed_log.json` file is created to track progress.

## Architecture

- `vision.py`: Image pre-processing and PDF handling.
- `intelligence.py`: Interface with Google Gen AI SDK (Gemini 2.0).
- `memory.py`: State management for incremental builds.
- `latex.py`: LaTeX generation and package management.
- `app.py`: Main entry point.

## License

[MIT](LICENSE)
