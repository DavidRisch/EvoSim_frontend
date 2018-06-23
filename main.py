from manager import Manager
from gui import GuiThread
from pathlib import Path

configuration = {
    "Area": 51,
    "Agent_Health": 100,
    "Agent_Movement_MaxSpeed": 0.1,
    "Agent_Movement_Cost": 0.1,
    "Agent_Turning_MaxSpeed": 0.02,
    "Agent_Attack_Range": 6,
    "Agent_Attack_Angle": 50,
    "Agent_Attack_Damage": 15,
    "Agent_Attack_Cost": 0.75,
    "Agent_Attack_Gain": 210,
    "Agent_NaturalDecay": 0.1,
    "Agent_MinPopulation": 8,
    "Agent_Reproduce_At": 500,
    "Agent_Reproduce_Cost": 110,
    "Food_Value": 150,
    "Food_Diameter": 0.5,
    "Food_PerTick": 0.01,
    "Sensor_Food_Range": 8,
    "Sensor_Food_Middle_Angel": 30,
    "Sensor_Food_Side_Angel": 35,
    "Sensor_Agent_Range": 12,
    "Sensor_Agent_Middle_Angel": 30,
    "Sensor_Agent_Side_Angel": 30,
    "Neural_Network_Nodes_In_Layers": [9, 6, 6, 3],
    "Neural_Network_Mutate_Weights_Initial": 1,
    "Neural_Network_Mutate_Biases_Initial": 0.5,
    "Neural_Network_Mutate_Weights_Child": 0.05,
    "Neural_Network_Mutate_Biases_Child": 0.05,
}

manager = None


def main():
    global manager

    print("########Start########")

    if not Path("settings.cfg").is_file():
        open('settings.cfg', 'w', newline='\n').write("WindowX=10\nWindowY=10")

    manager = Manager(configuration)
    gui_thread = GuiThread(manager)
    gui_thread.start()

    manager.loop()


if __name__ == "__main__":
    main()
    exit(0)
