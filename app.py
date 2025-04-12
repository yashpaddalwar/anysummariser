import streamlit as st
import os
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
from langchain_experimental.text_splitter import SemanticChunker
from groq import Groq
import requests
import html2text
import base64
from PIL import Image
import markdownify
import pdfplumber
import io
import time

st.set_page_config(page_title="AnySummarizer", layout="wide")

# Initialize Groq client
os.environ["GROQ_API_KEY"] = "gsk_...."
client = Groq()

# Function to fetch and convert webpage content to markdown
def convert_webpage_to_markdown(url):
    # Fetch the webpage content
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful

    # Create an html2text object to convert HTML to markdown
    h = html2text.HTML2Text()
    h.ignore_links = False  # Set this to True if you don't want to include hyperlinks

    # Convert the HTML content to markdown
    markdown_content = h.handle(response.text)

    return markdown_content

def convert_audio_to_text(audio_file):
    # Save the uploaded audio file temporarily
    temp_audio_path = "temp_uploaded_audio.m4a"
    with open(temp_audio_path, "wb") as temp_file:
        temp_file.write(audio_file.getbuffer())

    # Perform transcription using the Groq API
    client = Groq()
    try:
        with open(temp_audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(temp_audio_path, file.read()),
                model="distil-whisper-large-v3-en",
                response_format="verbose_json",
            )
            return transcription.text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")
    finally:
        # Clean up temporary audio file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

def pdf_to_markdown(pdf_file):

    markdown_content = ""

    try:
        # Open the PDF file using pdfplumber
        with pdfplumber.open(pdf_file) as pdf:
            for page_number, page in enumerate(pdf.pages):
                # Extract text from each page
                text = page.extract_text()
                if text:
                    markdown_content += f"# Page {page_number + 1}\n\n"
                    markdown_content += text + "\n\n"

        # Convert content to Markdown using markdownify
        markdown_content = markdownify.markdownify(markdown_content, heading_style="ATX")  # Corrected this line

        if not markdown_content.strip():
            raise ValueError("The PDF does not contain any readable text.")

    except Exception as e:
        raise RuntimeError(f"Error processing the PDF: {e}")

    return markdown_content



# LLM Function
def llm(prompt):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1024,
        top_p=1,
        stop=None,
    )
    return completion.choices[0].message.content

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def summarize_image(uploaded_image):
    image = Image.open(uploaded_image)
    base64_image = image_to_base64(image)
    prompt = "Write a summary of the given image in strictly one line."
    image_url = f"data:image/png;base64,{base64_image}"
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    image_summary = completion.choices[0].message.content
    return image_summary

# Load Prompts from Files
def load_prompt(file_name):
    with open(file_name, "r") as file:
        return file.read()

# Process content (shared logic for text input and file upload)
def process_content(content):
    # Initialize session state for summaries
    if "intermediate_summary" not in st.session_state:
        st.session_state.intermediate_summary = ""
    if "final_summary" not in st.session_state:
        st.session_state.final_summary = ""

    if not content.strip():
        st.error("Please enter or upload text to generate a summary.")
        return

    with st.spinner("🔍 Generating summary... Please wait."):
        # Split Documents
        # try:
        #     text_splitter = SemanticChunker(embedder)
        #     docs = text_splitter.split_documents([Document(page_content=content)])
        #     st.success("Used Semantic Chunking!")
        # except:
        #     from langchain.text_splitter import RecursiveCharacterTextSplitter
        #     text_splitter = RecursiveCharacterTextSplitter(
        #         chunk_size=1200,
        #         chunk_overlap=240
        #     )
        #     docs = text_splitter.split_documents([content])
        #     st.success("Used Recursive Chunking!")
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=240
        )
        docs = text_splitter.create_documents([content])
        st.success("Used Recursive Chunking!")

        # Generate Intermediate Summary
        intermediate_summary = ""
        for n, i in enumerate(docs):
            prompt1 = load_prompt("Prompts/prompt1.txt").replace("{text}", i.page_content)
            chunk_summary = llm(prompt1)
            intermediate_summary += f"Text segment {n+1}: {chunk_summary}\n\n"
            time.sleep(1)

        # Save intermediate summary to session state
        st.session_state.intermediate_summary = intermediate_summary

        # Generate Final Summary
        prompt2 = load_prompt("Prompts/prompt2.txt").replace("{intermediate_summary}", intermediate_summary)
        final_summary = llm(prompt2)

        # Save final summary to session state
        st.session_state.final_summary = final_summary

        st.success("✅ Summary Generated Successfully!")

