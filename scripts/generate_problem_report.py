import os
import re
import json
import pandas as pd
from pathlib import Path
from llama_cpp import Llama

# Configuration
DIRECTORY = os.path.join(os.path.dirname(__file__), "../dsa-variation")
OUTPUT_FILE = os.path.expanduser("~/Developer/pna/script/problem_status.xlsx")
MODEL_PATH = os.path.expanduser("../model/mistral-7b-instruct-v0.1.Q4_K_M.gguf")  # Update this path

# Initialize local LLM
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,  # Context window size
    n_threads=4,  # CPU threads to use
    verbose=False
)

def analyze_content(content):
    """Analyze problem content using local LLM"""
    problem_statement = content[:3000]  # Use first 3000 characters
    
    prompt = f"""Analyze this programming problem and respond in JSON format:
    {{
        "title": "concise problem title extracted from content",
        "has_cpp": boolean,
        "has_python": boolean
    }}

    Instructions:
    1. Create a short title from the problem content
    2. Check for complete C++ code (look for ```cpp code blocks)
    3. Check for complete Python code (look for ```python code blocks)

    Problem Content:
    {problem_statement}
    """
    
    try:
        response = llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
            max_tokens=200
        )
        
        result = json.loads(response['choices'][0]['message']['content'])
        return (
            result.get('title', 'Untitled Problem').strip(),
            result.get('has_cpp', False),
            result.get('has_python', False)
        )
        
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        # Fallback to simple regex checks
        has_cpp = '```cpp' in content
        has_python = '```python' in content
        title = re.search(r'^#\s+(.+)$', content, flags=re.MULTILINE)
        return (
            title.group(1).strip() if title else "Untitled Problem",
            has_cpp,
            has_python
        )

# ... rest of the code from original version (process_files, main) remains the same ...

def process_files(directory):
    data = []
    
    for file_path in Path(directory).glob("*.md"):
        print(f"Processing: {file_path.name}")
        serial = file_path.stem
        if not serial.isdigit():
            continue

        content = file_path.read_text(encoding='utf-8')
        
        # Get analysis from single API call
        title, has_cpp, has_python = analyze_content(content)
        
        data.append({
            "Serial No": int(serial),
            "Problem Title": title,
            "C++": "Yes" if has_cpp else "No",
            "Python": "Yes" if has_python else "No"
        })
    
    return sorted(data, key=lambda x: x["Serial No"])

def main():
    results = process_files(DIRECTORY)
    df = pd.DataFrame(results)
    
    # Save with auto-adjust column widths
    with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
        worksheet = writer.sheets['Sheet1']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(idx, idx, max_len)
    
    print(f"Excel file created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
