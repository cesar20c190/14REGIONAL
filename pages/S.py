def soma(a, b):
    """
    Add two numbers and return the result.

    Parameters:
    a (int or float): The first number.
    b (int or float): The second number.

    Returns:
    int or float: The sum of a and b.
    """
    return a + b

if __name__ == "__main__":
    print("Teste de soma:")
    resultado = soma(2, 3)
    print(f"2 + 3 = {resultado}")