# Streamlit App with Tabs
def main():
    st.title("📄 AnySummarizer!")
    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📂 Upload File", "📝 Paste Text", "🔗 Website URL","🎙️ Audio to Text", "📷 Image Summarization", "📄 PDFs"])

    # Tab 1: Upload File
    with tab1:
        st.subheader("Attach Your Text File")
        uploaded_file = st.file_uploader("Upload a .txt file:", type="txt")
        if uploaded_file is not None:
            file_content = uploaded_file.read().decode("utf-8")
            st.text_area("File Content:", file_content, height=200, disabled=True)
            if st.button("Generate Summary from File", key="generate_summary_file_button"):
                process_content(file_content)

    # Tab 2: Paste Text
    with tab2:
        st.subheader("Paste Text for Summarization")
        content = st.text_area("Enter your text for summarization:", height=200, placeholder="Paste your text here...")
        if st.button("Generate Summary", key="generate_summary_text_button"):
            process_content(content)

    with tab3:
        st.subheader("Paste Web URL")
        url = st.text_input("Enter the URL of the webpage:", placeholder="https://example.com")

        if url.strip():  # Check if the URL is not empty
                try:
                    content = convert_webpage_to_markdown(url)
                    if content.strip():
                        st.text_area("File Content:", content, height=200, disabled=True)
                    else:
                        st.error("Failed to fetch the webpage!")
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to fetch the webpage. Error: {e}")
        else:
            st.error("Please enter a valid URL.")
        
        if st.button("Generate Summary", key="generate_summary_url_button"):
            if content is not None:
                process_content(content)  # Call your summary generation function
            
    with tab4:
        st.subheader("Upload Your Audio File")
        uploaded_audio = st.file_uploader("Upload an audio file:", type=["mp3", "wav", "ogg", "m4a"])

        if uploaded_audio is not None:
            # Display the uploaded audio file
            st.audio(uploaded_audio, format="audio/mp3", start_time=0)
            try:
                transcription_text = convert_audio_to_text(uploaded_audio)
                st.subheader("Transcription Result:")
                st.text_area("Transcription:", transcription_text, height=200, disabled=True)
            except Exception as e:
                st.error(f"Error in transcription: {e}")

        if st.button("Generate Summary", key="generate_summary_audio_button"):
            if uploaded_audio is not None:
                process_content(transcription_text)  # Call your summary generation function
            else:
                st.error("Please Upload the Audio file!")

    with tab5:
        st.subheader("📷 Summarize Images")
        uploaded_image = st.file_uploader("Upload an image:", type=["jpg", "jpeg", "png"], key="image_uploader")
        if uploaded_image is not None:
            # Display the uploaded image
            st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)

            image_summary = summarize_image(uploaded_image)
            st.subheader("Image Summary:")
            st.write(image_summary)

    with tab6:
        st.subheader("Attach Your PDF File")
        uploaded_pdf = st.file_uploader("Upload a PDF file:", type=["pdf"])
        if uploaded_pdf is not None:
            try:
                # Call the pdf_to_markdown function to extract content
                pdf_content = pdf_to_markdown(uploaded_pdf)
                
                if pdf_content.strip():
                    st.text_area("Extracted PDF Content:", pdf_content, height=200, disabled=True)
                    
                    if st.button("Generate Summary from PDF", key="generate_summary_pdf_button"):
                        process_content(pdf_content)  # Call process_content function
                else:
                    st.error("The PDF seems to be empty. Please upload a valid PDF.")
            except Exception as e:
                st.error(f"Error processing the PDF: {e}")

    # Display Final Summary (outside tabs, only once)
    if "final_summary" in st.session_state and st.session_state.final_summary:
        st.subheader("Final Summary:")
        st.write(st.session_state.final_summary)

    # Option to Show Intermediate Summary (outside tabs, only once)
    if st.button("Show Intermediate Summary", key="show_intermediate_summary_button"):
        if "intermediate_summary" in st.session_state and st.session_state.intermediate_summary:
            st.subheader("Intermediate Summary:")
            st.write(st.session_state.intermediate_summary)
        else:
            st.warning("No intermediate summary available.")

# Run the App
if __name__ == "__main__":
    main()