from modules.ocr_pdf import ocr_pdf_async
import google.generativeai as genai
import os
import json
import PyPDF2
import re
from concurrent.futures import ThreadPoolExecutor
import time

# Rolls & Subjects
rolls = ["f9"]
subs = ["devops", "dmkd", "nws", "spm", "sqat", "ssic"]

# Configure Gemini API
genai.configure(api_key="API-KEY")
model = genai.GenerativeModel("gemini-2.5-flash")


def safe_extract_response(response):
    """Safely extract text from Gemini response parts."""
    try:
        return "".join(
            part.text for part in response.candidates[0].content.parts if hasattr(part, "text")
        ).strip()
    except Exception:
        return ""


def evaluate(roll, sub):
    # Run OCR
    start_time = time.time() 
    future = ocr_pdf_async(
        f"test-material/{roll}/{sub}.pdf",
        method="easyocr",
        pages="all",
        lang="en",
        gpu=True,
    )
    print(f"OCR started for {roll}-{sub}...")
    output = future.result()

    if not output.get("combined_text"):
        print(f"⚠️ OCR failed for {roll}-{sub}")
        return

    # Prompt template
    prompt = """
You are given raw OCR text from an exam paper.

Your task:
1. Clean the OCR text to make it readable.
2. Identify each question and the student’s answer.
3. Extract the answers into structured JSON in this format:
{
  "answers": [
    {
      "number": "1.a",
      "question": "Question text here",
      "text": "Student's answer text here",
      "marks": based on the max score of question,
      "remark": "Reason for deduction or comment"
    }
  ]
}
4. For evaluation: 
   - Award marks based on correctness and completeness.
   - Provide remarks if marks are deducted.

Return **only valid JSON** without additional text.

Here is the OCR text:
"""

    # Load question paper
    pdf_file = f"test-material/qps/{sub}_qp.pdf"
    qp = ""
    with open(pdf_file, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            qp += page.extract_text() + "\n"

    # Save raw question paper text for reference
    with open("question_paper.txt", "w", encoding="utf-8") as f:
        f.write(qp)

    q_paper = f"""
=========================================================
Here is the question paper:
{qp[470:]}   # Avoids junk header, adjust as needed
"""

    # Build final prompt
    final_prompt = prompt + output["combined_text"] + q_paper

    # Call Gemini
    response = model.generate_content(final_prompt)
    filtered_text = safe_extract_response(response)
    filtered_text = filtered_text.replace("```json", "").replace("```", "").strip()

    # Ensure results folder exists
    os.makedirs(f"results/{roll}", exist_ok=True)

    # Try parsing JSON
    try:
        data = json.loads(filtered_text)
    except json.JSONDecodeError:
        # Fallback: regex to extract first JSON-like block
        match = re.search(r"\{.*\}", filtered_text, re.S)
        if match:
            data = json.loads(match.group())
        else:
            print(f"❌ Failed to decode JSON for {roll}-{sub}")
            return

    # Save JSON result
    with open(f"results/{roll}/{sub}-result.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    elapsed = time.time() - start_time
    print(f"✅ JSON saved to results/{roll}/{sub}-result.json")
    print(f"⏱ Time taken for {roll}-{sub}: {elapsed:.2f} seconds\n")

if __name__ == "__main__":
    for r in rolls:
        roll_start = time.time()
        times = {}  # store per-subject time
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(evaluate, r, s): s for s in subs}
            for f in futures:
                f.result()
        roll_elapsed = time.time() - roll_start
        print(f"🕒 Total time for roll {r}: {roll_elapsed:.2f} seconds\n")
