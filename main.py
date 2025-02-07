from Circuit_Board import *
import time
def count_gates(file_path):
    with open(file_path, 'r') as f:
        return sum(1 for line in f if len(line.strip().split()) == 3 and line.strip().split()[0].startswith('g'))
def read_wire_length(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('wire_length'):
                return int(line.split()[1])
def main(input_file = "input.txt", output_file = "output.txt"):
    # Count the number of gates
    num_gates = count_gates(input_file)
    print(f"Number of gates: {num_gates}")

    if(num_gates <= 10):
        main_cluster(iterations=3, cool = 0.99999)
    elif(num_gates <= 100):
        main_cluster(iterations=3)
    elif(num_gates <= 300):
        main_cluster(iterations=1)
    elif(num_gates <= 400):
        main_cluster(cool=0.9999)
    else:
        main_cluster(cool=0.999)
    main_cluster(iterations=1, cool=0.99)

if __name__ == "__main__":
    st = time.time()
    input_file = "input.txt"
    output_file = "output.txt"
    main(input_file, output_file)
    e = time.time()
    print(f"Execution time: {e - st:.2f} seconds")