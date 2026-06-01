import os
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript

PY_LANGUAGE = Language(tspython.language())
JS_LANGUAGE = Language(tsjavascript.language())

def get_parser(file_extension):
    parser = Parser()
    if file_extension == ".py":
        parser.language = PY_LANGUAGE
    elif file_extension in [".js", ".ts"]:
        parser.language = JS_LANGUAGE
    else:
        return None
    return parser

def extract_functions(node, code_bytes):
    functions = []
    if node.type in ["function_definition", "function_declaration"]:
        for child in node.children:
            if child.type == "identifier":
                name = code_bytes[child.start_byte:child.end_byte].decode("utf-8")
                body = code_bytes[node.start_byte:node.end_byte].decode("utf-8")
                functions.append({
                    "name": name,
                    "code": body,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                })
                break
    for child in node.children:
        functions.extend(extract_functions(child, code_bytes))
    return functions

def extract_classes(node, code_bytes):
    classes = []
    if node.type == "class_definition":
        for child in node.children:
            if child.type == "identifier":
                name = code_bytes[child.start_byte:child.end_byte].decode("utf-8")
                body = code_bytes[node.start_byte:node.end_byte].decode("utf-8")
                classes.append({
                    "name": name,
                    "code": body,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                })
                break
    for child in node.children:
        classes.extend(extract_classes(child, code_bytes))
    return classes

def parse_file(file_path):
    _, ext = os.path.splitext(file_path)
    parser = get_parser(ext)
    if not parser:
        return None
    with open(file_path, "rb") as f:
        code_bytes = f.read()
    tree = parser.parse(code_bytes)
    root = tree.root_node
    return {
        "file": file_path,
        "language": ext,
        "functions": extract_functions(root, code_bytes),
        "classes": extract_classes(root, code_bytes),
    }

def parse_repository(repo_path):
    results = []
    supported = {".py", ".js", ".ts"}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in supported:
                full_path = os.path.join(root, file)
                result = parse_file(full_path)
                if result:
                    results.append(result)
                    print(f"Parsed: {file} — {len(result['functions'])} functions, {len(result['classes'])} classes")
    return results

if __name__ == "__main__":
    result = parse_file("main.py")
    if result:
        print(result)
    else:
        print("No functions found yet — main.py is empty, thats fine!")