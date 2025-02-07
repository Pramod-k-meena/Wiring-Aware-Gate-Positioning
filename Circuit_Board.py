import random
import math
from collections import defaultdict

class Gate:
    def __init__(self, name, width, height):
        self.name = name
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.pins = {}
        self.connections = []

class Wire:
    def __init__(self, start_gate, start_pin, end_gate, end_pin):
        self.start_gate = start_gate
        self.start_pin = start_pin
        self.end_gate = end_gate
        self.end_pin = end_pin

class CircuitBoard:
    def __init__(self):
        self.gates = {}
        self.wires = []
        self.width = 0
        self.height = 0

    def add_gate(self, gate):
        self.gates[gate.name] = gate

    def add_wire(self, wire):
        self.wires.append(wire)
        self.gates[wire.start_gate].connections.append(wire.end_gate)
        self.gates[wire.end_gate].connections.append(wire.start_gate)

    def calculate_wire_length(self):
        total_length = 0
        for wire in self.wires:
            start_gate = self.gates[wire.start_gate]
            end_gate = self.gates[wire.end_gate]
            start_x = start_gate.x + start_gate.pins[wire.start_pin][0]
            start_y = start_gate.y + start_gate.pins[wire.start_pin][1]
            end_x = end_gate.x + end_gate.pins[wire.end_pin][0]
            end_y = end_gate.y + end_gate.pins[wire.end_pin][1]
            total_length += abs(start_x - end_x) + abs(start_y - end_y)
        return total_length

    def optimize_placement(self, cool):
        sorted_gates = sorted(self.gates.values(), key=lambda x: len(x.connections), reverse=True)
        
        largest_gate = sorted_gates[0]
        largest_gate.x = 0
        largest_gate.y = 0
        placed_gates = {largest_gate.name}

        for gate in sorted_gates[1:]:
            if any(conn in placed_gates for conn in gate.connections):
                self.place_connected_gate(gate, placed_gates)
            else:
                self.place_unconnected_gate(gate)
            placed_gates.add(gate.name)

        # self.shift_to_first_quadrant()
        self.simulated_annealing(cool)
        

    def place_connected_gate(self, gate, placed_gates):
        best_x, best_y = None, None
        min_distance = float('inf')

        for connected_gate_name in gate.connections:
            if connected_gate_name in placed_gates:
                connected_gate = self.gates[connected_gate_name]
                for dx in range(-gate.width, connected_gate.width + 1):
                    for dy in range(-gate.height, connected_gate.height + 1):
                        x = connected_gate.x + dx
                        y = connected_gate.y + dy
                        if self.is_valid_placement(gate, x, y):
                            distance = self.calculate_distance(gate, x, y)
                            if distance < min_distance:
                                min_distance = distance
                                best_x, best_y = x, y

        if best_x is None or best_y is None:
            self.place_unconnected_gate(gate)
        else:
            gate.x, gate.y = best_x, best_y

    def place_unconnected_gate(self, gate):
        max_x = max((g.x + g.width for g in self.gates.values() if g.x is not None), default=0)
        max_y = max((g.y + g.height for g in self.gates.values() if g.y is not None), default=0)
        
        for y in range(0, max_y, 10):
            for x in range(0, max_x , 10):
                if self.is_valid_placement(gate, x, y):
                    gate.x, gate.y = x, y
                    return

        gate.x, gate.y = max_x + gate.width, 0

    def is_valid_placement(self, gate, x, y):
        if x < 0 or y < 0:
            return False
        for other_gate in self.gates.values():
            if other_gate.name != gate.name and other_gate.x is not None:
                if (x < other_gate.x + other_gate.width and x + gate.width > other_gate.x and
                    y < other_gate.y + other_gate.height and y + gate.height > other_gate.y):
                    return False
        return True

    def calculate_distance(self, gate, x, y):
        total_distance = 0
        for wire in self.wires:
            if wire.start_gate == gate.name or wire.end_gate == gate.name:
                other_gate_name = wire.end_gate if wire.start_gate == gate.name else wire.start_gate
                other_gate = self.gates[other_gate_name]
                if other_gate.x is not None:
                    gate_x = x + gate.pins[wire.start_pin if wire.start_gate == gate.name else wire.end_pin][0]
                    gate_y = y + gate.pins[wire.start_pin if wire.start_gate == gate.name else wire.end_pin][1]
                    other_x = other_gate.x + other_gate.pins[wire.end_pin if wire.start_gate == gate.name else wire.start_pin][0]
                    other_y = other_gate.y + other_gate.pins[wire.end_pin if wire.start_gate == gate.name else wire.start_pin][1]
                    total_distance += abs(gate_x - other_x) + abs(gate_y - other_y)
        return total_distance

    def simulated_annealing(self,cooling_rate):
        temperature = 1000
        min_temperature = 0.01

        current_solution = {gate.name: (gate.x, gate.y) for gate in self.gates.values()}
        current_cost = self.calculate_wire_length()
        best_solution = current_solution.copy()
        best_cost = current_cost

        while temperature > min_temperature:
            gate = random.choice(list(self.gates.values()))
            old_x, old_y = gate.x, gate.y

            for _ in range(20):
                new_x = max(0, old_x + random.randint(-20, 20))
                new_y = max(0, old_y + random.randint(-20, 20))
                if self.is_valid_placement(gate, new_x, new_y):
                    break
            else:
                continue

            gate.x, gate.y = new_x, new_y
            new_cost = self.calculate_wire_length()

            if new_cost < current_cost or random.random() < math.exp((current_cost - new_cost) / temperature):
                current_solution[gate.name] = (new_x, new_y)
                current_cost = new_cost

                if current_cost < best_cost:
                    best_solution = current_solution.copy()
                    best_cost = current_cost
            else:
                gate.x, gate.y = old_x, old_y

            temperature *= cooling_rate

        for gate_name, (x, y) in best_solution.items():
            self.gates[gate_name].x = x
            self.gates[gate_name].y = y

        self.update_board_dimensions()

    def shift_to_first_quadrant(self):
        min_x = min(gate.x for gate in self.gates.values())
        min_y = min(gate.y for gate in self.gates.values())

        for gate in self.gates.values():
            gate.x -= min_x
            gate.y -= min_y

        self.update_board_dimensions()

    def update_board_dimensions(self):
        self.width = max(gate.x + gate.width for gate in self.gates.values())
        self.height = max(gate.y + gate.height for gate in self.gates.values())

    def generate_output(self):
        wire_length = self.calculate_wire_length()
        output = f"bounding_box {self.width} {self.height}\n"
        output += f"wire_length {wire_length}\n"
        for gate in self.gates.values():
            output += f"{gate.name} {gate.x} {gate.y}\n"
        return output

