import methods

from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
import tkinter
import os
import errno
import datetime
import threading
import time
from PIL import Image  # pip install pillow
from PIL import ImageTk  # pip install pillow


class GuiThread (threading.Thread):
    def __init__(self, manager):
        threading.Thread.__init__(self)
        self.manager = manager
        self.name = "Gui thread"

    def run(self):
        print("Starting GUI thread")

        gui = Gui(self.manager.configuration)
        gui.manager = self.manager
        gui.bind_buttons()
        gui.tkinter_root.speed_slider.set(self.manager.speed)

        while not self.manager.exit_tasks:
            if not self.manager.frame_information.has_been_used and not self.manager.frame_information.is_being_used:
                self.manager.frame_information.is_being_used = True

                gui.frame_information = self.manager.frame_information
                gui.draw_frame()

                self.manager.frame_information.has_been_used = True
                self.manager.frame_information.is_being_used = False

            gui.position_has_been_saved = False
            gui.tkinter_root.update_idletasks()
            gui.tkinter_root.update()
            time.sleep(0.0001)  # 0.1ms

        # gui.tkinter_root.mainloop()

        print("Exiting GUI thread")


class Gui:
    manager = None

    position_has_been_saved = False

    configuration = {}
    area_in_px = 800
    tkinter_root = None

    one_unit_in_px = 0
    agent_images = []
    images = {}
    speed_before_pause = 20

    frame_information = None
    selected_agent_id = None

    table = []
    table_rows = 30
    table_agent_ids = []

    def __init__(self, configuration):
        self.configuration = configuration

        window_width = 5 + self.area_in_px + 5 + 500 + 5
        window_height = 5 + 60 + 5 + self.area_in_px + 5 + 100 + 5
        window_x = int(methods.read_setting("WindowX"))
        window_y = int(methods.read_setting("WindowY"))

        self.tkinter_root = tkinter.Tk()
        self.tkinter_root.geometry('%dx%d+%d+%d' % (window_width, window_height, window_x, window_y))

        self.tkinter_root.button_save = tkinter.Button(self.tkinter_root, text="Save", fg="black")
        self.tkinter_root.button_save.pack()
        self.tkinter_root.button_save.place(x=5, y=5, width=60, height=30)

        self.tkinter_root.button_load = tkinter.Button(self.tkinter_root, text="Load", fg="black")
        self.tkinter_root.button_load.pack()
        self.tkinter_root.button_load.place(x=70, y=5, width=60, height=30)

        self.tkinter_root.button_jump = tkinter.Button(self.tkinter_root, text="Jump 1 tick [k]", fg="black")
        self.tkinter_root.button_jump.pack()
        self.tkinter_root.button_jump.place(x=140, y=5, width=100, height=30)

        self.tkinter_root.speed_slider = Scale(self.tkinter_root, from_=0, to=1000, orient=HORIZONTAL)
        self.tkinter_root.speed_slider.pack()
        self.tkinter_root.speed_slider.place(x=(5 + self.area_in_px - 405), y=5, width=400, height=65)

        controls = Label(self.tkinter_root, anchor=NW, justify=LEFT,
                         text="faster[j]; slower[h]")

        controls.pack()
        controls.place(x=5, y=40, width=300, height=30)

        label_y = 5 + 60 + 5 + self.area_in_px + 5
        label_width = (self.area_in_px / 2 - 10)

        self.tkinter_root.agent_information_text = StringVar()
        self.tkinter_root.agent_information_text.set("")
        agent_information = Label(self.tkinter_root, anchor=NW, justify=LEFT,
                                  textvariable=self.tkinter_root.agent_information_text)
        agent_information.pack()

        agent_information.place(x=(self.area_in_px / 2 + 5), y=label_y, width=label_width, height=100)

        self.tkinter_root.general_information_text = StringVar()
        self.tkinter_root.general_information_text.set("")
        general_information = Label(self.tkinter_root, anchor=NW, justify=LEFT,
                                    textvariable=self.tkinter_root.general_information_text)
        general_information.pack()

        general_information.place(x=5, y=label_y, width=label_width, height=100)

        self.prepare_canvas()
        self.create_table()

    def bind_buttons(self):
        self.tkinter_root.protocol('WM_DELETE_WINDOW', self.quit_window)

        self.tkinter_root.button_save.bind("<Button-1>", self.save)
        self.tkinter_root.button_load.bind("<Button-1>", self.load)
        self.tkinter_root.button_jump.bind("<Button-1>", self.jump)
        self.tkinter_root.bind("h", lambda event, delta=-1: self.alter_speed(delta))
        self.tkinter_root.bind("j", lambda event, delta=1: self.alter_speed(delta))
        self.tkinter_root.bind("k", self.jump)
        self.tkinter_root.speed_slider.bind("<B1-Motion>", self.slider_set_speed)
        self.tkinter_root.speed_slider.bind("<Button-1>", self.slider_set_speed)
        self.tkinter_root.speed_slider.bind("<ButtonRelease-1>", self.slider_set_speed)

        self.tkinter_root.canvas.bind("<Button-1>", self.click_on_canvas)
        self.tkinter_root.bind("<space>", self.toggle_pause)

        self.tkinter_root.bind("<Configure>", self.save_window_position)

    def draw_frame(self):
        self.tkinter_root.canvas.delete("all")
        for agent in self.frame_information.state["agents"]:
            self.draw_agent(agent)
        for food_position in self.frame_information.state["food_positions"]:
            self.draw_food(food_position)

        self.set_information_texts()

        self.update_table()

    def set_information_texts(self):
        if "selected_agent" in self.frame_information.state:
            agent = "health: " + str(self.frame_information.state["selected_agent"]["health"]) + "\n"
            agent += "age: " + str(self.frame_information.state["selected_agent"]["age"]) + "\n"
            agent += "generation: " + str(self.frame_information.state["selected_agent"]["generation"]) + "\n"
            agent += "sensors: " + methods.double_list_to_string(
                self.frame_information.state["selected_agent"]["sensors"]) + "\n"
            agent += "output: " + methods.double_list_to_string(
                self.frame_information.state["selected_agent"]["output"]) + "\n"
        else:
            agent = "---"

        self.tkinter_root.agent_information_text.set(agent)

        general = "Tick: " + str(self.frame_information.state["tick_count"]) + "\n"
        general += "Tick/Sec: " + str(self.frame_information.state["ticks_per_second"]) + "\n"
        general += "Agents: " + str(len(self.frame_information.state["agents"])) \
                   + " / " + str(self.configuration["Agent_MinPopulation"])
        self.tkinter_root.general_information_text.set(general)

    def draw_agent(self, agent):
        # print("draw agent: "+str(agent))

        image_index = round(agent["direction"] * 60)
        image_index %= 60
        image = self.agent_images[image_index]

        center_position = [agent["position"][0] * self.one_unit_in_px,
                           self.area_in_px - agent["position"][1] * self.one_unit_in_px]

        self.tkinter_root.canvas.create_image(center_position[0], center_position[1], anchor=CENTER, image=image)

        if agent["id"] == self.manager.selected_agent_id:
            self.tkinter_root.canvas.create_image(center_position[0], center_position[1], anchor=CENTER,
                                                  image=self.images["Highlight"])

            angle = 360 * agent["direction"]
            angle = -angle + 90

            self.draw_agent_arcs(center_position, angle)

        # if agent.marked:
        #     self.tkinter_root.canvas.create_image(center_position[0], center_position[1], anchor=CENTER,
        #                                           image=self.images["Marker"])

    def draw_agent_arcs(self, center_position, angle):
        colors = {"Food": "#ffde00",
                  "Agent": "#4eff00",
                  "Attack": "#a80000"}

        for sensor_type in ["Food", "Agent"]:
            sensor_middle_angle = self.configuration["Sensor_" + sensor_type + "_Middle_Angel"]
            sensor_side_angle = self.configuration["Sensor_" + sensor_type + "_Side_Angel"]
            sensor_range = self.configuration["Sensor_" + sensor_type + "_Range"] * self.one_unit_in_px
            color = colors[sensor_type]

            x1 = center_position[0] - sensor_range
            x2 = center_position[0] + sensor_range
            y1 = center_position[1] - sensor_range
            y2 = center_position[1] + sensor_range

            self.tkinter_root.canvas.create_arc(x1, y1, x2, y2, outline=color,
                                                start=angle + sensor_middle_angle / 2 + sensor_side_angle,
                                                extent=-sensor_side_angle)

            self.tkinter_root.canvas.create_arc(x1, y1, x2, y2, outline=color,
                                                start=angle - sensor_middle_angle / 2,
                                                extent=sensor_middle_angle)

            self.tkinter_root.canvas.create_arc(x1, y1, x2, y2, outline=color,
                                                start=angle - sensor_middle_angle / 2 - sensor_side_angle,
                                                extent=sensor_side_angle)

            self.tkinter_root.canvas.create_arc(x1, y1, x2, y2, outline=color,
                                                start=angle + sensor_middle_angle / 2 + sensor_side_angle,
                                                extent=(360 - 2 * sensor_side_angle - sensor_middle_angle))

        attack_angle = self.configuration["Agent_Attack_Angle"]
        attack_range = self.configuration["Agent_Attack_Range"] * self.one_unit_in_px
        color = colors["Attack"]

        x1 = center_position[0] - attack_range
        x2 = center_position[0] + attack_range
        y1 = center_position[1] - attack_range
        y2 = center_position[1] + attack_range

        self.tkinter_root.canvas.create_arc(x1, y1, x2, y2, outline=color,
                                            start=angle - attack_angle / 2,
                                            extent=attack_angle)

    def draw_food(self, position):
        self.tkinter_root.canvas.create_image(position[0] * self.one_unit_in_px,
                                              self.area_in_px - position[1] * self.one_unit_in_px,
                                              anchor=CENTER, image=self.images["Food"])

    def prepare_canvas(self):

        self.one_unit_in_px = self.area_in_px / self.configuration["Area"]
        self.one_unit_in_px = round(self.one_unit_in_px)

        self.tkinter_root.canvas = Canvas(self.tkinter_root, width=1, height=1, bg="#bbbbbb")
        self.tkinter_root.canvas.configure(highlightthickness=0, borderwidth=0)
        self.tkinter_root.canvas.place(x=5, y=70, width=self.area_in_px, height=self.area_in_px)

        agent_image = Image.open("graphics/Agent.png")
        for i in range(0, 60):
            image = agent_image
            image = image.rotate(-(i / 60) * 360)
            image = image.resize((self.one_unit_in_px, self.one_unit_in_px), Image.ANTIALIAS)
            image = ImageTk.PhotoImage(image)

            self.agent_images.append(image)

        image = Image.open("graphics/Food.png")
        size = round(self.one_unit_in_px * self.configuration["Food_Diameter"])
        image = image.resize((size, size), Image.ANTIALIAS)
        self.images["Food"] = ImageTk.PhotoImage(image)

        image = Image.open("graphics/Highlight.png")
        size = round(self.one_unit_in_px * 0.5)
        image = image.resize((size, size), Image.ANTIALIAS)
        self.images["Highlight"] = ImageTk.PhotoImage(image)

        image = Image.open("graphics/Marker.png")
        size = round(self.one_unit_in_px * 1)
        image = image.resize((size, size), Image.ANTIALIAS)
        self.images["Marker"] = ImageTk.PhotoImage(image)

    def click_on_canvas(self, event):
        # print("click start");
        click_position = [event.x, self.area_in_px - event.y]
        for i in [0, 1]:
            click_position[i] = click_position[i] / self.one_unit_in_px

        closest_distance = 9999999999
        closest_agent_id = 0

        print(self.frame_information.state["agents"])

        for agent in self.frame_information.state["agents"]:
            distance = methods.calculate_distance(click_position, agent["position"])
            if distance < closest_distance:
                closest_distance = distance
                closest_agent_id = agent["id"]

        self.manager.selected_agent_id = closest_agent_id
        # print("click " + str(self.manager.selected_agent_id))

    def create_table(self):
        top_left_x = 810
        top_left_y = 70
        row_heights = 25
        cell_width = 100
        column_names = ["age", "health", "generation"]

        for row_id in range(0, self.table_rows):
            row = {}
            y = top_left_y + row_heights * row_id
            for column_id in range(0, 3):
                x = top_left_x + cell_width * column_id

                table_cell = tkinter.Button(self.tkinter_root, text="", fg="black")
                table_cell.pack()
                table_cell.place(x=x, y=y, width=cell_width, height=(row_heights))
                table_cell.bind("<Button-1>", lambda event, table_row_id=(row_id-1): self.select_table(table_row_id))


                row[column_names[column_id]] = table_cell

            self.table.append(row)

        self.table[0]["age"].configure(text="age")
        self.table[0]["health"].configure(text="health")
        self.table[0]["generation"].configure(text="generation")

    def select_table(self, table_row_id):
        agent_id = self.table_agent_ids[table_row_id]
        self.manager.selected_agent_id = agent_id
        print("a..", table_row_id)
        # item = self.tkinter_root.tree_view.item(self.tkinter_root.tree_view.focus())
        # i = int(item["text"])
        #
        # self.highlighted_agent_id = self.frame_information.agents[i].id

    def update_table(self):
        for row_id in range(1, self.table_rows):
            for key, cell in self.table[row_id].items():
                cell.configure(bg="#f0f0f0")
                cell.configure(text="")

        self.table_agent_ids = []
        table_row = 1
        for agent in self.frame_information.state["agents"]:
            if table_row >= self.table_rows:
                return
            self.table_agent_ids.append(agent["id"])
            row = self.table[table_row]

            health = '{0:.2f}'.format(agent["health"])

            row["age"].configure(text=agent["age"])
            row["health"].configure(text=health)
            row["generation"].configure(text=agent["generation"])

            if agent["id"] == self.manager.selected_agent_id:
                for key, cell in row.items():
                    cell.configure(bg="#fffb3a")
            else:
                for key, cell in row.items():
                    cell.configure(bg="#f0f0f0")

            table_row += 1

    def open_file_dialog(self, path):
        self.manager.speed = 20
        file_path = filedialog.askopenfilename(initialdir=path, title="Select save file",
                                               filetypes=(("EvoSim saves", "*.EvoSim"), ("all files", "*.*")))
        return file_path

    # noinspection PyUnusedLocal
    def toggle_pause(self, event):
        if self.manager.speed != 0:
            self.speed_before_pause = self.manager.speed
            self.manager.speed = 0
            self.draw_frame()
            # self.update_table()
        else:
            self.manager.speed = self.speed_before_pause

        self.tkinter_root.speed_slider.set(self.manager.speed)

    # noinspection PyUnusedLocal
    def slider_set_speed(self, event):
        slider_max = 1000
        real_max = 5000
        exponent = 2

        factor = 5000 / 1000**exponent

        value = self.tkinter_root.speed_slider.get()
        value = factor * value**exponent

        self.manager.speed = int(value)

    def alter_speed(self, delta):
        self.manager.speed += delta
        self.tkinter_root.speed_slider.set(self.manager.speed)

    # noinspection PyUnusedLocal
    def save(self, event):
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".EvoSim"
        path = self.manager.main_directory + "/saves"

        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        path += "/" + filename
        self.manager.save_path = path

    # noinspection PyUnusedLocal
    def load(self, event):
        path = self.manager.main_directory + "/saves"
        self.manager.load_path = self.open_file_dialog(path)

    # noinspection PyUnusedLocal
    def jump(self, event):
        self.manager.jump_to_tick = self.manager.tick_count + 1

    def quit_window(self):
        self.manager.exit_tasks = True
        self.tkinter_root.destroy()

    # noinspection PyUnusedLocal
    def save_window_position(self, event):
        if self.position_has_been_saved:
            return
        self.position_has_been_saved = True

        geometry = self.tkinter_root.geometry()
        geometry = geometry.split("+")
        print(geometry)

        methods.write_setting("WindowX", geometry[1])
        methods.write_setting("WindowY", geometry[2])

