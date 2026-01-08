# Mars Mission Report
## Mission Overview

The Mars mission aims to collect scientific data from various terrain types on the Martian surface. The primary objectives are to analyze ice composition in icy terrain, measure radiation levels in sandy terrain, and capture panoramic images of crater terrain. Given the limited resources available, we must prioritize tasks effectively to maximize efficiency.

## Mission Strategy
The mission strategy consists of several key steps that aim to achieve the scientific goals outlined in the mission summary while adhering to the constraints and avoiding risks.

### Goal 1: Analyze Ice Composition at Nodes N22 and N23

1. Rover_3 begins its journey from node N34, heading towards N5 (medium priority, distance 36.0 km).
2. At N5, rover_3 takes a short break to recharge before proceeding to the icy terrain.
3. Rover_3 reaches nodes N22 and N23, conducting the necessary ice composition analysis while minimizing energy consumption by using the shortest path between these points.
4. The drone (drone\_0) is dispatched from node N8, flying over the region of interest to capture high-resolution images of the terrain for further analysis.

### Goal 2: Measure Radiation Levels at Node N90

1. Rover_1 travels directly from its starting location at N16 to node N90 (shortest distance, low energy).
2. Upon arrival, rover_1 measures radiation levels, providing critical data for future missions.
3. Drone\_2 flies over the area, capturing images of the terrain and potentially providing additional insights.

### Goal 3: Capture Panoramic Images at Node N5

- **Note:** Initially, we aimed to have this task assigned to a rover due to its relatively lower priority. However, given the constraints on rover energy and the specific requirements for crater terrain imaging (which can be more efficiently captured by drones), this goal is reassigned.
1. Drone\_3 flies from node N74 towards node N5 (medium priority, distance 8.0 km).
2. Upon arrival, drone\_3 captures panoramic images of the terrain at N5.

### Goal 4: Collect Subsurface Samples near Nodes N12, N45, and N78

- **Note:** Initially assigned to rover_1 but reassigned for efficiency.
1. Rover_4 travels from its starting location at N16 towards nodes N12, N45, and N78 (longest distance, medium priority).
2. Upon arrival at each node, rover_4 collects subsurface samples while ensuring it maintains enough energy reserves.

### General Operational Constraints

- **Rover Energy Levels:** All rovers are tasked with maintaining energy levels above 30% to avoid forced recharging during critical operations.
- **Drone Flight Time:** Drones must return to base after 25 minutes of flight to recharge, adhering to mission constraints.
- **Communication with Base Station N1:** Satellites maintain communication with the base station every 2 hours.

### Operational Risks

- **Unstable Terrain at Node N60:** Avoided due to initial path selection by rovers and drones.
- **High Radiation Zone at Node N88:** Assessed and navigated around by rover_4.
- **Frequent Dust Storms at Node N33:** Anticipated but not directly impacting the mission given the chosen paths.


The mission strategy ensures that all high-priority goals are addressed efficiently by both rovers and drones, with a balanced approach to energy consumption and communication. The drone’s capabilities are utilized for tasks requiring aerial perspective or high-resolution imaging, while rovers tackle terrestrial operations where necessary.