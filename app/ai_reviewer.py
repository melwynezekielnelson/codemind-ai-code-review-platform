import os
import sys
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELS = [
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-v4-flash:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
]

def ask_ai(prompt, system_prompt="You are an expert code reviewer."):
    for model in MODELS:
        print(f"Trying: {model}")
        for attempt in range(3):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8501",
                        "X-Title": "CodeMind AI",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 1000,
                    },
                    timeout=30,
                )
                data = response.json()

                if "choices" in data:
                    print(f"Success with: {model}")
                    return data["choices"][0]["message"]["content"]

                if data.get("error", {}).get("code") == 429:
                    wait = data["error"]["metadata"].get("retry_after_seconds", 5)
                    print(f"  Rate limited, waiting {wait:.0f}s...")
                    time.sleep(min(wait, 20))
                    continue

                print(f"  Error: {data.get('error', {}).get('message')}")
                break

            except Exception as e:
                print(f"  Exception: {e}")
                break

    return "AI is busy right now. Please try again in a moment."

def review_function(func_name, func_code, security_issues=None):
    security_context = ""
    if security_issues:
        security_context = "Security issues found:\n"
        for issue in security_issues:
            security_context += f"- Line {issue['line']}: {issue['issue']}\n"

    prompt = (
        f"Review this Python function and provide:\n"
        f"1. What it does (1 sentence)\n"
        f"2. Any bugs or issues\n"
        f"3. Security concerns\n"
        f"4. How to improve it\n\n"
        f"Function name: {func_name}\n\n"
        f"Code:\n{func_code}\n\n"
        f"{security_context}"
        f"Keep your response concise and practical."
    )
    return ask_ai(prompt)

def explain_code(code, language="Python"):
    prompt = (
        f"Explain this {language} code in simple terms:\n"
        f"- What does it do?\n"
        f"- How does it work step by step?\n"
        f"- What is it used for?\n\n"
        f"Code:\n{code}"
    )
    return ask_ai(prompt, "You are a coding teacher explaining to a beginner.")

def suggest_refactor(func_name, func_code):
    prompt = (
        f"Refactor this Python function to be cleaner and more efficient.\n"
        f"Show the improved version with a brief explanation of changes.\n\n"
        f"Function: {func_name}\n"
        f"{func_code}"
    )
    return ask_ai(prompt, "You are a senior Python developer focused on clean code.")

def generate_full_review(parsed_files, security_issues):
    reviews = []
    for file_result in parsed_files:
        file_path = file_result["file"]
        print(f"\nReviewing: {file_path}")
        file_security = [
            issue for issue in security_issues
            if issue.get("file", "").endswith(os.path.basename(file_path))
        ]
        for func in file_result["functions"]:
            print(f"  Analyzing: {func['name']}...")
            review = review_function(func["name"], func["code"], file_security)
            reviews.append({
                "file": file_path,
                "function": func["name"],
                "code": func["code"],
                "ai_review": review,
                "start_line": func["start_line"],
            })
    return reviews

if __name__ == "__main__":
    sys.path.append(".")
    from parser.code_parser import parse_file

    print("Testing AI Review on main.py...\n")
    parsed = [parse_file("main.py")]

    if parsed[0] and parsed[0]["functions"]:
        func = parsed[0]["functions"][0]
        print(f"Reviewing: {func['name']}\n")
        print("-" * 40)
        review = review_function(func["name"], func["code"])
        print(review)
        print("-" * 40)
        print("\nExplaining code...\n")
        explanation = explain_code(func["code"])
        print(explanation)
    else:
        print("No functions found in main.py")