def parse_input(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    board = CircuitBoard()
    current_gate = None
    
    for line in lines:
        parts = line.strip().split()
        
        if len(parts) == 3 and parts[0].startswith('g'):
            gate_name = parts[0]
            width = int(parts[1])
            height = int(parts[2])
            current_gate = Gate(gate_name, width, height)
            board.add_gate(current_gate)

        elif parts[0] == 'pins' and current_gate:
            gate_name = parts[1]
            gate = board.gates[gate_name]
            for i in range(2, len(parts), 2):
                pin_name = f"p{(i-2)//2 + 1}"
                pin_x = int(parts[i])
                pin_y = int(parts[i+1])
                gate.pins[pin_name] = (pin_x, pin_y)

        elif parts[0] == 'wire':
            start_gate, start_pin = parts[1].split('.')
            end_gate, end_pin = parts[2].split('.')
            wire = Wire(start_gate, start_pin, end_gate, end_pin)
            board.add_wire(wire)
    
    return board

def main_cluster(input_file = "input.txt", output_file = "output.txt", iterations = 1,cool = 0.99999):
    min_output = None
    min_wire_length = float('inf')

    for i in range(iterations):
        # print(f"Iteration {i+1}") 
        # Parse input from file
        board = parse_input(input_file)
        # Optimize placement
        board.optimize_placement(cool)  # Assuming this function is implemented
        # Generate output
        output = board.generate_output()  # Assuming this function returns output as a string
        # Extract wire length from the output
        wire_length = int(output.split('\n')[1].split()[1])  # Assuming 2nd line has wire length in this format
        # print(f"Wire length: {wire_length}")
        if wire_length < min_wire_length:
            min_wire_length = wire_length
            board.shift_to_first_quadrant()
            min_output = output
    # Write the best output to output_file
    with open(output_file, 'w') as f:
        f.write(min_output)
    
    # print("\nBest output written to output file.")
