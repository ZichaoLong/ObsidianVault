#!/usr/bin/env python3
"""Executable structural reference for HB-Lattice-v0.

This file intentionally uses only the Python standard library.  The vector
functions below are toy kernels: they make data flow and state changes visible,
but they are not a numerical implementation of Transformer attention.

The reference demonstrates four contracts:

1. P0-P4 is a pre-norm GPT-like residual backbone for every cell.
2. A receiving leaf always updates observer state.
3. Only selected leaves call the heavy kernel and emit a result.
4. Processing a chunk produces the same outputs, routes, and final state as
   repeatedly processing one token at a time.

P5 and P6 deliberately use separate stage-local state namespaces.  Sharing
mutable observer/load state across those planes would require an additional
commutation or scan proof before the plane-major chunk schedule is valid.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from math import sqrt, tanh
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple


Vector = Tuple[float, ...]
LeafKey = Tuple[int, int]

DIM = 4
REGION_COUNT = 4
CELLS_PER_REGION = 4
CELL_ROWS = 4
CELL_COLS = 4
CELL_COUNT = CELL_ROWS * CELL_COLS
LEAF_ROWS = 4
LEAF_COLS = 4
LEAVES_PER_CELL = LEAF_ROWS * LEAF_COLS

REGION_CELL_BUDGET = 2
LEAF_BUDGET = 2
LOAD_DECAY = 0.90
REGION_LOAD_WEIGHT = 0.35
LEAF_LOAD_WEIGHT = 0.25


def zeros() -> Vector:
    return (0.0,) * DIM


def add(*vectors: Vector) -> Vector:
    return tuple(sum(values) for values in zip(*vectors))


def scale(vector: Vector, factor: float) -> Vector:
    return tuple(factor * value for value in vector)


def vector_sum(vectors: Iterable[Vector]) -> Vector:
    result = zeros()
    for vector in vectors:
        result = add(result, vector)
    return result


def rms_norm(vector: Vector, epsilon: float = 1e-6) -> Vector:
    rms = sqrt(sum(value * value for value in vector) / DIM + epsilon)
    return scale(vector, 1.0 / rms)


def mean_abs(vector: Vector) -> float:
    return sum(abs(value) for value in vector) / DIM


def squash(vector: Vector) -> Vector:
    return tuple(tanh(value) for value in vector)


def constant_vector(value: float) -> Vector:
    return tuple(value * (index + 1) / DIM for index in range(DIM))


def alternating_projection(vector: Vector, seed: int) -> float:
    signs = (1.0, -1.0, 1.0, -1.0)
    return sum(
        signs[(index + seed) % DIM] * value
        for index, value in enumerate(vector)
    ) / DIM


def top_k(scores: Mapping[int, float], count: int) -> Tuple[int, ...]:
    ranked = sorted(scores, key=lambda item: (-scores[item], item))
    return tuple(ranked[:count])


@dataclass
class CausalAttentionState:
    total: Vector = field(default_factory=zeros)
    count: int = 0


@dataclass
class LeafState:
    observer: float = 0.0
    load: float = 0.0


@dataclass
class RuntimeState:
    next_position: int = 0
    attention: List[CausalAttentionState] = field(
        default_factory=lambda: [CausalAttentionState() for _ in range(CELL_COUNT)]
    )
    cell_load: List[float] = field(
        default_factory=lambda: [0.0 for _ in range(CELL_COUNT)]
    )
    # These namespaces are semantically separate, even if one device stores
    # both for the same geometric leaf coordinate.
    p5_leaf: List[LeafState] = field(
        default_factory=lambda: [
            LeafState() for _ in range(CELL_COUNT * LEAVES_PER_CELL)
        ]
    )
    p6_leaf: List[LeafState] = field(
        default_factory=lambda: [
            LeafState() for _ in range(CELL_COUNT * LEAVES_PER_CELL)
        ]
    )


@dataclass(frozen=True)
class Message:
    source_cell: int
    source_leaf: int
    target_cell: int
    target_leaf: int
    merge_cell: int
    payload: Vector


@dataclass(frozen=True)
class SlowDelta:
    source_cell: int
    source_leaf: int
    merge_cell: int
    payload: Vector


@dataclass(frozen=True)
class TokenTrace:
    position: int
    selected_cells: Tuple[Tuple[int, ...], ...]
    p5_active: Tuple[LeafKey, ...]
    p6_active: Tuple[LeafKey, ...]
    p6_message_count: int
    p5_heavy_calls: int
    p6_heavy_calls: int


def state_index(cell: int, leaf: int) -> int:
    return cell * LEAVES_PER_CELL + leaf


def get_leaf_state(states: List[LeafState], key: LeafKey) -> LeafState:
    cell, leaf = key
    return states[state_index(cell, leaf)]


def embed(token: int, position: int) -> Vector:
    """A deterministic stand-in for token and position embedding."""

    return tuple(
        tanh(0.17 * (token + 1) * (index + 1) + 0.03 * (position + 1))
        for index in range(DIM)
    )


def inject_context(token_vector: Vector, cell: int) -> Vector:
    """P0: inject small global, region, and cell-specific context."""

    region = cell // CELLS_PER_REGION
    return add(
        token_vector,
        scale(token_vector, 0.05),
        scale(token_vector, 0.01 * (region + 1)),
        constant_vector(0.002 * (cell + 1)),
    )


def causal_attention(
    normalized_input: Vector,
    attention_state: CausalAttentionState,
    cell: int,
) -> Vector:
    """Toy causal readout used in place of a real packed Attention kernel."""

    attention_state.total = add(attention_state.total, normalized_input)
    attention_state.count += 1
    causal_mean = scale(attention_state.total, 1.0 / attention_state.count)
    return scale(causal_mean, 0.10 + 0.01 * (cell % CELLS_PER_REGION))


def ffn(normalized_input: Vector, cell: int) -> Vector:
    """Toy cell-local FFN residual delta."""

    shifted = add(normalized_input, constant_vector(0.01 * (cell + 1)))
    return scale(squash(shifted), 0.08 + 0.005 * (cell % CELLS_PER_REGION))


def pre_norm_gpt_block(
    cell_input: Vector,
    attention_state: CausalAttentionState,
    cell: int,
) -> Vector:
    """P1-P4: the always-on GPT-like fast path."""

    attention_delta = causal_attention(rms_norm(cell_input), attention_state, cell)
    attention_merged = add(cell_input, attention_delta)
    ffn_delta = ffn(rms_norm(attention_merged), cell)
    return add(attention_merged, ffn_delta)


def update_load(current: float, selected: bool) -> float:
    indicator = 1.0 if selected else 0.0
    return LOAD_DECAY * current + (1.0 - LOAD_DECAY) * indicator


def select_region_cells(
    fast: Sequence[Vector],
    state: RuntimeState,
) -> Tuple[Tuple[int, ...], ...]:
    """P4: select at most two cells in each row-shaped region."""

    selected_by_region: List[Tuple[int, ...]] = []
    all_selected: Set[int] = set()

    for region in range(REGION_COUNT):
        cells = tuple(
            range(
                region * CELLS_PER_REGION,
                (region + 1) * CELLS_PER_REGION,
            )
        )
        average_load = sum(state.cell_load[cell] for cell in cells) / len(cells)
        scores = {
            cell: alternating_projection(fast[cell], cell)
            - REGION_LOAD_WEIGHT * (state.cell_load[cell] - average_load)
            for cell in cells
        }
        selected = top_k(scores, REGION_CELL_BUDGET)
        selected_by_region.append(selected)
        all_selected.update(selected)

    for cell in range(CELL_COUNT):
        state.cell_load[cell] = update_load(
            state.cell_load[cell],
            cell in all_selected,
        )

    return tuple(selected_by_region)


def merge_inbox(inbox: Mapping[LeafKey, Sequence[Message]]) -> Dict[LeafKey, Vector]:
    """Merge every inbox in a stable source order."""

    merged: Dict[LeafKey, Vector] = {}
    for key, messages in inbox.items():
        ordered = sorted(
            messages,
            key=lambda message: (
                message.source_cell,
                message.source_leaf,
                message.target_cell,
                message.target_leaf,
            ),
        )
        merged[key] = vector_sum(message.payload for message in ordered)
    return merged


def update_observers(
    payloads: Mapping[LeafKey, Vector],
    states: List[LeafState],
) -> None:
    """Every receiver updates state, including leaves that remain inactive."""

    for key, payload in payloads.items():
        leaf_state = get_leaf_state(states, key)
        leaf_state.observer = 0.90 * leaf_state.observer + 0.10 * mean_abs(payload)


def select_leaves(
    payloads: Mapping[LeafKey, Vector],
    states: List[LeafState],
    stage: int,
) -> Tuple[LeafKey, ...]:
    """Select at most two receiving leaves per destination cell."""

    candidates_by_cell: Dict[int, List[int]] = {}
    for cell, leaf in payloads:
        candidates_by_cell.setdefault(cell, []).append(leaf)

    selected: Set[LeafKey] = set()
    for cell, leaves in candidates_by_cell.items():
        unique_leaves = sorted(set(leaves))
        cell_states = [get_leaf_state(states, (cell, leaf)) for leaf in range(LEAVES_PER_CELL)]
        average_load = sum(item.load for item in cell_states) / LEAVES_PER_CELL
        scores: Dict[int, float] = {}
        for leaf in unique_leaves:
            leaf_state = get_leaf_state(states, (cell, leaf))
            semantic_score = alternating_projection(payloads[(cell, leaf)], leaf + stage)
            semantic_score += 0.03 * leaf_state.observer
            semantic_score += 0.001 * ((cell + 1) * (leaf + 3) % 17)
            scores[leaf] = semantic_score - LEAF_LOAD_WEIGHT * (
                leaf_state.load - average_load
            )
        for leaf in top_k(scores, min(LEAF_BUDGET, len(scores))):
            selected.add((cell, leaf))

    for cell in range(CELL_COUNT):
        for leaf in range(LEAVES_PER_CELL):
            leaf_state = get_leaf_state(states, (cell, leaf))
            leaf_state.load = update_load(
                leaf_state.load,
                (cell, leaf) in selected,
            )

    return tuple(sorted(selected))


def heavy_leaf_kernel(
    payload: Vector,
    leaf_state: LeafState,
    cell: int,
    leaf: int,
    stage: int,
) -> Vector:
    """Toy stand-in for an expensive Attention, SSM, FFN, or adapter kernel."""

    local_context = constant_vector(
        0.02 * leaf_state.observer + 0.001 * (cell + leaf + stage)
    )
    gain = 0.05 if stage == 5 else 0.07
    return scale(squash(add(payload, local_context)), gain)


def leaf_neighbors(cell: int, leaf: int) -> Tuple[LeafKey, ...]:
    """The nine fixed P5-to-P6 candidate edges from the architecture note."""

    cell_row, cell_col = divmod(cell, CELL_COLS)
    leaf_row, leaf_col = divmod(leaf, LEAF_COLS)

    targets: Set[LeafKey] = {(cell, leaf)}
    for row_delta, col_delta in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        neighbor_leaf_row = (leaf_row + row_delta) % LEAF_ROWS
        neighbor_leaf_col = (leaf_col + col_delta) % LEAF_COLS
        targets.add(
            (cell, neighbor_leaf_row * LEAF_COLS + neighbor_leaf_col)
        )

        neighbor_cell_row = (cell_row + row_delta) % CELL_ROWS
        neighbor_cell_col = (cell_col + col_delta) % CELL_COLS
        neighbor_cell = neighbor_cell_row * CELL_COLS + neighbor_cell_col
        targets.add((neighbor_cell, leaf))

    return tuple(sorted(targets))


def run_p5(
    fast: Sequence[Vector],
    selected_cells: Sequence[Sequence[int]],
    state: RuntimeState,
) -> Tuple[List[Message], Tuple[LeafKey, ...]]:
    """P5: all candidate leaves update state; active leaves compute and emit."""

    inbox: Dict[LeafKey, List[Message]] = {}
    for region_cells in selected_cells:
        for cell in region_cells:
            for leaf in range(LEAVES_PER_CELL):
                key = (cell, leaf)
                inbox[key] = [
                    Message(
                        source_cell=cell,
                        source_leaf=-1,
                        target_cell=cell,
                        target_leaf=leaf,
                        merge_cell=cell,
                        payload=fast[cell],
                    )
                ]

    payloads = merge_inbox(inbox)
    update_observers(payloads, state.p5_leaf)
    active = select_leaves(payloads, state.p5_leaf, stage=5)

    outgoing: List[Message] = []
    for cell, leaf in active:
        leaf_state = get_leaf_state(state.p5_leaf, (cell, leaf))
        result = heavy_leaf_kernel(payloads[(cell, leaf)], leaf_state, cell, leaf, 5)
        for target_cell, target_leaf in leaf_neighbors(cell, leaf):
            outgoing.append(
                Message(
                    source_cell=cell,
                    source_leaf=leaf,
                    target_cell=target_cell,
                    target_leaf=target_leaf,
                    merge_cell=target_cell,
                    payload=result,
                )
            )

    return outgoing, active


def run_p6(
    messages: Sequence[Message],
    state: RuntimeState,
) -> Tuple[List[SlowDelta], Tuple[LeafKey, ...]]:
    """P6: merge local messages, update every receiver, then select compute."""

    inbox: Dict[LeafKey, List[Message]] = {}
    for message in messages:
        key = (message.target_cell, message.target_leaf)
        inbox.setdefault(key, []).append(message)

    payloads = merge_inbox(inbox)
    update_observers(payloads, state.p6_leaf)
    active = select_leaves(payloads, state.p6_leaf, stage=6)

    deltas: List[SlowDelta] = []
    for cell, leaf in active:
        leaf_state = get_leaf_state(state.p6_leaf, (cell, leaf))
        result = heavy_leaf_kernel(payloads[(cell, leaf)], leaf_state, cell, leaf, 6)
        deltas.append(
            SlowDelta(
                source_cell=cell,
                source_leaf=leaf,
                merge_cell=cell,
                payload=result,
            )
        )

    return deltas, active


def deadline_merge(
    fast: Sequence[Vector],
    slow_deltas: Sequence[SlowDelta],
) -> List[Vector]:
    """P7: fixed-source-order residual merge into each cell backbone."""

    by_cell: Dict[int, List[SlowDelta]] = {}
    for delta in slow_deltas:
        by_cell.setdefault(delta.merge_cell, []).append(delta)

    output: List[Vector] = []
    for cell in range(CELL_COUNT):
        ordered = sorted(
            by_cell.get(cell, []),
            key=lambda delta: (delta.source_cell, delta.source_leaf),
        )
        slow = vector_sum(delta.payload for delta in ordered)
        output.append(add(fast[cell], slow))
    return output


def readout(cell_output: Sequence[Vector]) -> Vector:
    return scale(vector_sum(cell_output), 1.0 / CELL_COUNT)


class HBLatticeV0Reference:
    def __init__(self) -> None:
        self.state = RuntimeState()

    def forward_chunk(
        self,
        tokens: Sequence[int],
    ) -> Tuple[List[Vector], List[TokenTrace]]:
        """Run one HB-Lattice superblock over a finite token chunk."""

        start = self.state.next_position
        positions = list(range(start, start + len(tokens)))

        # P0: construct one carrier per token and cell.
        cell_input: List[List[Vector]] = []
        for token, position in zip(tokens, positions):
            token_vector = embed(token, position)
            cell_input.append(
                [inject_context(token_vector, cell) for cell in range(CELL_COUNT)]
            )

        # P1-P4: a real backend packs this [cell, token, hidden] work.  The toy
        # attention state is scanned in token order to preserve causal semantics.
        fast: List[List[Vector]] = [
            [zeros() for _ in range(CELL_COUNT)] for _ in tokens
        ]
        for cell in range(CELL_COUNT):
            for token_offset in range(len(tokens)):
                fast[token_offset][cell] = pre_norm_gpt_block(
                    cell_input[token_offset][cell],
                    self.state.attention[cell],
                    cell,
                )

        # P4 selector: token order is semantic; batch/chunk packing is not.
        selected_cells = [
            select_region_cells(token_fast, self.state) for token_fast in fast
        ]

        p5_messages: List[List[Message]] = []
        p5_active: List[Tuple[LeafKey, ...]] = []
        for token_fast, token_cells in zip(fast, selected_cells):
            messages, active = run_p5(token_fast, token_cells, self.state)
            p5_messages.append(messages)
            p5_active.append(active)

        p6_deltas: List[List[SlowDelta]] = []
        p6_active: List[Tuple[LeafKey, ...]] = []
        for messages in p5_messages:
            deltas, active = run_p6(messages, self.state)
            p6_deltas.append(deltas)
            p6_active.append(active)

        outputs: List[Vector] = []
        traces: List[TokenTrace] = []
        for token_offset, position in enumerate(positions):
            cell_output = deadline_merge(fast[token_offset], p6_deltas[token_offset])
            outputs.append(readout(cell_output))
            traces.append(
                TokenTrace(
                    position=position,
                    selected_cells=selected_cells[token_offset],
                    p5_active=p5_active[token_offset],
                    p6_active=p6_active[token_offset],
                    p6_message_count=len(p5_messages[token_offset]),
                    p5_heavy_calls=len(p5_active[token_offset]),
                    p6_heavy_calls=len(p6_active[token_offset]),
                )
            )

        self.state.next_position += len(tokens)
        return outputs, traces


def vectors_close(left: Sequence[Vector], right: Sequence[Vector]) -> bool:
    if len(left) != len(right):
        return False
    return all(
        abs(left_value - right_value) <= 1e-12
        for left_vector, right_vector in zip(left, right)
        for left_value, right_value in zip(left_vector, right_vector)
    )


def format_active(active: Sequence[LeafKey]) -> str:
    by_cell: Dict[int, List[int]] = {}
    for cell, leaf in active:
        by_cell.setdefault(cell, []).append(leaf)
    return " ".join(
        f"C{cell}:L{','.join(str(leaf) for leaf in leaves)}"
        for cell, leaves in sorted(by_cell.items())
    )


def run_demo(tokens: Sequence[int]) -> None:
    prefill_model = HBLatticeV0Reference()
    prefill_output, prefill_trace = prefill_model.forward_chunk(tokens)

    decode_model = HBLatticeV0Reference()
    decode_output: List[Vector] = []
    decode_trace: List[TokenTrace] = []
    for token in tokens:
        output, trace = decode_model.forward_chunk([token])
        decode_output.extend(output)
        decode_trace.extend(trace)

    assert vectors_close(prefill_output, decode_output)
    assert prefill_trace == decode_trace
    assert prefill_model.state == decode_model.state

    print("chunk == repeated decode: PASS")
    for trace in prefill_trace:
        region_text = " ".join(
            f"R{region}:{','.join('C' + str(cell) for cell in cells)}"
            for region, cells in enumerate(trace.selected_cells)
        )
        print(f"t={trace.position}  selected-cells [{region_text}]")
        print(
            f"  P5 heavy={trace.p5_heavy_calls:2d}  "
            f"P6 messages={trace.p6_message_count:3d}  "
            f"P6 heavy={trace.p6_heavy_calls:2d}"
        )
        print(f"  P5 active: {format_active(trace.p5_active)}")
        print(f"  P6 active: {format_active(trace.p6_active)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tokens",
        nargs="*",
        type=int,
        default=[7, 1, 9, 3],
        help="integer token ids used by the toy embedding",
    )
    arguments = parser.parse_args()
    run_demo(arguments.tokens)


if __name__ == "__main__":
    main()
