# /// script
# dependencies = [
#     "marimo==0.24.2",
#     "yggdrisil==0.1.0",
# ]
# requires-python = ">=3.13"
#
# [tool.uv.sources]
# yggdrisil = { git = "https://github.com/McClain-Thiel/yggdrisil.git", rev = "1fed375d8f8286b08d8a3d58e5dec1f477f9651a" }
# ///

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from yggdrisil import (
        Decision,
        EvaluationResult,
        Objective,
        Proposal,
        RunLimits,
        Runner,
        SQLiteStateGraph,
        evaluate_cached,
        stable_hash,
    )

    return (
        Decision,
        EvaluationResult,
        Objective,
        Proposal,
        RunLimits,
        Runner,
        SQLiteStateGraph,
        evaluate_cached,
        mo,
        stable_hash,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Yggdrisil + Minimal E. coli

    ![Yggdrisil](https://bavipower.com/cdn/shop/articles/1_1024x1024.jpg?v=1521033281)

    ## The idea
    You can imagine a lot of scientific exploration or optimization as a state search graph or tree (hence, Yggdrisil) where modified versions of an existing state are downstream nodes and the modifications are edges. These modifications are candidates, not guaranteed improvements. Humans are often pretty good at intuiting what modification to make to get a more optimized version but are constrained by how many states they can explore. Computers can use simple algorithms to explore a massive number of states. Humans can be efficient in terms of the number of states visited, and machines are good at applying brute force to a massive number of states. The idea is to combine informed proposals with automated search and test whether this finds better states with fewer expensive evaluations.

    By building a framework where we can use an "agent", or an LLM with access to some tools, to propose these modifications and then receive feedback from the state, we might be able to get the best of both worlds in terms of efficiency and being able to apply large amounts of compute to solving the problem.


    **Slightly more formally:**
    So if a scientist is trying to build or optimize something, they might have an initial **state** $S_0$, a current state $S$, and a set of **actions** $A(S)$ they can perform. An action $a \in A(S)$ creates a new candidate state:

    $$
    S' = T(S, a).
    $$

    You can imagine applying this over and over again and forming a graph or tree of states. The leaves mark the ends of the paths explored so far; they are not necessarily the best states.

    Here, we will show the simple framework we've built to do this and an application to E. coli genome minimization.

    ## The Yggdrisil Framework

    We built Yggdrisil, a Python library, to test this. The library includes a bunch of very flexible classes and search algorithms to make this easy to implement. Here are the primary building blocks with examples we will assemble into a minimal working run.

    To stick with the theme of the package name, we can use an example inspired by [DnD](https://www.dungeonsanddragons.com/).

    ### Example: Optimizing Your Pack

    I don't want to get too into the rules of DnD here, but this should be pretty easy to conceptualize without too much background. You can carry a maximum amount of weight; let's call it 10 units. You just broke into a dragon's den or whatever and are now making your escape. You want to maximize the value of items you're taking with you without exceeding your maximum carrying capacity.

    We define the items with values and weights below. Although this is a small combinatorial problem that we could solve directly, you can also imagine how it can be formulated as a state search problem. We'll come back to an example that's less trivial later.
    """)
    return


@app.cell
def packing_catalog(mo):
    gear = {
        "moonblade": {"name": "Moonblade", "weight": 6, "value": 12},
        "shield": {"name": "Oak shield", "weight": 5, "value": 8},
        "spellbook": {"name": "Spellbook", "weight": 4, "value": 10},
        "rope": {"name": "Silken rope", "weight": 3, "value": 4},
        "rations": {"name": "Trail rations", "weight": 2, "value": 3},
        "potion": {"name": "Healing potion", "weight": 1, "value": 5},
    }
    pack_capacity = 10

    mo.ui.table(
        [{"Item": item["name"], "Weight": item["weight"], "Value": item["value"]}
         for item in gear.values()],
        selection=None, pagination=False, show_search=False,
        show_column_summaries=False, show_data_types=False,
    )
    return gear, pack_capacity


@app.cell(hide_code=True)
def packing_state_description(mo):
    mo.md(r"""
    **State — what have we packed?**

    A state $S$ is the set of item IDs in the backpack; given the way we've structured the items, its value and weight are calculable. We can start with an empty bag defined simply. The library will wrap the object to make it work in the framework.
    """)
    return


@app.cell
def packing_state():
    initial_pack = frozenset()
    initial_pack
    return (initial_pack,)


@app.cell(hide_code=True)
def packing_action_description(mo):
    mo.md(r"""
    **Action — what do we add?**

    An action $a$ is the ID of one item to add. The string `"potion"` proposes packing the healing potion. An item can be added only once.
    """)
    return


@app.cell
def packing_action():
    example_action = "potion"
    example_action
    return (example_action,)


@app.cell(hide_code=True)
def packing_transition_description(mo):
    mo.md(r"""
    **Transition — how does the backpack change?**

    Our transition is simply adding the item to the pack. It keeps the existing items and adds one new item. We, as users, define the transition: a function that takes a state and an action and returns a new state. Because a `frozenset` is immutable, we must keep and return the result of `union`.
    """)
    return


@app.cell
def packing_transition(example_action, initial_pack):
    def add_item(pack: frozenset[str], item: str) -> frozenset[str]:
        if item in pack:
            raise ValueError(f"Already packed: {item}")
        # A frozenset is immutable, so union returns the new state.
        new_pack = pack.union({item})
        return new_pack


    add_item(initial_pack, example_action)
    return (add_item,)


@app.cell(hide_code=True)
def packing_problem_description(mo):
    mo.md(r"""
    **Problem — define the possible states and transitions.**

    The problem supplies the initial state, `apply`, and `state_key`. `weight` and `value` sum the item properties. `legal_actions` lists every item we have not packed yet, including items that would make the backpack too heavy.

    Unknown items and duplicate additions are still invalid actions. An overweight backpack is a valid candidate state: we can assemble it and then discover that we cannot lift it.

    Packing a potion and then a spellbook reaches the same state as packing them in the opposite order. Hashing the set gives both paths the same state ID, so the graph can merge them.
    """)
    return


@app.cell
def packing_problem(add_item, gear, initial_pack, stable_hash):
    class PackingProblem:
        def __init__(self, items):
            self.items = items
            self.initial_state = frozenset()

        def state_key(self, state):
            return stable_hash(state)

        def weight(self, state):
            return sum(self.items[item]["weight"] for item in state)

        def value(self, state):
            return sum(self.items[item]["value"] for item in state)

        def apply(self, state, action):
            if action not in self.items:
                raise ValueError(f"Unknown item: {action}")
            return add_item(state, action)

        def legal_actions(self, state):
            return [item for item in self.items if item not in state]


    packing_problem = PackingProblem(gear)
    packing_problem.legal_actions(initial_pack)
    return (packing_problem,)


@app.cell(hide_code=True)
def packing_evaluator_description(mo):
    mo.md(r"""
    **Evaluator — can we lift it?**

    We can put items into the backpack before knowing whether it will be usable. The evaluator reports its weight, raw item value, and whether we can carry it. A failed carrying check returns **"I can't lift it"** as feedback; the state remains in the graph.

    Here `measure` is just a cheap calculation, shared by the objective and the evaluator. `evaluate` wraps those measurements in an `EvaluationResult` that Yggdrisil can store and cache. The example below tries the moonblade and shield together: 11 weight units in a 10-unit capacity.
    """)
    return


@app.cell
async def packing_evaluator(EvaluationResult, pack_capacity, packing_problem):
    class PackEvaluator:
        name = "adventurers-pack"
        version = "2"

        def __init__(self, problem, capacity):
            self.problem = problem
            self.capacity = capacity
            self.config = {"items": problem.items, "capacity": capacity}

        def measure(self, state):
            weight = self.problem.weight(state)
            can_carry = weight <= self.capacity
            return {
                "weight": weight,
                "value": self.problem.value(state),
                "can_carry": can_carry,
                "feedback": "I can carry it" if can_carry else "I can't lift it",
            }

        async def evaluate(self, state):
            return EvaluationResult(metrics=self.measure(state))


    packing_evaluator = PackEvaluator(packing_problem, pack_capacity)
    (await packing_evaluator.evaluate(frozenset({"moonblade", "shield"}))).metrics
    return (packing_evaluator,)


@app.cell(hide_code=True)
def packing_objective_description(mo):
    mo.md(r"""
    **Objective — what counts as better?**

    We want the highest-value backpack we can carry. The evaluator reports what happened; the objective turns that evidence into a ranking:

    $$
    f(S) = \begin{cases}
    \sum_{i \in S} v_i, & \text{if we can carry } S, \\
    -\infty, & \text{otherwise}.
    \end{cases}
    $$

    An overweight pack keeps its raw value and feedback in the graph, but its objective score prevents it from being selected as our best usable pack. Scoring a state poorly does not block its creation or remove it.

    There is no predefined winning score. We leave `goal_reached` unset and search until the budget is used or there are no more proposals. This toy objective calls the evaluator's cheap `measure` method directly; an expensive experiment would need a deliberate evaluation and caching schedule.
    """)
    return


@app.cell
def packing_objective(Objective, packing_evaluator):
    def score_pack(state):
        metrics = packing_evaluator.measure(state)
        return metrics["value"] if metrics["can_carry"] else float("-inf")


    packing_objective = Objective(score=score_pack, maximize=True)
    packing_objective.score(frozenset({"potion", "spellbook"}))
    return (packing_objective,)


@app.cell(hide_code=True)
def packing_proposal_description(mo):
    mo.md(r"""
    **Proposal and Decision — record a choice.**

    A `Proposal` identifies a parent state and an action. A `Decision` groups the proposals made by one policy operation. This example proposes adding the healing potion to the empty backpack. The live policy will construct decisions in the same way.
    """)
    return


@app.cell
def packing_proposal(
    Decision,
    Proposal,
    example_action,
    initial_pack,
    packing_problem,
):
    example_proposal = Proposal(
        parent_id=packing_problem.state_key(initial_pack),
        action=example_action,
    )
    example_decision = Decision(
        role="pack-item",
        selected_state_ids=[example_proposal.parent_id],
        proposals=[example_proposal],
    )
    example_decision
    return


@app.cell(hide_code=True)
def packing_policy_description(mo):
    mo.md(r"""
    **Policy — choose which backpack to explore next.**

    This is the biggest deviation from our intended agentic example. We want an agent—an LLM with tools—to make the proposals, but we use a deterministic policy here to keep the example simple and cheap to run locally. Both kinds of policy are supported by the framework.

    An LLM version can reuse Yggdrisil's `NavigatorExplorerPolicy`: the **navigator** selects an existing state, and the **explorer** uses tools and proposes actions. The inherited `step()` method returns the same `Decision` and `Proposal` objects as our local policy.

    ```python
    from yggdrisil.agents import NavigatorExplorerPolicy
    from yggdrisil.agents.pydantic_ai import make_explorer, make_navigator


    def inspect_pack(items: list[str]) -> dict[str, int | bool | str]:
        "Measure a candidate pack, including packs that are too heavy."
        unknown = set(items) - packing_problem.items.keys()
        if unknown:
            raise ValueError(f"Unknown items: {sorted(unknown)}")
        if len(items) != len(set(items)):
            raise ValueError("Each item can only be packed once")
        return packing_evaluator.measure(frozenset(items))


    class SmartPackingPolicy(NavigatorExplorerPolicy):
        def __init__(self, model: str):
            navigator = make_navigator(
                model,
                instructions=(
                    "Choose one existing frontier state to explore. "
                    "Use the explorer's saved notes to guide your choice. "
                    "Do not invent state IDs."
                ),
            )
            explorer = make_explorer(
                model,
                str,  # Each action is a single item ID.
                tools=[inspect_pack],
                instructions=(
                    f"Available items (ID, weight, value): {gear}. "
                    "Inspect the current pack and try candidate packs with inspect_pack. "
                    "Return item IDs to add, each as an independent one-item addition "
                    "to the current state, never an item already in the pack. "
                    "Heavy packs are allowed proposals; use the feedback to judge them. "
                    "Include a short note describing what you tried and learned."
                ),
            )
            super().__init__(
                navigator=navigator,
                explorer=explorer,
                goal=f"Maximize loot value while carrying at most {pack_capacity} weight.",
                max_requests=1,
            )
    ```

    `inspect_pack` is the explorer's tool. It reports value, weight, and "I can't lift it" feedback without blocking overweight candidates. Tool probes are recorded in the explorer's decision; they only become graph states if the explorer proposes the corresponding action and the runner applies it.

    This block is illustrative and is not executed by the notebook. To use it, install the `yggdrisil[agents]` extra, configure your provider credentials outside the notebook, instantiate `SmartPackingPolicy(model="provider:model-name")` with a real model identifier, and pass it as the runner's `policy`. The problem, evaluator, objective, and graph stay the same. The adapter records the explorer's tool calls and notes for inspection; those notes help guide later navigation. This does not make the runner automatically schedule evaluations.

    Our best-first policy prioritizes the highest-scoring expandable backpack and proposes every item not already inside it. Some children will be too heavy. They are recorded, evaluated, and given a low score, rather than being filtered out before we try them.

    Other branches stay available. This baseline can eventually expand overweight states too; it does not prune them. That is deliberately simple: a more informed policy could use the feedback to avoid wasting further effort on those branches. Each step expands one parent, and alphabetical ordering breaks ties reproducibly.
    """)
    return


@app.cell
def packing_policy(Decision, Proposal, packing_objective, packing_problem):
    class PackingPolicy:
        def __init__(self, problem, objective):
            self.problem = problem
            self.objective = objective

        async def step(self, graph, status):
            candidates = [
                node for node in graph.frontier()
                if self.problem.legal_actions(node.state)
            ]
            if not candidates:
                return []
            parent = max(candidates, key=lambda node: (
                self.objective.score(node.state), tuple(sorted(node.state)),
            ))
            return [Decision(
                role="pack-item",
                selected_state_ids=[parent.state_id],
                proposals=[
                    Proposal(parent_id=parent.state_id, action=item)
                    for item in self.problem.legal_actions(parent.state)
                ],
            )]


    packing_policy = PackingPolicy(packing_problem, packing_objective)
    return (packing_policy,)


@app.cell(hide_code=True)
def packing_limits_description(mo):
    mo.md(r"""
    **RunLimits — bound the search.**

    Six items give $2^6 = 64$ distinct sets, including the empty pack and overweight packs. We cap the graph at 64 states and use the slider to limit how many parents we expand. Each slider change starts a fresh, deterministic search. Try **0**, **1**, and **2** to see the first branches and an overweight outcome, then increase the budget.
    """)
    return


@app.cell
def packing_budget_control(mo):
    packing_step_budget = mo.ui.slider(
        start=0,
        stop=64,
        step=1,
        value=64,
        label="Maximum backpacks to expand",
        show_value=True,
    )
    packing_step_budget
    return (packing_step_budget,)


@app.cell
def packing_limits(RunLimits, packing_step_budget):
    packing_limits = RunLimits(
        max_steps=packing_step_budget.value,
        max_states=64,
    )
    packing_limits
    return (packing_limits,)


@app.cell(hide_code=True)
def packing_runner_description(mo):
    mo.md(r"""
    **State graph and Runner — run the search.**

    The runner applies proposals and records each resulting state, including backpacks we cannot lift. The objective ranks them during the search. Different packing orders reuse the same state.

    After the run, we explicitly call `evaluate_cached` for every discovered state to persist its full feedback. The objective and these reports use the same cheap measurement, so their results agree. The runner itself does not automatically invoke the evaluator.

    We save a fresh SQLite graph for each run so the built-in inspector can open it. Each run is saved in a `runs/` directory beside the notebook.
    """)
    return


@app.cell
async def packing_run(
    Runner,
    SQLiteStateGraph,
    evaluate_cached,
    mo,
    packing_evaluator,
    packing_limits,
    packing_objective,
    packing_policy,
    packing_problem,
):
    from uuid import uuid4

    # A fresh database keeps slider reruns independent and preserves earlier runs.
    packing_graph_path = (
        mo.notebook_dir() / "runs" / f"packing-{uuid4().hex}.sqlite"
    )
    with SQLiteStateGraph(packing_graph_path) as _graph:
        packing_result = await Runner(
            problem=packing_problem,
            policy=packing_policy,
            graph=_graph,
            limits=packing_limits,
            objective=packing_objective,
        ).run()
        packing_states = _graph.states()
        packing_evaluations = {}
        for _node in packing_states:
            packing_evaluations[_node.state_id] = await evaluate_cached(
                _graph, _node.state_id, packing_evaluator,
            )
        packing_best = _graph.get_state(packing_result.best_state_id)
        packing_evidence = packing_evaluations[packing_best.state_id]
        packing_edges = _graph.edges()
        packing_decisions = _graph.decisions(packing_result.run_id)
    return (
        packing_best,
        packing_edges,
        packing_evaluations,
        packing_evidence,
        packing_result,
        packing_states,
    )


@app.cell(hide_code=True)
def packing_results_description(mo):
    mo.md(r"""
    **Inspect the result.**

    The library has a web-based inspector where you can see the agent traces, graph, and evaluations, but to keep this easy to read on the web, we'll use a simple graphic. Green nodes are carryable backpacks. Red nodes are recorded candidates with **"I can't lift it"** feedback. The diagram shows one route to the best carryable pack and one route to the first overweight pack discovered. The table underneath contains every evaluated state, including the unsuccessful candidates.
    """)
    return


@app.cell(hide_code=True)
def packing_live_output(
    gear,
    initial_pack,
    mo,
    pack_capacity,
    packing_best,
    packing_edges,
    packing_evaluations,
    packing_evidence,
    packing_problem,
    packing_result,
    packing_states,
):
    _by_id = {node.state_id: node for node in packing_states}
    _metrics = {state_id: record.metrics for state_id, record in packing_evaluations.items()}
    _incoming = {}
    for _edge in packing_edges:
        _incoming.setdefault(_edge.child_id, _edge)
    _heavy = [node for node in packing_states if not _metrics[node.state_id]["can_carry"]]
    _targets = [packing_best]
    if _heavy:
        _targets.append(_heavy[0])
    _root_id = packing_problem.state_key(initial_pack)
    _shown_ids = {_root_id}
    _shown_edges = {}
    for _target in _targets:
        _current = _target.state_id
        _shown_ids.add(_current)
        while _current != _root_id:
            _edge = _incoming[_current]
            _shown_edges[_edge.edge_id] = _edge
            _shown_ids.add(_edge.parent_id)
            _current = _edge.parent_id
    _node_names = {
        node.state_id: f"n{index}" for index, node in enumerate(packing_states)
        if node.state_id in _shown_ids
    }
    _lines = ["flowchart TD"]
    for _state_id, _name in _node_names.items():
        _measurement = _metrics[_state_id]
        _feedback = "Can carry" if _measurement["can_carry"] else "Can't lift"
        _style = "carryable" if _measurement["can_carry"] else "overweight"
        _lines.append(
            f'    {_name}(("{_measurement["weight"]} / {pack_capacity} weight'
            f'<br/>{_measurement["value"]} value<br/>{_feedback}")):::{_style}'
        )
    for _edge in _shown_edges.values():
        _item_name = gear[_edge.action]["name"]
        _lines.append(
            f'    {_node_names[_edge.parent_id]} -->|"Add {_item_name}"| {_node_names[_edge.child_id]}'
        )
    _lines.extend([
        "classDef carryable fill:#d9edc3,stroke:#517a35,color:#172b12",
        "classDef overweight fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d",
    ])
    _rows = [
        {
            "Step": node.created_step,
            "Items": ", ".join(gear[item]["name"] for item in sorted(node.state)) or "Empty pack",
            "Weight": _metrics[node.state_id]["weight"],
            "Value": _metrics[node.state_id]["value"],
            "Feedback": _metrics[node.state_id]["feedback"],
        }
        for node in packing_states
    ]
    _reason = {
        "no_proposals": "all expandable backpacks have been explored",
        "max_steps": "the expansion budget was used",
        "max_states": "the state limit was reached",
    }[packing_result.stop_reason]
    _contents = ", ".join(gear[item]["name"] for item in sorted(packing_best.state)) or "Empty backpack"
    mo.vstack([
        mo.md(
            f"**Best carryable backpack: {_contents}**\n\n"
            f"**{packing_evidence.metrics['value']} value**, "
            f"**{packing_evidence.metrics['weight']} / {pack_capacity} weight**. "
            f"Recorded **{len(packing_states) - len(_heavy)} carryable** and "
            f"**{len(_heavy)} overweight** states, connected by {len(packing_edges)} edges. "
            f"Stopped because {_reason}."
        ),
        mo.mermaid("\n".join(_lines)),
        mo.ui.table(_rows, selection=None, pagination=True, page_size=8,
                    show_column_summaries=False, show_data_types=False,
                    label="All evaluated backpacks"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Other Features of the Library
    There are some other features of the library that make it useful for this problem.

    - **Save and resume a search.** States, transitions, evaluations, and run progress are stored in SQLite, so we can return to a long search without starting over.
    - **Merge equivalent states.** Different sequences of actions can reach the same result. The graph merges states with the same identity while keeping the different paths that reached them.
    - **Reuse expensive evaluations.** Cached results are tied to the state and the evaluator's name, version, and configuration, so we can reuse a previous measurement when those match.
    - **Use several evaluators.** We can store several kinds of evidence about the same state and define separately how the objective ranks it. The application decides when to run these evaluations.
    - **Swap search policies.** Random search, best-first search, and LLM-based policies can use the same problem and graph interfaces, making it easier to compare how they choose candidates.
    - **Keep a record of decisions and attempts.** Decisions can include the model, input context, tool calls, and output. Each proposal records whether it created a transition, reused one, failed, or was skipped.
    - **Inspect the search as it runs.** The built-in web viewer shows the graph and lets us click through states, evaluations, decisions, and transitions.
    - **Export the results.** JSON, GraphML, and NetworkX exports let us analyze the graph or build our own plots after a run.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Minimizing E. coli

    For a more realistic use case, let's think about minimizing an E. coli genome. You can start with something to be optimized; let's say we start with MG1655. Then we want to minimize the genome ([why?](https://link.springer.com/chapter/10.1007/978-981-19-7911-8_2)). We can define the root node as the full MG1655 genome. In the experiment code, each state records the set of genes deleted from that reference, so the root has an empty deletion set. To optimize, we can think about what genes we want to delete, then define each set of genes to delete as an action on an edge, and each resulting genome as another state node.

    For the 20-gene-capped experiments described below, an action deletes a gene or set of genes, up to 20 per transition. The objective is to minimize the number of remaining genes while passing a model-based growth gate. In the reference arm, that means positive FBA growth and RBA feasibility at a growth floor of 0.1 h⁻¹.

    This is where the framework and agent earn their pay. Genome minimization, as you might expect, is a much harder task for several reasons. Biology is filled with complex networks of genes, and the effects of combining deletions can be hard to predict. Some single-gene deletions are lethal under the chosen growth conditions. Other deletions are tolerated individually but become lethal in combination, a phenomenon known as synthetic lethality. This means that genes we can delete separately cannot always be deleted together. [Côté et al. (2016)](https://doi.org/10.1128/mBio.01714-16) provide an E. coli example of these genetic interactions.

    We need to be able to navigate this network of candidate states (combinations of genes) and evaluate which combinations might be viable (model predictions alone cannot establish viability in a living cell) and which are not. As in the backpack example, a candidate can be a valid state representation even if it fails the viability evaluation.

    Experimental measurements can be noisy, and even a deterministic model is an imperfect proxy for a living cell. We'll come back to this. The total number of combinations is also absolutely massive: $n$ genes give $2^n$ possible subsets. For scale, taking approximately $n = 4{,}200$ protein-coding genes gives roughly $2.1 \times 10^{1264}$ subsets. The precise gene count depends on the annotation, and the actual search space depends on which genes we allow ourselves to delete. Brute-force exploration is infeasible at this scale. Existing algorithms tackle the problem using heuristics and models; we want to test whether agent-guided search can make better use of a limited evaluation budget.

    ### Related work

    This is, of course, not the first attempt at E. coli minimization, nor the first use of agents to search over candidate designs. The relevant work falls into three groups: genome reduction, optimization under limited evaluation budgets, and agentic search.

    #### Genome Reduction

    Experimental work by [Pósfai et al. (2006)](https://doi.org/10.1126/science.1126439) showed that planned deletions could produce reduced E. coli genomes while preserving useful growth and protein-production properties under the tested conditions. On the computational side, [Rees-Garbutt et al. (2020)](https://www.nature.com/articles/s41467-020-14545-0) introduced Minesweeper and GAMA, which alternate candidate design and whole-cell simulation to find reduced Mycoplasma genitalium genomes. These are direct precedents for treating genome minimization as a search problem, although their organism and evaluator differ from our proposed E. coli example.

    [Gherman et al. (2025)](https://doi.org/10.1016/j.cels.2025.101392) provide an especially close domain comparison: they combine an adapted Minesweeper algorithm, an E. coli whole-cell model, and a machine-learning surrogate to accelerate genome reduction.

    [Shcherbakova et al. (2025, preprint v2)](https://www.biorxiv.org/content/10.1101/2024.10.22.619620v2) take a generative-model approach in *Designing minimal E. coli genomes using variational autoencoders*. They train VAEs on E. coli pangenome data, modify the loss to encourage smaller gene sets, and computationally evaluate sampled designs with an E. coli whole-cell model. This connects directly to our proposal-policy comparison: a learned generative model could propose candidate gene sets or guide deletion choices within Yggdrisil, alongside simple algorithms and LLM-based policies.

    #### Optimization

    Optimization is a major focus of both maths and machine-learning research, but several papers address either structurally similar problems or optimization in similar domains. [Jones, Schonlau, and Welch (1998)](https://doi.org/10.1023/A:1008306431147) use surrogate models to balance promising regions against uncertainty when objective evaluations are expensive. In biological sequence design, [Angermueller et al. (2020)](https://proceedings.mlr.press/v119/angermueller20a.html) introduce P3BO, which allocates proposals across an ensemble of methods according to their previous performance.

    #### Agentic Search

    Agentic search is a newer paradigm. [Language Agent Tree Search, or LATS (Zhou et al., 2024)](https://proceedings.mlr.press/v235/zhou24r.html) combines Monte Carlo tree search with language-model proposals, value estimates, reflection, and environmental feedback. [AIDE (Jiang et al., 2025)](https://arxiv.org/abs/2502.13138) frames machine-learning engineering as tree search over candidate code, while [The AI Scientist-v2 (Yamada et al., 2025)](https://arxiv.org/abs/2504.08066) uses agentic tree search within a broader research workflow. Branching exploration and building on previous attempts are therefore established ideas.

    An especially close biological example is [PABLO (Maus et al., 2026, preprint)](https://arxiv.org/abs/2601.22382v2). It coordinates planner, explorer, and worker agents for biological black-box optimization under an evaluation budget, using a history that includes successful and unsuccessful candidates. Its molecular and peptide design experiments make it relevant to our proposed agent-driven search. Using multiple agents, retaining failures, or optimizing biological designs is not by itself a new contribution.

    **With all this existing work, what does this project contribute?**

    A few things, I think. I'll dive into the specifics throughout the rest of this report, but:

    * Understanding how agents reason — we run some interesting experiments that have some surprising results. This helps us understand how agents think.
    * Benchmarking proposal policies — in this framework, a policy can be just about anything. It's interesting to benchmark LLMs, simple algorithms, and other models on a new kind of task.
    * The framework itself — this framework is open source and makes it straightforward to implement similar state search problems.

    ### Framing the Problem

    Using the same building blocks as the dungeon example, we can lay out the minimal E. coli problem. The walkthrough below follows the experiment implementation in [`yggdrisil-minimal-ecoli`](https://github.com/McClain-Thiel/yggdrisil-minimal-ecoli/tree/ea8f948862f7047f41364152977779743a43661e). We describe the reference search, which uses two growth checks: flux balance analysis (FBA) and resource balance analysis (RBA). Both are explained below.

    The Python-style pseudocode below keeps the experiment's main logic and leaves out type annotations, validation details, and storage plumbing. Helper names describe operations rather than actual library APIs. These blocks are for explanation and are not executed here. Full runs require the application's model and data dependencies; LLM-based runs also require an API key.
    """)
    return


@app.cell
def _(mo):
    mo.mermaid("""
    flowchart TD
        root(("Full MG1655<br/>D = ∅"))
        a(("Genome minus A<br/>D = A"))
        ab(("Genome minus A and B<br/>D = A ∪ B"))
        root -->|Delete gene set A| a
        a -->|Delete gene set B| ab
    """)
    return


@app.cell(hide_code=True)
def ecoli_state_description(mo):
    mo.md(r"""
    #### State: which genes have we deleted?

    In the dungeon example, the state was the set of items in the backpack. Here, our universe is the protein-coding genes in MG1655. We can think of a state as the genes we have retained: everything we have not deleted.

    The experiments store the equivalent **set of deleted genes**. Given the reference genome, either representation tells us the other. An empty deletion set therefore represents the root, the full MG1655 genome.

    We use `b` locus tags, such as `b0001`, as gene IDs. A frozen set makes deletion order irrelevant: deleting A then B reaches the same state as deleting B then A. Some experiments restrict which genes are eligible for deletion; genes outside that candidate set remain present.
    """)
    return


@app.cell(hide_code=True)
def ecoli_state_code(mo):
    mo.md(r"""
    ```python
    all_genes = load_mg1655_gene_ids()
    candidate_genes = load_candidate_gene_ids()
    initial_state = frozenset()  # No deletions yet.

    def retained_genes(deleted):
        return all_genes - deleted
    ```
    """)
    return


@app.cell(hide_code=True)
def ecoli_objective_description(mo):
    mo.md(r"""
    #### Objective: how small can we make it while passing the growth checks?

    The objective is simple: delete as many genes as possible while keeping the cell viable. Deleting genes is easy; deciding whether the cell could still grow is the interesting part.

    In the experiments, we approximate this with the FBA and RBA checks explained below. Among candidates passing both checks, we prefer more deletions, then higher FBA growth. The code keeps these measurements separate rather than combining everything into one weighted score. A model passing these checks still needs biological validation.
    """)
    return


@app.cell(hide_code=True)
def ecoli_objective_code(mo):
    mo.md(r"""
    ```python
    def passes_growth_checks(evidence):
        fba = evidence["fba"]
        rba = evidence["rba"]
        return (
            fba["solver_status"] == "optimal"
            and fba["growth_rate"] > 0
            and rba["feasible_at_growth_floor"]
        )

    def candidate_rank(deleted, evidence):
        return len(deleted), evidence["fba"]["growth_rate"]
    ```

    We rank only candidates that pass the checks. The full reporting code uses a stable state ID to break any remaining ties. The `fba-only` ablation omits the RBA requirement but still records its result.
    """)
    return


@app.cell(hide_code=True)
def ecoli_action_description(mo):
    mo.md(r"""
    #### Action: which additional genes should we delete?

    The action space is absolutely massive. We let the policy, which may be an agent or a simpler algorithm, choose a combination of genes that are still present and eligible for deletion.

    For the experiments described here, each action deletes between 1 and 20 genes. A policy step can propose several such actions. Keeping actions small lets us test changes incrementally; recovery comes from returning to a good parent and trying a different or smaller bundle after a failed child.
    """)
    return


@app.cell(hide_code=True)
def ecoli_action_code(mo):
    mo.md(r"""
    ```python
    available = candidate_genes - deleted

    action = choose_deletions(
        available,
        min_genes=1,
        max_genes=20,
    )
    ```

    Each action contains distinct genes. Fixed-size baseline arms request the maximum bundle size; variable-size arms can choose fewer.
    """)
    return


@app.cell(hide_code=True)
def ecoli_transition_description(mo):
    mo.md(r"""
    #### Transition: apply the deletion

    This is simple: apply the new deletions to the state. Conceptually, we remove genes from the retained genome. Because we store deletions, the code adds them to the deletion set.

    The problem checks that an action contains 1–20 eligible genes that have not already been deleted. For a valid action, the transition is just the set union below. Like an overweight backpack, a genome that fails a growth check is still recorded. Evaluation tells the policy whether to expand it.
    """)
    return


@app.cell(hide_code=True)
def ecoli_transition_code(mo):
    mo.md(r"""
    ```python
    def apply(deleted, action):
        return deleted.union(action)
    ```
    """)
    return


@app.cell(hide_code=True)
def ecoli_policy_description(mo):
    mo.md(r"""
    #### Policy and proposal: where do we try next?

    A policy chooses a parent state and proposes additional deletions. The agent version uses a deterministic scheduler to choose parents, then an LLM explorer to propose actions using the available evidence and previous outcomes. Random and heuristic baselines replace those choices with simpler rules.

    The important recovery behavior is that a good parent remains available after a failed child. We can return to it and try different genes or a smaller deletion bundle. We do not undo deletions inside the failed child.

    Each proposal pairs a parent with one action. In closed-book experiments, the model sees opaque gene labels; the saved states still use canonical gene IDs.
    """)
    return


@app.cell(hide_code=True)
def ecoli_policy_code(mo):
    mo.md(r"""
    ```python
    def propose_next(graph):
        parents = [
            node for node in graph.states
            if passes_growth_checks(node.evidence)
        ]
        if not parents:
            return []

        parent = scheduler.choose(parents, history=graph.history)
        available = candidate_genes - parent.deleted_genes
        actions = explorer.propose(
            parent,
            available_genes=available,
            max_genes=20,
            history=graph.history,
        )
        return [(parent, action) for action in actions]
    ```

    This sketches the agent policy. The scheduler balances promising states with diversity and previous attempts; it can select parents that already have children.
    """)
    return


@app.cell(hide_code=True)
def ecoli_runner_description(mo):
    mo.md(r"""
    #### Runner, graph, and limits: put the pieces together

    The runner evaluates the root, asks the policy for proposals, applies them, and evaluates the resulting states. It saves the states, transitions, measurements, and decision history in the graph. Different deletion orders can reuse the same state and cached measurements.

    We set limits on unique states, policy steps, and optionally wall time. The root counts as a state. LLM calls have additional limits on requests, tool use, tokens, and cost. The sketch below shows the main loop; the implementation also handles retries, interrupted runs, and checks that saved results match the current configuration.
    """)
    return


@app.cell(hide_code=True)
def ecoli_runner_code(mo):
    mo.md(r"""
    ```python
    graph.add_state(initial_state)
    graph.evaluate_cached(initial_state, evaluators)

    for step in range(max_steps):
        if state_or_time_limit_reached(graph):
            break

        proposals = propose_next(graph)
        if not proposals:
            break

        for parent, action in proposals:
            if state_or_time_limit_reached(graph):
                break

            child = apply(parent.deleted_genes, action)
            graph.add_transition(parent, action, child)
            graph.evaluate_cached(child, evaluators)

    ```

    Every valid proposed child is recorded, including those that fail growth checks. Subsequent parent selection uses the saved evidence. The implementation also has explicit retry and logging rules for empty responses and provider failures.
    """)
    return


@app.cell(hide_code=True)
def ecoli_evaluators(mo):
    mo.md(r"""
    ### Evaluators: what do we know about this candidate?

    The backpack needed weight and value. For a genome, we need several different kinds of evidence. We record five measurements: how much we removed, what experiments say about those genes, which annotated functions remain, and whether two mechanistic models predict growth.

    An **evaluator** takes a candidate genome and returns measurements. Only the FBA and RBA results determine whether a parent passes the reference search's growth checks. Essentiality and module retention provide additional evidence that a policy can use when choosing what to try.

    #### Genome size: how much have we removed?

    Here, “size” means the **number of protein-coding genes** remaining in the reference registry. An annotation identifies genes and their positions in a genome; our registry takes these from the MG1655 reference annotation. The original K-12 genome sequence is described by [Blattner et al. (1997)](https://doi.org/10.1126/science.277.5331.1453).

    This evaluator simply counts the deletion set and subtracts it from the reference gene count. It counts a short gene and a long gene equally, so it measures gene reduction rather than DNA length. It says nothing about whether the resulting cell can grow.

    In the experiment snapshot, the full registry has 4,290 genes. The WCM comparison permits deletions from a 1,216-gene subset, but the remaining-gene count still starts from the full registry. Genes outside that subset have not disappeared.

    ```python
    def measure_size(deleted):
        return {
            "genes_deleted": len(deleted),
            "genes_remaining": len(all_genes - deleted),
        }
    ```

    #### Essentiality: what happens when these genes are disrupted experimentally?

    An **essential gene** is required for growth under specified conditions. Conditions matter: a cell may need a gene to make a nutrient in minimal medium, but tolerate its loss when that nutrient is supplied.

    We use the experimental calls in Table S1 of [Choe et al. (2023)](https://doi.org/10.1128/msystems.00896-22). Their **transposon insertion sequencing**, or **Tn-seq**, experiment inserts DNA into many genomic positions and sequences the surviving population. A shortage of insertions within a gene can suggest that disrupting it harms growth. The paper also investigates false calls, including cases where DNA-binding proteins prevent insertion.

    The dataset compares **LB**, a rich growth medium, with **M9 glucose**, a defined minimal medium. Our application summarizes the two calls as follows; these are the application's labels, not universal biological categories:

    | Label | Call in LB | Call in M9 glucose |
    | --- | --- | --- |
    | Essential | Essential | Essential |
    | Conditionally essential | Nonessential | Essential |
    | Nonessential | Nonessential | Nonessential |
    | Ambiguous | Essential | Nonessential |
    | Unknown | No matched measurement | No matched measurement |

    We count deleted genes in each category and retain their identities. “Unknown” means missing evidence. Even a nonessential call does not guarantee that a gene can be deleted safely alongside other genes: combinations can be synthetically lethal. These classifications inform the search but are not a blanket deletion ban.

    ```python
    from collections import Counter

    def measure_essentiality(deleted):
        labels = [essentiality_table[gene] for gene in deleted]
        return dict(Counter(labels))
    ```

    The table includes an `unknown` entry for genes without a matched measurement. This sketch shows the counts; the experiment also saves the genes in each category.

    #### Module retention: do we still encode the pieces of a biological function?

    **KEGG**, the Kyoto Encyclopedia of Genes and Genomes, organizes biological knowledge into pathways and other functional descriptions. A **KEGG module** is a smaller unit, such as the reactions needed to make a particular compound or the components of a molecular complex. [Takami et al. (2012)](https://doi.org/10.1186/1471-2164-13-699) describe using modules to infer functional capacity from gene sets.

    Genes are mapped to **KEGG Orthology (KO)** identifiers: labels for molecular functions. Several genes can support the same KO. A module then specifies which functions are required using **AND** and **OR** rules, with optional components where appropriate. For example, `(A OR B) AND C` needs either function A or B, plus function C. See the official [KO definitions](https://www.genome.jp/kegg/ko.html) and [module completeness rules](https://www.genome.jp/kegg/module.html).

    We first identify modules that are complete in the undeleted reference, then check which become incomplete after deletion. The result records retained and broken modules, plus missing required functions. Fixed background annotations remain available alongside the functions encoded by retained genes.

    This is an annotation-based check: it asks whether the required pieces are encoded, not whether a pathway actually carries enough material to support growth. Missing annotations are reported as coverage gaps, and a broken module is evidence for the policy rather than an automatic declaration of lethality.

    ```python
    def measure_modules(deleted):
        remaining = all_genes - deleted
        functions = functions_present(remaining, background_annotations)

        broken = []
        for module in reference_complete_modules:
            if not module.requirements_met(functions):
                broken.append(module)

        return {
            "n_complete": len(reference_complete_modules) - len(broken),
            "broken_modules": broken,
        }
    ```

    `requirements_met` stands for the module’s AND/OR logic, not a percentage-of-genes threshold.

    #### FBA: can the metabolic network produce biomass?

    **Flux balance analysis (FBA)** asks how material can flow through a network of biochemical reactions. A **metabolite** is a molecule consumed or produced by those reactions, and a **flux** is a reaction's rate. FBA assumes a steady state: production and consumption of each internal metabolite balance. Nutrient uptake and reaction bounds restrict the allowed flows. A numerical solver finds flows satisfying these constraints while optimizing a chosen objective. [Orth, Thiele, and Palsson (2010)](https://doi.org/10.1038/nbt.1614) give an introduction.

    For growth, the objective is a **biomass reaction**: a bookkeeping reaction that consumes the building blocks needed to make cellular material in specified proportions. Its flux serves as the model's predicted specific growth rate, in inverse hours. It is a mathematical representation of growth, rather than a simulation of an individual cell dividing. See [Feist and Palsson (2010)](https://doi.org/10.1016/j.mib.2010.03.003).

    We use **iML1515**, an E. coli metabolic reconstruction linking genes, proteins, and reactions, with an aerobic M9/glucose medium. **Gene–protein–reaction rules** describe which genes support each reaction: an enzyme complex may need multiple genes together, while alternative enzymes can provide redundancy. Deleting genes disables reactions according to those rules, after which the model is solved again. The reconstruction is described by [Monk et al. (2017)](https://doi.org/10.1038/nbt.3956).

    We record the predicted growth rate and **solver status**, which tells us whether the optimization succeeded. An optimal solution can still have zero growth, so the search requires both an optimal solve and positive biomass flux. We also record **coverage**: which deleted genes occur in the model. A gene outside iML1515 can have important functions that this evaluator cannot assess.

    ```python
    def measure_fba(deleted):
        model = iml1515.copy()
        modeled, unmodeled = split_by_model_coverage(deleted, model)

        model.set_medium(aerobic_m9_glucose)
        model.knock_out_genes(modeled)
        solution = model.maximize_biomass()

        return {
            "growth_rate": solution.growth_rate,
            "solver_status": solution.status,
            "unmodeled_deletions": unmodeled,
        }
    ```

    `knock_out_genes` applies the gene–protein–reaction rules. The model is copied so one candidate’s deletions do not change the next candidate’s starting model.

    #### RBA: can the cell build and maintain the machinery needed for growth?

    **Resource balance analysis (RBA)** adds constraints on the machinery that carries out cellular processes. Metabolic reactions require enough **enzymes** to support their fluxes. Making those enzymes requires **ribosomes**, which synthesize proteins, and supporting processes such as **chaperoning**, which helps proteins fold, and **secretion**, which transports proteins. The model also limits how much machinery fits into cellular compartments and how the cell allocates its **proteome**, its complement of proteins. These requirements compete for finite resources. See the [RBA overview](https://rba.inrae.fr/overview.html) and [Bulović et al. (2019)](https://doi.org/10.1016/j.ymben.2019.06.001).

    Our evaluator uses the E. coli K-12 RBA model from that work. A deletion disables the modeled enzymes and process machinery requiring the corresponding protein. We then ask whether the remaining system can support **balanced growth**: sustained growth with a consistent cellular composition, including enough production to replenish its machinery. The mathematical constraints are described in the [RBA theory guide](https://rba.inrae.fr/theory.html).

    The experiment tests a fixed **growth floor** of **0.1 h⁻¹**. This means asking whether the model can sustain that specific growth rate, rather than searching for each candidate's maximum rate. The floor is an experiment setting, not a universal boundary between living and dead cells.

    The result reports feasibility at that floor, modeled and unmodeled deletions, and solver diagnostics. RBA covers processes that ordinary FBA leaves out, but it still models only part of the cell. Passing both checks is evidence for a candidate worth studying further, not confirmation that it will divide experimentally.

    ```python
    def measure_rba(deleted):
        model = rba_reference.copy()
        modeled, unmodeled = split_by_model_coverage(deleted, model)

        model.disable_protein_machines(modeled)
        solution = model.check_growth(rate=0.1)

        return {
            "feasible_at_growth_floor": solution.feasible,
            "solver_status": solution.status,
            "unmodeled_deletions": unmodeled,
        }
    ```

    The model keeps its configured medium and resource constraints. A numerical solver error is a failed computation, not evidence that the genome is lethal; the experiment records diagnostics and raises unresolved errors.

    #### Keep the evidence together, without collapsing it into one score

    Each evaluator returns a different view of the same candidate. The experiment saves those measurements with **coverage** (what was actually assessed) and **provenance** (which data, model, and settings produced the result). A cached result can be reused when the candidate and evaluator configuration match.

    ```python
    evaluators = {
        "size": measure_size,
        "essentiality": measure_essentiality,
        "modules": measure_modules,
        "fba": measure_fba,
        "rba": measure_rba,
    }

    def evaluate(deleted):
        return {
            name: measure(deleted)
            for name, measure in evaluators.items()
        }
    ```

    The short keys here are just for the pseudocode. The growth checks use FBA and RBA; the remaining evidence helps describe and compare candidates. Coverage gaps remain visible even when a candidate passes both models.
    """)
    return


if __name__ == "__main__":
    app.run()
