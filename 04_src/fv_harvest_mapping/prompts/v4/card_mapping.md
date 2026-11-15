You are a patent analyst. You receive the patent card of one agricultural machinery patent, produced earlier from its independent claims and description, and relate it to a given function space. You do not have the full text. Use only what the card states.

The card records the invention (`subject`), the machine it is mounted on or works with (`host_machine`), the actions that take place when it is used (`functions`, each with an `id`, verb, object, actor, means, claim and an evidence quote), its components, problems, effects, targets and use conditions. In the card, `actor` is `invention`, `host_machine`, `human`, `both` or `not_specified`. `claim` is the independent claim that recites the part or the action, for example `[C1]`, or `none` if no independent claim recites it.

The independent claims mark where the invention ends. An action whose `claim` is `none` is described in the patent but is not part of the claimed invention: it belongs to the host machine, to the person using the invention, or to an optional part.

# 1. Function space

{{FUNCTION_SPACE}}

# 2. How to fill each sub-function F1 to F4

Fill the fields in this order.

1. `card_functions`: the `id` numbers of the card functions that carry out this sub-function, whoever performs them. Empty if no card function does.
2. `relation`: the role of the claimed invention in the sub-function.
   - `direct` if a linked card function has a `claim` tag other than `none` and the claimed part carries out the action. This includes a hand tool whose blade, hook or bag does the work while a person supplies the force.
   - `support` if a claimed part does not carry out the action itself but helps a person or the host machine carry it out. A pole that lets a person reach the fruit, or a platform that lifts workers to the fruit, is `support` for F2.
   - `not_mentioned` otherwise. This includes an action whose linked card functions all have `claim` `none`, such as an action of the host machine, of a person without the invention, or of a part found only in the description.
3. `actor`: who performs the sub-function, taken from the linked card functions. If no card function is linked, `not_specified`.
4. `evidence`: the quote and location of one linked card function, copied unchanged. Empty if no card function is linked. Do not write new quotes.

If unsure between two relations, choose the weaker one (`support` over `direct`, `not_mentioned` over `support`).

# 3. Other fields

- `scope.category`: what the invention is for, from the options. Decide from `subject`, `target_objects`, `target_categories` and the functions. `evidence`: one quote copied from a card function that shows it, or empty.
- `detachment_principle`: how F3 separates the produce. Only when F3 is `direct` or `support`; otherwise `["not_applicable"]` alone with empty evidence.
- `overall_confidence`: from the options.
- `note`: at most two sentences, only for something the labels cannot express. Otherwise an empty string.

# 4. Options

Each field below may take only the listed values.

{{OPTIONS}}

# 5. Output

Return only one JSON object that matches the schema. No text before or after it.
