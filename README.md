# 📄 AnySummariser

**AnySummariser** is a powerful and user-friendly Streamlit app designed to generate concise summaries from multiple types of inputs including plain text, web pages, audio, images, and PDFs. It leverages advanced LLMs and chunking strategies to ensure accurate summarization, regardless of content type.

---

## 🚀 Features

- 📂 **Upload File**: Upload `.txt` files and get instant summaries.
- 📝 **Paste Text**: Enter any custom text and summarize it.
- 🔗 **Webpage Summarization**: Enter a URL and summarize its contents using HTML-to-Markdown conversion.
- 🎙️ **Audio Transcription**: Upload audio files (`.mp3`, `.wav`, `.ogg`, `.m4a`) and get text transcription followed by summarization.
- 📷 **Image Summarization**: Upload an image and get a one-line summary using vision models.
- 📄 **PDF Summarization**: Extract text from uploaded PDFs, convert it to Markdown, and summarize it.

---

## 🧠 How It Works

1. **Input**: Choose from multiple input types (Text, File, Web, Audio, Image, PDF).
2. **Chunking**: Content is chunked using RecursiveCharacterTextSplitter.
3. **Intermediate Summaries**: Each chunk is summarized using an LLM.
4. **Final Summary**: A final summary is generated using the combined intermediate summaries.

---

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **LLMs**: [Groq API](https://console.groq.com/)
  - `llama-3.3-70b-versatile` (Text Summarization)
  - `llama-3.2-11b-vision-preview` (Image Summarization)
  - `distil-whisper-large-v3-en` (Audio Transcription)
- **Text Extraction**: `html2text`, `pdfplumber`, `markdownify`
- **Chunking**: `langchain`'s `RecursiveCharacterTextSplitter`

---

## 📦 Installation

```bash
git clone https://github.com/yashpaddalwar/anysummariser.git
cd AnySummariser
pip install -r requirements.txt
```


## 📝 Notes
 - This app uses recursive chunking by default for general-purpose splitting.
 - Semantic chunking is available (commented out) if embedding support is desired.
 - PDF extraction relies on pdfplumber and may not extract tables or images well.
 - Make sure to handle Groq usage limits and ensure model access in production.



