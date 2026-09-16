"""Generate Semester 3 Python for Data Analytics sample question paper (PDF and TXT)."""

import os
from pathlib import Path
import fitz  # PyMuPDF

SAMPLE_DIR = Path(__file__).resolve().parent

SAMPLE_TEXT = """COLLEGE OF ENGINEERING & TECHNOLOGY
DEPARTMENT OF INFORMATION TECHNOLOGY
SEMESTER III EXAMINATION — PYTHON FOR DATA ANALYTICS
Max Marks: 70
Duration: 3 Hours

Instructions:
1. Answer all questions.
2. Figures to the right indicate full marks.
3. Assume suitable data wherever necessary.

Q1. (a) Define NumPy ndarray. Explain array indexing, slicing, and broadcasting with code examples. [5 Marks]
Q1. (b) Explain Pandas Series and DataFrame structures. How do they differ in indexing and dimensions? [5 Marks]
Q1. (c) Write a Python program to create a 3x3 identity matrix and calculate its determinant and inverse using NumPy. [5 Marks]

Q2. (a) Write a Python script to load a real-world CSV dataset using Pandas, identify missing values, and handle them using forward fill and mean imputation. [10 Marks]
Q2. (b) Explain data grouping and aggregation using groupby() and pivot_table() functions in Pandas with examples. [5 Marks]

Q3. (a) Design an end-to-end data visualization pipeline using Matplotlib and Seaborn to plot histograms, boxplots, and a correlation heatmap for feature analysis. [10 Marks]
Q3. (b) Differentiate between Exploratory Data Analysis (EDA) and Confirmatory Data Analysis with practical examples. [5 Marks]

Q4. (a) Explain feature scaling and normalization techniques: Min-Max Scaling and Z-Score Standardization using Python scikit-learn. [10 Marks]
Q4. (b) Write Python code to clean irregular string columns and parse ISO datetime strings in a time-series dataset. [5 Marks]

Q5. (a) Explain statistical outlier detection techniques using Interquartile Range (IQR) and Z-score thresholding in Python. [10 Marks]
Q5. (b) Write a Python script to calculate Pearson and Spearman rank correlation coefficients between two numerical variables. [5 Marks]
"""

def generate_samples():
    txt_path = SAMPLE_DIR / "sem3_python_data_analytics.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT.strip() + "\n")
    print(f"Generated TXT sample: {txt_path}")

    pdf_path = SAMPLE_DIR / "sem3_python_data_analytics.pdf"
    doc = fitz.open()
    page = doc.new_page()

    # Draw title and content
    rect = fitz.Rect(50, 50, 550, 800)
    page.insert_textbox(
        rect,
        SAMPLE_TEXT.strip(),
        fontsize=10,
        fontname="helv",
        align=fitz.TEXT_ALIGN_LEFT
    )

    doc.save(str(pdf_path))
    doc.close()
    print(f"Generated PDF sample: {pdf_path}")

if __name__ == "__main__":
    generate_samples()
