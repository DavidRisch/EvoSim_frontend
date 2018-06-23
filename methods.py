import math


def double_list_to_string(input_list):
    output = "["
    for element in input_list:
        output += "{:.2f}".format(element) + ", "

    output = output[:-2]
    output += "]"
    return output


def calculate_distance(position_a, position_b):
    a_to_b_x = position_b[0] - position_a[0]
    a_to_b_y = position_b[1] - position_a[1]

    distance = math.sqrt(math.pow(a_to_b_x, 2) + math.pow(a_to_b_y, 2))

    return distance


def calculate_direction_difference(position_a, position_b, direction_a):
    a_to_b_x = position_b[0] - position_a[0]
    a_to_b_y = position_b[1] - position_a[1]

    angle = (math.atan2(-a_to_b_y, -a_to_b_x) + math.pi) / 2

    direction = angle / math.pi
    direction = -direction + 0.25

    direction = direction - direction_a
    while direction < 0:
        direction = 1 + direction

    return direction


def confine_number(number, minimum, maximum):
    if minimum is not None:
        if number < minimum:
            number = minimum

    if maximum is not None:
        if number > maximum:
            number = maximum

    return number


def wrap_position(position, configuration):
    for i in [0, 1]:
        if position[i] < 0:
            position[i] = configuration["Area"] + position[i]
        if position[i] > configuration["Area"]:
            position[i] = configuration["Area"] - position[i]

    return position


def wrap_direction(direction):
    if direction < 0:
        direction = 1 + direction
    if direction > 1:
        direction = 1 - direction

    return direction


def send_message(header, content):
    directory = __file__
    directory = directory.replace("\\", "/")
    position = directory.rfind("/")
    directory = directory[:position]
    position = directory.rfind("/")
    directory = directory[:position]
    directory += "/"

    message = "~" + header + "~ " + content
    # print(message)

    output_file = open(directory + "ToBackend.txt", "w")

    output_file.write(message)
    output_file.close()


def read_setting(name):
    file = open("settings.cfg", "r")
    for line in file:
        position = line.find("=")
        if position != -1:
            line_name = line[:position]
            line_output = line[position+1:]
            if line_name == name:
                return line_output


def write_setting(name, value):
    lines = open("settings.cfg", "r").read().splitlines()
    for i in range(0, len(lines)):
        position = lines[i].find("=")
        if position != -1:
            line_name = lines[i][:position]
            if line_name == name:
                lines[i] = name + "=" + value
    open('settings.cfg', 'w', newline='\n').write('\n'.join(lines))
