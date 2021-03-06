import matplotlib.pyplot as plt
import numpy as np
from scripts.world import World
from scripts.mapreader import viz_map
import gc
import keyboard
import os

#Region[Red] Save paths

if not os.path.exists('output'):
        os.makedirs('output')
output_path = './output'

#EndRegion

#Region[Cyan] Main

run_dict = { 0 : '|', 1 : '/', 2 : '-', 3 : '\\', 4 : '|', 5 : '/', 6 : '-', 7 : '\\' }

def main(HEADLESS=False, SAVING=False):

    gc.enable()
    escape = False
    i=0

    world = World('data/battleground.map', n_robots=10, spawn_radius=30)

    print("| World generated, entering simulation")
    map_size = np.sum(world.worldMap != '@')

    fig, axes = plt.subplots(2,6, figsize=(1,3))
    gs = axes[0,3].get_gridspec()
    for row in axes:
        for ax in row[3:]:
            ax.remove()
    worldax = plt.subplot(gs[:,3:])
    worldax.set_axis_off()
    fig.tight_layout()

    if not(HEADLESS):
        plt.ion()
        for row in axes:
            for ax in row:
                ax.set_axis_off()

    while not(escape) and (HEADLESS or plt.get_fignums()) and i < 3000:
        try:
            escape = keyboard.is_pressed("shift+esc")
        except:
            escape = False
        if (i%10 == 0):
            print('| Simulation running, press SHIFT+ESCAPE to end - Step {} |{}|'.format(i, run_dict[(i//10)%8]), end='\r')
        world.step(fig, axes, worldax, HEADLESS, i)

        comp = []
        for robot in world.robots.values():
            comp.append(robot.exploration_history[-1]/map_size)

        i += 1
    
    print()

    if not(HEADLESS):
        plt.ioff()

    if SAVING:
        plt.close()
        
        viz_map(world.worldMap, "Global world map", os.path.join(output_path, "world.png"), show=not(HEADLESS))
        
        completion = {}
        
        for robot in world.robots.values():
            
            save_path = os.path.join(output_path, "map_robot_{}_.png".format(robot.id))
            fig_name = "Map of the robot {} after {} steps".format(robot.id, i)
            viz_map(robot.dynamicMap.map, fig_name, save_path, show=not(HEADLESS))
            completion[robot.id] = np.array(robot.exploration_history)/map_size

        for rid, hist in completion.items():
            np.random.seed(rid)
            color = np.random.rand(3)/2.0
            plt.plot(hist, color=color)
        if (len(completion) <= 15):
            plt.legend(labels=completion.keys(), ncol=max(1,len(completion)//5))
        plt.suptitle('Completion of the maps over time')
        plt.savefig(os.path.join(output_path, 'completion.png'))
        if not(HEADLESS):
            plt.show()

    print("| Simulation ended. Check robot maps in output folder.")
#EndRegion

main()