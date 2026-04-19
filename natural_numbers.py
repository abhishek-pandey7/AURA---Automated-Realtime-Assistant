def print_natural_numbers():
    try:
        n = int(input("Enter a number (n): "))
        if n < 1:
            print("Please enter a positive integer greater than 0.")
            return
        
        for i in range(1, n + 1):
            print(i)
    except ValueError:
        print("Invalid input. Please enter an integer.")

if __name__ == "__main__":
    print_natural_numbers()
