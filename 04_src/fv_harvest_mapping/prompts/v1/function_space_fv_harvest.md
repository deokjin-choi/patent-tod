## Top-level function

F0. Mechanically harvest fruits and vegetables. The invention replaces manual harvesting with machine actions, or assists manual harvesting with a machine.
- Input: produce attached to the plant, or in the soil for root vegetables (material); mechanical work for detachment (energy); location and state of the target (signal).
- Output: produce detached from the plant and gathered (material).

## Sub-functions

| ID | Name | Action | Flow | Typical card verbs |
|---|---|---|---|---|
| F1 | Identify harvestable produce | Determine the location and/or state (ripeness, size, quality, presence) of the produce to be harvested | signal | sense, detect, measure, track, process |
| F2 | Position harvesting mechanism | Move the harvesting mechanism to the target, or hold it there: arm motion, guiding a vehicle along rows, adjusting the height of a picking head, an operator holding a pole | energy | position, guide, translate, rotate, stabilize |
| F3 | Detach or pick produce | Separate the produce from the plant, or lift it from the soil for root vegetables, by applying mechanical force: cutting, twisting, pulling, shaking, suction, digging | material and energy | separate, remove, extract, divide |
| F4 | Collect and transfer produce | Gather the detached produce and/or move it to a next location: catching frame, bag, conveyor, bin, elevator | material | collect, contain, transfer, transport, store |

The verbs in the last column are typical, not decisive. Decide from what the action does to the produce or the mechanism.

Examples of `support`: grip-force control that improves detachment by a robot gripper (F3 support); a telescopic pole or a work platform that helps an operator reach the fruit (F2 support); a ripeness indicator shown to a human picker (F1 support).

## Scope

`in_scope` is `yes` if the invention is for harvesting fruits or vegetables (including root vegetables), or is a component or accessory specifically for such harvesting. It is `no` if the invention targets only grain, cotton, forage, lawn, tree nuts or tobacco, or a task other than harvesting (pruning, thinning, leaf removal, spraying, post-harvest processing only). It is `unclear` otherwise.

## Detachment principle

`detachment_principle` records how F3 separates the produce. Fill it only when F3 is `direct` or `support`; otherwise use `["not_applicable"]` alone with empty evidence.
