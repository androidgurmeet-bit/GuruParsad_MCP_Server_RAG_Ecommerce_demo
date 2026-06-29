print("calculator.py loaded")
def calculator_tool(query):
    try:
        return str(eval(query))
    except:
        return "Invalid math expression"