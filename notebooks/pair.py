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

    For a more realistic use case, let's think about minimizing an E. coli genome. You can start with something to be optimized; let's say we start with MG1655. Then we want to minimize the genome ([why?](https://link.springer.com/chapter/10.1007/978-981-19-7911-8_2)). We can define a root node "state" as the full MG1655 genome (represented here as a set of genes). To optimize, we can think about what genes we want to delete, then define each set of genes to delete as an action on an edge, and each resulting genome as another state node.

    For this simplified task, an action deletes a gene or set of genes (up to 20 per transition). We can define the objective as minimizing the number of genes, subject to not killing the cell (as defined by maintaining growth above a chosen threshold).

    This is where the framework and agent earn their pay. Genome minimization, as you might expect, is a much harder task for several reasons. Biology is filled with complex networks of genes, and the effects of combining deletions can be hard to predict. Some single-gene deletions are lethal under the chosen growth conditions. Other deletions are tolerated individually but become lethal in combination, a phenomenon known as synthetic lethality. This means that genes we can delete separately cannot always be deleted together. [Côté et al. (2016)](https://doi.org/10.1128/mBio.01714-16) provide an E. coli example of these genetic interactions.

    We need to be able to navigate this network of candidate states (combinations of genes) and evaluate which combinations might be viable (model predictions alone cannot establish viability in a living cell) and which are not. As in the backpack example, a candidate can be a valid state representation even if it fails the viability evaluation.

    Evaluations are noisy, and even a good model is an imperfect proxy for a living cell. We'll come back to this. The total number of combinations is also absolutely massive: $n$ genes give $2^n$ possible subsets. For scale, taking approximately $n = 4{,}200$ protein-coding genes gives roughly $2.1 \times 10^{1264}$ subsets. The precise gene count depends on the annotation, and the actual search space depends on which genes we allow ourselves to delete. Brute-force exploration is infeasible at this scale. Existing algorithms tackle the problem using heuristics and models; we want to test whether agent-guided search can make better use of a limited evaluation budget.

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

    * Understanding how agents reason — we run some interesting experiments that have some surprising results. This helps us understand how agents reason.
    * Benchmarking proposal policies — in this framework, a policy can be just about anything. It's interesting to benchmark LLMs, simple algorithms, and other models on a new kind of task.
    * The framework itself — this framework is open source and makes it straightforward to implement similar state search problems.

    ### Framing the Problem
    """)
    return


@app.cell
def _(mo):
    mo.mermaid("""
    flowchart TD
        root(("Full MG1655<br/>genome"))
        a(("Genome<br/>minus A"))
        ab(("Genome<br/>minus A and B"))
        root -->|Delete gene set A| a
        a -->|Delete gene set B| ab
    """)
    return


@app.cell(hide_code=True)
def related_work_sources(mo):
    mo.accordion({
        "Related-work sources — saved Notion notes and primary papers": mo.md(r"""
    This reading list combines papers tagged **Yggdrisil** in the [Literature Repo](https://www.notion.so/60205c251eee4745b338745b8fd39cfc) with the VAE preprint linked during drafting. This is a first selection for the draft, not a complete literature review.

    | Work | Why it belongs here | Saved note | Primary paper |
    | --- | --- | --- | --- |
    | Pósfai et al. (2006) | Experimental E. coli genome reduction | [Notion](https://www.notion.so/3ddd0098937c81bc8ff9cb78adaea392) | [Science](https://doi.org/10.1126/science.1126439) |
    | Côté et al. (2016) | Context-dependent gene essentiality and synthetic lethality | [Notion](https://www.notion.so/3ddd0098937c81d29fa6c59a07f5545b) | [mBio](https://doi.org/10.1128/mBio.01714-16) |
    | Rees-Garbutt et al. (2020) | Minesweeper and GAMA; computational genome reduction | [Notion](https://www.notion.so/3ddd0098937c817f878cf41c7668283d) | [Nature Communications](https://www.nature.com/articles/s41467-020-14545-0) |
    | Gherman et al. (2025) | E. coli reduction with a whole-cell model and ML surrogate | [Notion](https://www.notion.so/3ddd0098937c81529398fa7d012789d7) | [Cell Systems](https://doi.org/10.1016/j.cels.2025.101392) |
    | Shcherbakova et al. (2025), VAE genome design | Learned proposals for reduced E. coli gene sets, evaluated in silico | Added during drafting | [bioRxiv, v2](https://www.biorxiv.org/content/10.1101/2024.10.22.619620v2) |
    | Jones et al. (1998) | Optimization when evaluations are expensive | [Notion](https://www.notion.so/3ddd0098937c81fd8cf4e9fca8977d3a) | [Journal of Global Optimization](https://doi.org/10.1023/A:1008306431147) |
    | Angermueller et al. (2020), P3BO | Adaptive allocation across biological sequence optimizers | [Notion](https://www.notion.so/3ddd0098937c815abdfbde061c386560) | [ICML](https://proceedings.mlr.press/v119/angermueller20a.html) |
    | Zhou et al. (2024), LATS | Agent search with environmental feedback | [Notion](https://www.notion.so/3ddd0098937c8125bd41d8af8cb51937) | [ICML](https://proceedings.mlr.press/v235/zhou24r.html) |
    | Jiang et al. (2025), AIDE | Tree search over candidate code | [Notion](https://www.notion.so/3dfd0098937c812db947f33d4f97bea2) | [Preprint](https://arxiv.org/abs/2502.13138) |
    | Yamada et al. (2025), AI Scientist-v2 | Agentic tree search within an automated research workflow | [Notion](https://www.notion.so/3dfd0098937c8190be09f622e51b4594) | [Preprint](https://arxiv.org/abs/2504.08066) |
    | Maus et al. (2026), PABLO | Close precedent for agent-driven biological optimization | [Notion](https://www.notion.so/3ddd0098937c816593b7d2c51192f7df) | [Preprint, v2](https://arxiv.org/abs/2601.22382v2) |
    | Chen et al. (2024) | How evaluator quality affects the value of search | [Notion](https://www.notion.so/3dfd0098937c81198360fc88afdcde02) | [ACL](https://aclanthology.org/2024.acl-long.738/) |

    The primary abstracts were checked for the broad summaries above, with additional method passages checked for Minesweeper/GAMA, Gherman's surrogate, and PABLO. The VAE summary is based on the linked v2 abstract. Detailed architecture comparisons remain to be developed.
    """)
    })
    return


if __name__ == "__main__":
    app.run()
