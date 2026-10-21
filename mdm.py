# Hamming Code - Error Detection and Correction
# Even Parity

def calculate_parity_bits(m):
    r = 0

    while (2 ** r) < (m + r + 1):
        r += 1

    return r


def generate_hamming_code(data):
    m = len(data)

    # Calculate number of parity bits
    r = calculate_parity_bits(m)

    total_bits = m + r

    # Create 1-based array
    hamming = ['0'] * (total_bits + 1)

    # Place data bits
    data_index = 0

    for position in range(1, total_bits + 1):
        if (position & (position - 1)) != 0:
            hamming[position] = data[data_index]
            data_index += 1

    # Calculate parity bits
    for i in range(r):
        parity_position = 2 ** i
        parity = 0

        for position in range(1, total_bits + 1):
            if position & parity_position:
                parity ^= int(hamming[position])

        hamming[parity_position] = str(parity)

    return ''.join(hamming[1:])


def detect_and_correct(received):
    n = len(received)

    # Convert to 1-based array
    hamming = ['0'] + list(received)

    error_position = 0

    # Calculate number of parity bits
    r = 0
    while (2 ** r) <= n:
        r += 1

    # Calculate syndrome
    for i in range(r):
        parity_position = 2 ** i
        parity = 0

        for position in range(1, n + 1):
            if position & parity_position:
                parity ^= int(hamming[position])

        if parity != 0:
            error_position += parity_position

    # Display error status
    if error_position == 0:
        print("\nNo error detected.")
    else:
        print("\nError detected at position:", error_position)

        # Correct the error
        if hamming[error_position] == '0':
            hamming[error_position] = '1'
        else:
            hamming[error_position] = '0'

        print("Corrected Hamming Code:",
              ''.join(hamming[1:]))

    # Extract original data
    data = ""

    for position in range(1, n + 1):
        if (position & (position - 1)) != 0:
            data += hamming[position]

    print("Recovered Data:", data)


# ---------------- MAIN PROGRAM ----------------

data = input("Enter binary data: ")

# Validate input
if not all(bit in '01' for bit in data):
    print("Invalid input. Enter only 0 and 1.")
else:
    # Generate Hamming Code
    hamming_code = generate_hamming_code(data)

    print("\nOriginal Data:", data)
    print("Generated Hamming Code:", hamming_code)

    # Introduce error
    received = input(
        "\nEnter received Hamming Code "
        "(modify one bit to simulate an error): "
    )

    if len(received) != len(hamming_code) or \
       not all(bit in '01' for bit in received):

        print("Invalid received Hamming Code.")

    else:
        print("Received Hamming Code:", received)

        # Detect and correct error
        detect_and_correct(received)
