import methods

import time
import json


class FrameInformation:
    is_being_used = False
    has_been_used = True
    state = {}


class Manager:
    configuration = {}
    agents = []
    food_positions = []
    tick_count = 0
    food_to_spawn = 0
    # keeps track of food, that needs to be spawned (because configuration["Food_PerTick"] is not an int)

    fps = 20
    last_frame_ms = 0
    speed = 20  # ticks/second
    speed_before_pause = 0
    jump_to_tick = 0

    number_of_threads = 8

    mark_agents_at_age = 2000

    exit_tasks = False
    frame_information = FrameInformation()

    backend_needs_configuration = True
    main_directory = ""
    selected_agent_id = 0
    save_path = ""
    load_path = ""

    def __init__(self, configuration):
        self.configuration = configuration

        directory = __file__
        directory = directory.replace("\\", "/")
        position = directory.rfind("/")
        directory = directory[:position]
        position = directory.rfind("/")
        directory = directory[:position]
        self.main_directory = directory

    def read_message(self):
        file = open(self.main_directory + "/ToFrontend.txt", "r+")
        line = file.read()

        if len(line) < 6:
            return

        prefix = line[:6]
        content = line[7:]

        if content[:1] == "{" and content[-1] == "}":

            if prefix == '~conf~':
                self.backend_needs_configuration = True
                print("send cnf")
                methods.send_message("conf", json.dumps(self.configuration))

            if prefix == '~updt~':
                self.backend_needs_configuration = False
                update = json.loads(content)
                self.tick_count = update["tick_count"]
                self.use_update(update)

        file.truncate(0)
        file.close()

    def use_update(self, state):

        if not self.frame_information.is_being_used:
            self.frame_information.is_being_used = True
            self.frame_information.state = state
            self.frame_information.is_being_used = False
            self.frame_information.has_been_used = False

        # oldest_agent_age = -1
        # oldest_agent_id = 0
        # for agent in state["agents"]:
        #     if agent["age"] > oldest_agent_age:
        #         oldest_agent_age = agent["age"]
        #         oldest_agent_id = agent["id"]
        #
        # if oldest_agent_age >= self.mark_agents_at_age:
        #     print("marking agent", oldest_agent_age, oldest_agent_id)
        #     self.speed = 20
        #     self.selected_agent_id = oldest_agent_id

        if self.save_path == state["save_path"]:
            self.save_path = ""

        if self.load_path == state["load_path"]:
            self.load_path = ""

    def send_input_message(self):
        data = {
            "simulation_speed": self.speed,
            "selected_agent_id": self.selected_agent_id,
            "jump_to_tick": self.jump_to_tick,
            "save_path": self.save_path,
            "load_path": self.load_path,
        }

        string = json.JSONEncoder().encode(data)

        methods.send_message("inpt", string)

    def loop(self):
        print("reading...")

        while not self.exit_tasks:
            start_ms = time.time() * 1000.0

            self.read_message()
            if not self.backend_needs_configuration:
                self.send_input_message()

            current_ms = time.time() * 1000.0

            time_to_next_loop = (1 / 40) * 1000  # 40fps
            time_to_next_loop -= current_ms - start_ms

            if time_to_next_loop < 0:
                time_to_next_loop = 0

            time.sleep(time_to_next_loop / 1000)
