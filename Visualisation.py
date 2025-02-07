import pygame
import random
import sys

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
BACKGROUND_COLOR = (255, 255, 255)
GATE_ALPHA = 128
WIRE_COLOR = (0, 255, 0)
WIRE_HIGHLIGHT_COLOR = (255, 0, 0)
PIN_COLOR = (0, 0, 255)
PIN_HIGHLIGHT_COLOR = (255, 0, 0)
PIN_RADIUS = 10

def distance_to_line(point, line_start, line_end):
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:  # It's a point not a line
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = ((px - x1) * dx + (py - y1) * dy) / (dx ** 2 + dy ** 2)
    t = max(0, min(1, t))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5

def process_input(fp="input.txt"):
    gates = {}
    wires = {}
    pins = {}
    wire_id = 0
    with open(fp, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith("pins"):
            temp = line.split()
            curr_gate = temp[1]
            gates[curr_gate]['pins'] = {}
            for i, pin in enumerate(temp[2:]):
                if i % 2 == 1:
                    gates[curr_gate]['pins'][f'p{i // 2 + 1}'] = (int(temp[i + 1]), int(temp[i + 2]))
        elif line.startswith("wire"):
            start, end = line.split()[1:]
            start_gate, start_pin = start.split('.')
            end_gate, end_pin = end.split('.')
            if gates[start_gate]['pins'][start_pin][0] == gates[start_gate]['width'] or gates[start_gate]['pins'][start_pin][0] == 0:
                mid_pos = 1
            else:
                mid_pos = 0
            wires[wire_id] = {'start': (start_gate, start_pin), 'end': (end_gate, end_pin), 'mid_pos': mid_pos}
            if f'{start_gate}.{start_pin}' not in pins:
                pins[f'{start_gate}.{start_pin}'] = [wire_id]
            else:
                pins[f'{start_gate}.{start_pin}'].append(wire_id)
            if f'{end_gate}.{end_pin}' not in pins:
                pins[f'{end_gate}.{end_pin}'] = [wire_id]
            else:
                pins[f'{end_gate}.{end_pin}'].append(wire_id)
            wire_id += 1
        else:
            curr_gate = line.split()[0]
            width = int(line.split()[1])
            height = int(line.split()[2])
            gates[curr_gate] = {'width': width, 'height': height}
    return gates, wires, pins

class CircuitVisualizer:
    def __init__(self, gates=None, wires=None, fp="output.txt"):
        if gates is None or wires is None:
            self.gates, self.wires, self.pins = process_input()
        self.coordinates = {}
        self.bounding_box = (1, 1)
        self.wire_length = None
        self.load_coordinates(fp)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Circuit Visualizer")
        self.offset_x, self.offset_y = 0, 0
        self.scale = min(SCREEN_WIDTH / self.bounding_box[0], SCREEN_HEIGHT / self.bounding_box[1])
        self.dragging = False
        self.last_mouse_pos = None
        self.font = pygame.font.Font(None, 30)
        self.colors = {}
        for gate in self.gates.keys():
            self.colors[gate] = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))

    def load_coordinates(self, fp):
        with open(fp, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith("bounding_box"):
                self.bounding_box = [int(x) for x in line.split()[1:]]
            elif line.startswith("wire_length"):
                self.wire_length = int(line.split()[1])
            else:
                parts = line.split()
                self.coordinates[parts[0]] = (int(parts[1]), int(parts[2]))

    def draw_gate(self, gate, x, y):
        width, height = self.gates[gate]['width'], self.gates[gate]['height']
        color = self.colors[gate]
        rect = pygame.Rect(x, y, width * self.scale, height * self.scale)
        pygame.draw.rect(self.screen, color + (GATE_ALPHA,), rect)
        pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
        text = self.font.render(gate, True, (0, 0, 0))
        text_rect = text.get_rect(center=rect.center)
        self.screen.blit(text, text_rect)

    def draw_wire(self, wire, highlight=False):
        start_gate, start_pin = wire['start']
        end_gate, end_pin = wire['end']
        start = self.coordinates[start_gate][0] + self.gates[start_gate]['pins'][start_pin][0], self.coordinates[start_gate][1] + self.gates[start_gate]['pins'][start_pin][1]
        end = self.coordinates[end_gate][0] + self.gates[end_gate]['pins'][end_pin][0], self.coordinates[end_gate][1] + self.gates[end_gate]['pins'][end_pin][1]
        if wire['mid_pos'] == 1:
            mid = end[0], start[1]
        else:
            mid = start[0], end[1]
        start = self.transform_point(start)
        end = self.transform_point(end)
        mid = self.transform_point(mid)
        color = WIRE_HIGHLIGHT_COLOR if highlight else WIRE_COLOR
        pygame.draw.line(self.screen, color, start, mid, 2)
        pygame.draw.line(self.screen, color, mid, end, 2)

    def draw_pin(self, pin_id, highlight=False):
        gate = pin_id.split('.')[0]
        pin_info = self.gates[gate]['pins'][pin_id.split('.')[1]]
        pin = self.coordinates[gate][0] + pin_info[0], self.coordinates[gate][1] + pin_info[1]
        transformed_pin = self.transform_point(pin)
        if highlight:
            pygame.draw.circle(self.screen, PIN_HIGHLIGHT_COLOR, transformed_pin, PIN_RADIUS)
        else:
            pygame.draw.circle(self.screen, PIN_COLOR, transformed_pin, PIN_RADIUS)

    def transform_point(self, point):
        x, y = point
        return (x + self.offset_x) * self.scale, (y + self.offset_y) * self.scale

    def inverse_transform_point(self, point):
        x, y = point
        return x / self.scale - self.offset_x, y / self.scale - self.offset_y

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(BACKGROUND_COLOR)
        is_mouse_close_to_any_pin = self.is_mouse_close_to_any_pin(mouse_pos)
        for gate, (x, y) in self.coordinates.items():
            transformed_x, transformed_y = self.transform_point((x, y))
            self.draw_gate(gate, transformed_x, transformed_y)
        for gate in self.coordinates.keys():
            for pin_id in self.gates[gate]['pins'].keys():
                if f'{gate}.{pin_id}' != is_mouse_close_to_any_pin:
                    self.draw_pin(f'{gate}.{pin_id}')
        if is_mouse_close_to_any_pin is not None:
            self.draw_pin(is_mouse_close_to_any_pin, highlight=True)

        hovered_point = self.get_hovered_point(mouse_pos)

        if is_mouse_close_to_any_pin is None:
            for wire in self.wires.values():
                self.draw_wire(wire, False)
                if self.is_point_on_wire(hovered_point, wire):
                    self.draw_hover_box(mouse_pos, str(self.get_wire_length(wire)))
        else:
            for wire_id in self.pins[is_mouse_close_to_any_pin]:
                self.draw_wire(self.wires[wire_id], True)
                if self.is_point_on_wire(hovered_point, self.wires[wire_id]):
                    self.draw_hover_box(mouse_pos, str(self.get_wire_length(self.wires[wire_id])))

    def get_hovered_point(self, mouse_pos):
        return self.inverse_transform_point(mouse_pos)

    def get_wire_length(self, wire):
        start_gate, start_pin = wire['start']
        end_gate, end_pin = wire['end']
        start = self.coordinates[start_gate][0] + self.gates[start_gate]['pins'][start_pin][0], self.coordinates[start_gate][1] + self.gates[start_gate]['pins'][start_pin][1]
        end = self.coordinates[end_gate][0] + self.gates[end_gate]['pins'][end_pin][0], self.coordinates[end_gate][1] + self.gates[end_gate]['pins'][end_pin][1]
        return abs(start[0] - end[0]) + abs(start[1] - end[1])

    def draw_hover_box(self, mouse_pos, text):
        text_surface = self.font.render(text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(mouse_pos[0] + 20, mouse_pos[1] - 20))
        bg_rect = text_rect.inflate(20, 20)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, 1)
        self.screen.blit(text_surface, text_rect)

    def is_point_on_wire(self, point, wire):
        start_gate, start_pin = wire['start']
        end_gate, end_pin = wire['end']
        start = self.coordinates[start_gate][0] + self.gates[start_gate]['pins'][start_pin][0], self.coordinates[start_gate][1] + self.gates[start_gate]['pins'][start_pin][1]
        end = self.coordinates[end_gate][0] + self.gates[end_gate]['pins'][end_pin][0], self.coordinates[end_gate][1] + self.gates[end_gate]['pins'][end_pin][1]
        if wire['mid_pos'] == 1:
            mid = end[0], start[1]
        else:
            mid = start[0], end[1]
        d1 = distance_to_line(point, start, mid)
        d2 = distance_to_line(point, mid, end)
        d = min(d1, d2)
        return d < 0.15

    def is_mouse_close_to_any_pin(self, mouse_pos):
        for gate, gate_info in self.gates.items():
            for pin_id, pin_info in gate_info['pins'].items():
                pin = self.coordinates[gate][0] + pin_info[0], self.coordinates[gate][1] + pin_info[1]
                transformed_pin = self.transform_point(pin)
                if ((transformed_pin[0] - mouse_pos[0]) ** 2 + (transformed_pin[1] - mouse_pos[1]) ** 2) ** 0.5 < PIN_RADIUS * 1.5:
                    if f'{gate}.{pin_id}' in self.pins:
                        return f'{gate}.{pin_id}'

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                    for wire_id, wire in self.wires.items():
                        if self.is_point_on_wire(self.get_hovered_point(event.pos), wire):
                            self.wires[wire_id]['mid_pos'] = 1 - self.wires[wire_id]['mid_pos']
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx, dy = event.pos[0] - self.last_mouse_pos[0], event.pos[1] - self.last_mouse_pos[1]
                    self.offset_x += dx / self.scale
                    self.offset_y += dy / self.scale
                    self.last_mouse_pos = event.pos
            elif event.type == pygame.MOUSEWHEEL:
                zoom_factor = 1.1
                if event.y > 0:
                    self.scale *= zoom_factor
                else:
                    self.scale /= zoom_factor
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def run(self):
        clock = pygame.time.Clock()
        total_wire_length = 0
        for wire in self.wires.values():
            total_wire_length += self.get_wire_length(wire)
        print(f"Calculated total wire length: {total_wire_length}")
        if total_wire_length != self.wire_length:
            print(f"Total wire length is incorrect! Expected: {self.wire_length}, Found: {total_wire_length}")
        while True:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            clock.tick(60)


visualizer = CircuitVisualizer()
visualizer.run()