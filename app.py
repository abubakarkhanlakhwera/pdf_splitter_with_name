import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
import os
import zipfile
import shutil
import pdfplumber
import re

# Extract information from a specific page of the PDF using pdfplumber
def extract_pdf_info(page):
    text = page.extract_text()
    
    # Use regex to extract Name and Mobile#
    # Capture prefix like "DR.", "CH.", etc. and name
    name_pattern = r"Name:\s*(\w+\.?\s*)?([A-Za-z\s]+)"  # Capture optional title (DR., CH., etc.)
    mobile_pattern = r"Mobile#:\s*(\d{10})"
    
    name = None
    mobile = None

    # Search for Name and Mobile# on the page
    name_match = re.search(name_pattern, text)
    mobile_match = re.search(mobile_pattern, text)

    if name_match:
        title = name_match.group(1) if name_match.group(1) else ""
        name = f"{title}{name_match.group(2)}".strip()  # Combine title and name

        # Remove unwanted spaces or extra punctuation after title, e.g., "DR." -> "DR"
        if title:
            title = title.strip(".").upper()  # Clean up the title
            name = name.replace(title, f"{title}_")  # Format as "DR_" or "CH_"
    else:
        name = "Unknown_Name"  # Default value if not found

    if mobile_match:
        mobile = mobile_match.group(1).strip()
    else:
        mobile = "Unknown_Mobile"  # Default value if not found

    return name, mobile

# Streamlit app
def main():
    st.title("PDF Page Splitter with Dynamic Prefixes for Each Page")

    # Upload PDF file
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        # Reading the uploaded PDF file
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)

        # Show number of pages
        st.write(f"Total pages: {total_pages}")

        # Create a directory for the uploaded PDF file
        pdf_name = uploaded_file.name.replace('.pdf', '')
        dir_name = f"split_pdfs/{pdf_name}"

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        # Split each page into separate PDF with dynamic prefixes
        for page_number in range(total_pages):
            writer = PdfWriter()
            page = reader.pages[page_number]
            writer.add_page(page)

            # Extract Name and Mobile# from the current page
            with pdfplumber.open(uploaded_file) as pdf:
                current_page = pdf.pages[page_number]
                name, mobile = extract_pdf_info(current_page)

            # Create a new filename using extracted Name and Mobile
            output_filename = os.path.join(dir_name, f"{name}_Mobile_{mobile}_Page_{page_number + 1}.pdf")

            with open(output_filename, "wb") as output_file:
                writer.write(output_file)

        # Create a zip file containing all the split PDFs
        zip_filename = f"{dir_name}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dir_name):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), dir_name))

        # Provide a single download button for the zip file
        with open(zip_filename, "rb") as zip_file:
            st.download_button(
                label="Download All Pages as ZIP",
                data=zip_file,
                file_name=zip_filename,
                mime="application/zip"
            )

        # Clean up by removing the directory and zip file after download
        shutil.rmtree(dir_name)
        os.remove(zip_filename)

if __name__ == "__main__":
    main()
