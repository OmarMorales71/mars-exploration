# **Mars Mission Report**
## **Mission Overview**

The Mars mission aims to explore the Martian terrain while investigating its mineral composition, monitoring atmospheric dust density, surveying potential subsurface water traces, and performing high-resolution aerial imaging. The primary priorities of this mission are to complete goals with higher priority first.

## **Mission Strategy**

To ensure efficient operation, each goal has been assigned a rover or drone based on their compatibility with the terrain type. The following is a detailed explanation of how each goal will be completed:

### **Goal 2: Survey potential subsurface water traces in icy terrain at nodes N41 and N42.**
This goal could not be assigned to any vehicle due to its terrain-incompatibility with "icy" (rover_0, rover_1, rover_2, rover_3, rover_4). As a result, this goal will not be completed.

### **Goal 4: Monitor atmospheric dust density in sandy terrain at node N18.**
*   Rover 0 and Rover 1 have no path to reach N18 and return; therefore, they cannot complete this task.
*   Drone 0 was assigned to complete this goal as it offers the highest camera resolution and altitude among efficient candidates, while maintaining a short flight time.

    -   Drone 0 will start at location `N8`.
    -   It will follow path: `["N8", "N70", "N92", "N18", "N92", "N70", "N8"]` to reach node N18.
    -   After completing the task, it will return to its starting point.

### **Goal 1: Investigate mineral composition in rocky terrain near nodes N14 and N27.**
*   Rover 0 and Rover 1 have no path to reach N14/N27 and return; therefore, they cannot complete this task.
*   Drone 4 was assigned to complete this goal as it offers the most balanced utilization across goals with adequate imaging quality and a feasible flight duration.

    -   Drone 4 will start at location `N52`.
    -   It will follow path: `["N52", "N14", "N13", "N18", "N92", "N27", "N53", "N63", "N52"]` to reach nodes N14 and N27.
    -   After completing the task, it will return to its starting point.

### **Goal 3: Perform high-resolution aerial imaging of crater terrain at node N66.**
*   Drone 3 was assigned to complete this goal as it maintains balanced utilization across goals with adequate imaging quality and a feasible flight duration.

    -   Drone 3 will start at location `N74`.
    -   It will follow path: `["N74", "N63", "N53", "N66", "N53", "N63", "N74"]` to reach node N66.
    -   After completing the task, it will return to its starting point.

### **General Operational Constraints and Risks**

*   Rovers must avoid prolonged operation when energy falls below 10%.
*   Drones are required to complete all flights within their maximum operational range.
*   Satellites must periodically relay telemetry data through the primary communication node.
*   No autonomous vehicle may enter regions marked as geologically unstable or environmentally hazardous.

### **Scientific Goals that Could Not be Completed**

Unfortunately, Goal 2: Survey potential subsurface water traces in icy terrain at nodes N41 and N42., could not be completed due to terrain-incompatibility.