# 📚 AI Book Creator

AI Book Creator is a web application that allows you to generate complete books, from outline to final manuscript, using the power of Google's Gemini AI. You can define a theme, and the application will guide you through the process of creating a detailed plan, writing chapters, and generating final documents in DOCX and PDF formats.

## ✨ Features

-   **Interactive Web UI:** A user-friendly interface built with Gradio.
-   **Step-by-Step Book Creation:** Guides you through planning, chapter generation, and finalization.
-   **AI-Powered Content Generation:** Uses the Gemini API to generate outlines, summaries, titles, and chapter content.
-   **Customizable:** Allows you to choose the number of chapters, style, and other parameters.
-   **Multiple Output Formats:** Generates final documents in both DOCX and PDF.
-   **Project-Based:** Saves your progress automatically, allowing you to continue your work later.

## 🚀 Getting Started

Follow these instructions to set up and run the application in your local environment.

### Prerequisites

-   Python 3.7+
-   A Google Gemini API Key. You can get one from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 1. Clone the Repository

```bash
git clone <repository_url>
cd <repository_directory>
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

Install the required Python libraries using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Configure the API Key

You need to set your Gemini API key as an environment variable.

**On macOS/Linux:**
```bash
export GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

**On Windows (Command Prompt):**
```bash
set GEMINI_API_KEY="YOUR_API_KEY_HERE"
```
**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

Replace `"YOUR_API_KEY_HERE"` with your actual Gemini API key.

### 5. Run the Application

Once the dependencies are installed and the API key is configured, you can run the application:

```bash
python app.py
```

This will start the Gradio web server. You will see a local URL in your terminal (usually `http://127.0.0.1:7860`). Open this URL in your web browser to use the application.

## Usage

1.  **Enter a Theme:** Start by entering the central theme or idea for your book in the "Etapa 1: Planejamento Inicial" section.
2.  **Start Planning:** Click the "Iniciar Planejamento" button. The AI will generate a suggested outline and a detailed summary.
3.  **Finalize the Plan:** Review the generated content. Choose a title from the suggestions (or write your own), and set the number of chapters and other options. Click "Finalizar Planejamento e Salvar".
4.  **Generate Chapters:** In "Etapa 2", click "Gerar Todos os Capítulos". The application will create each chapter sequentially, saving the progress as it goes. This may take a long time.
5.  **Finalize and Download:** Once the chapters are created, go to "Etapa 3" and click "Revisar Livro e Gerar Arquivos". The AI will perform a final review of the entire manuscript. After the review, download links for the DOCX and PDF files will appear.

---
*This application was developed and refactored by Jules, an AI Software Engineer.*
