from crsa_agent.initial_code_check_utils import (
    detect_language,
    check_python,
    check_java,
)


python_code = """
def calculate_total(items):
    return sum(items)
"""

invalid_python = """
def calculate_total(items)
    return sum(items)
"""

java_code = """
class ProductSearch {
    public void search() {
        System.out.println("Hell
        o");
    }
}
"""

invalid_java = """
class ProductSearch {
    public void search() {
        System.out.println("Hello")
    }
}
"""


# 1. Language Detection
print("\n========== LANGUAGE DETECTION ==========")

print("Python:", detect_language(python_code))
print("Java:", detect_language(java_code))


# 2. Python Syntax Validation
print("\n========== PYTHON VALIDATION ==========")

print("Valid Python:", check_python(python_code))
print("Invalid Python:", check_python(invalid_python))


# 3. Java Syntax Validation
print("\n========== JAVA VALIDATION ==========")

print("Valid Java:", check_java(java_code))
print("Invalid Java:", check_java(invalid_java))