## Top-level function

F0. Mechanically harvest fruits and vegetables. The invention replaces manual harvesting with machine actions, or helps people harvest manually.
- Input: produce attached to the plant, or in the soil for root vegetables (material); mechanical work for detachment (energy); location and state of the target (signal).
- Output: produce detached from the plant and gathered (material).

## Sub-functions

| ID | Name | Action | Flow | Typical verbs |
|---|---|---|---|---|
| F1 | Identify harvestable produce | Determine the location and/or state (ripeness, size, quality, presence) of the produce to be harvested | signal | sense, detect, measure, track, process |
| F2 | Position harvesting mechanism | Move the part that detaches the produce to the target, or hold it there: moving a picking arm or head, steering a harvester along rows, adjusting the height of a cutting head | energy | position, guide, translate, rotate, stabilize |
| F3 | Detach or pick produce | Separate the produce from the plant, or free it from the soil for root vegetables, by cutting, twisting, pulling, shaking, suction or digging | material and energy | separate, divide, extract, remove |
| F4 | Collect and transfer produce | Gather the detached produce and/or move it onward: catching frame, bag, conveyor, bin, elevator | material | collect, contain, transfer, transport, store |

The verbs in the last column are typical, not decisive. Decide from what the action does to the produce or the mechanism.

Examples:
- A robot that finds fruit with a camera, moves its arm, cuts the stem and drops the fruit on a conveyor: F1 to F4 `direct`, actor `invention`.
- A pole picker with a cutting hook and a catching bag, operated by hand: F3 and F4 `direct`, actor `human`. F2 `support`, actor `human`, because the pole helps the person reach the fruit. F1 `not_mentioned`.
- A self-propelled platform that lifts workers who pick fruit by hand into a bin filler: F2 `support`, actor `invention`. F3 `not_mentioned`, actor `human`. F4 `direct`, actor `invention`.
- A grip-force controller for a robot gripper: F3 `support`, actor `host_machine`.
- A gripper-and-cutter end effector claimed on its own, mounted on a robot arm whose camera is only described: F3 `direct`, actor `invention`. F1 and F2 `not_mentioned`, actor `host_machine`, because the camera and the arm are not in the independent claims.
