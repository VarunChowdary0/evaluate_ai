# Evaluate.AI

Evaluate.AI is a Python tool that automates the evaluation of exam answer sheets.  
It uses **OCR** to extract text from PDFs and **Google Gemini AI** to evaluate answers, producing structured JSON output with marks and remarks.

---

## Features

- Extracts text from scanned PDF answer sheets using **EasyOCR**.
- Automatically evaluates answers against the question paper.
- Outputs structured JSON for each student and subject:
  ```json
  {
    "answers": [
      {
        "number": "1.a",
        "question": "Question text here",
        "text": "Student's answer text here",
        "marks": 4,
        "remark": "Reason for deduction or comment"
      }
    ]
  }

- Tracks time taken per subject and total time per student.

- Supports parallel processing using Python’s ThreadPoolExecutor.

## Requirements

- Python 3.10+

- Packages:
```bash
pip install -r requirements.txt
```

- GPU (optional, but speeds up OCR).


## Setup

### 1. Clone the repository:
```bash
git clone https://github.com/VarunChowdary0/evaluate.ai.git
cd evaluate.ai
```

### 2. Set your Google Gemini API key in main.py:
```
genai.configure(api_key="YOUR_API_KEY")
```

### 3. Prepare folders:
```
test-material/
    f9/
        devops.pdf
        dmkd.pdf
        ...
    qps/
        devops_qp.pdf
        dmkd_qp.pdf
        ...
```

## Usage

Run the main script:
```
python main.py
```

### - The script will:

- - Run OCR on all PDFs for each student and subject.

- - Call Google Gemini to evaluate answers.

- - Save results in results/{roll}/{subject}-result.json.

- - Print time taken per subject and total time per student.

### Folder Structure
```evaluate.ai/
│
├─ main.py                # Main evaluation script
├─ modules/
│   └─ ocr_pdf.py         # OCR module using EasyOCR
├─ test-material/
│   ├─ f9/                # Answer sheets by roll
│   └─ qps/               # Question papers
├─ results/               # JSON results per student
├─ requirements.txt       # Python dependencies
└─ README.md
```

## Notes

- GPU recommended: OCR is much faster on GPU. Without GPU, EasyOCR will run on CPU and may be slower.

- JSON output: If Gemini AI produces non-JSON output, the script uses regex to clean it.

- Parallel processing: The script runs subjects in parallel for faster processing.
