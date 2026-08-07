#!/usr/bin/env python3
"""Executable structural reference for HB-Line-v0.

This standard-library-only model separates three things that the historical
HB-Lattice drawing combined:

1. A line graph defines spatial adjacency inside every depth slice.
2. Internal messages travel only from depth ``d`` to depth ``d + 1``;
   final outbound messages enter statically declared output-boundary slots.
3. Observe/update/score, group allocation, and active compute are fixed
   microstages inside one slice transition.

The toy kernels are not Transformer or Mamba implementations.  The reference
checks a narrower architectural contract: depth-major chunk execution, token-
major decode execution, and arbitrary chunk splitting produce the same output,
route artifacts, and persistent state.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
from math import sqrt, tanh
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


Vector = Tuple[float, ...]

DIM = 4
SITE_COUNT = 8
DEPTH_COUNT = 6
GROUP_SIZE = 4
ACTIVE_BUDGET = 2
BACKBONE_SITES = (1, 5)
LOAD_DECAY = 0.90
LOAD_WEIGHT = 0.25


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


def alternating_projection(vector: Vector, seed: int) -> float:
    signs = (1.0, -1.0, 1.0, -1.0)
    return sum(
        signs[(index + seed) % DIM] * value
        for index, value in enumerate(vector)
    ) / DIM


def top_k(scores: Mapping[int, float], count: int) -> Tuple[int, ...]:
    ranked = sorted(scores, key=lambda site: (-scores[site], site))
    return tuple(ranked[:count])


def line_neighbors(site: int) -> Tuple[int, ...]:
    """Return self and radius-one neighbors without wraparound."""

    return tuple(
        candidate
        for candidate in (site - 1, site, site + 1)
        if 0 <= candidate < SITE_COUNT
    )


def group_sites(group: int) -> Tuple[int, ...]:
    start = group * GROUP_SIZE
    return tuple(range(start, start + GROUP_SIZE))


def group_of(site: int) -> int:
    return site // GROUP_SIZE


def backbone_for_group(group: int) -> int:
    candidates = tuple(site for site in BACKBONE_SITES if group_of(site) == group)
    if len(candidates) != 1:
        raise ValueError("each group must contain exactly one backbone site")
    return candidates[0]


def validate_config() -> None:
    if DIM <= 0 or SITE_COUNT <= 0 or DEPTH_COUNT <= 0:
        raise ValueError("dimensions, sites, and depths must be positive")
    if SITE_COUNT % GROUP_SIZE != 0:
        raise ValueError("SITE_COUNT must be divisible by GROUP_SIZE")
    if not 1 <= ACTIVE_BUDGET <= GROUP_SIZE:
        raise ValueError("ACTIVE_BUDGET must fit inside one group")
    if any(not 0 <= site < SITE_COUNT for site in BACKBONE_SITES):
        raise ValueError("backbone site is outside the line")
    for group in range(SITE_COUNT // GROUP_SIZE):
        backbone_for_group(group)


validate_config()


@dataclass(frozen=True)
class Message:
    position: int
    source_depth: int
    source_site: int
    target_site: int
    source_slot: int
    payload: Vector


@dataclass
class NodeState:
    observer: float = 0.0
    causal_total: Vector = field(default_factory=zeros)
    causal_count: int = 0


@dataclass
class AllocatorState:
    load: List[float] = field(
        default_factory=lambda: [0.0 for _ in range(SITE_COUNT)]
    )


@dataclass
class RuntimeState:
    next_position: int = 0
    node: List[List[NodeState]] = field(
        default_factory=lambda: [
            [NodeState() for _ in range(SITE_COUNT)]
            for _ in range(DEPTH_COUNT)
        ]
    )
    allocator: List[AllocatorState] = field(
        default_factory=lambda: [AllocatorState() for _ in range(DEPTH_COUNT)]
    )


@dataclass(frozen=True)
class DepthTrace:
    receiving_sites: Tuple[int, ...]
    active_sites: Tuple[int, ...]
    message_count: int


@dataclass(frozen=True)
class TokenTrace:
    position: int
    by_depth: Tuple[DepthTrace, ...]


@dataclass
class PartialTrace:
    position: int
    by_depth: List[DepthTrace] = field(default_factory=list)


@dataclass(frozen=True)
class ObservedSite:
    payload: Vector
    score: float


def embed(token: int, position: int, site: int) -> Vector:
    return tuple(
        tanh(
            0.17 * (token + 1) * (index + 1)
            + 0.03 * (position + 1)
            + 0.005 * (site + 1)
        )
        for index in range(DIM)
    )


def input_messages(token: int, position: int) -> List[Message]:
    """Toy dense expansion; a production model may use a forward tree."""

    return [
        Message(
            position=position,
            source_depth=-1,
            source_site=-1,
            target_site=site,
            source_slot=0,
            payload=embed(token, position, site),
        )
        for site in range(SITE_COUNT)
    ]


def merge_inbox(messages: Sequence[Message]) -> Dict[int, Vector]:
    """Merge each target inbox in stable source order."""

    by_target: Dict[int, List[Message]] = {}
    for message in messages:
        by_target.setdefault(message.target_site, []).append(message)

    merged: Dict[int, Vector] = {}
    for target, target_messages in by_target.items():
        ordered = sorted(
            target_messages,
            key=lambda message: (
                message.source_depth,
                message.source_site,
                message.source_slot,
                message.target_site,
            ),
        )
        merged[target] = vector_sum(message.payload for message in ordered)
    return merged


def observe_update_score(
    depth: int,
    site: int,
    payload: Vector,
    state: NodeState,
) -> ObservedSite:
    """Receive -> merge -> state update -> cheap score."""

    state.observer = 0.90 * state.observer + 0.10 * mean_abs(payload)
    normalized = rms_norm(payload)
    state.causal_total = add(state.causal_total, normalized)
    state.causal_count += 1
    semantic = alternating_projection(normalized, depth + site)
    score = semantic + 0.04 * state.observer
    return ObservedSite(payload=payload, score=score)


def update_load(current: float, selected: bool) -> float:
    indicator = 1.0 if selected else 0.0
    return LOAD_DECAY * current + (1.0 - LOAD_DECAY) * indicator


def allocate(
    observed: Mapping[int, ObservedSite],
    state: AllocatorState,
) -> Tuple[int, ...]:
    """Select one fixed backbone site plus at most one sparse site per group."""

    selected: List[int] = []
    group_count = SITE_COUNT // GROUP_SIZE
    for group in range(group_count):
        candidates = tuple(site for site in group_sites(group) if site in observed)
        if not candidates:
            continue

        backbone = backbone_for_group(group)
        fixed = (backbone,) if backbone in observed else ()
        remaining_budget = ACTIVE_BUDGET - len(fixed)
        optional = tuple(site for site in candidates if site not in fixed)
        average_load = sum(state.load[site] for site in group_sites(group)) / GROUP_SIZE
        priorities = {
            site: observed[site].score
            - LOAD_WEIGHT * (state.load[site] - average_load)
            for site in optional
        }
        selected.extend(fixed)
        selected.extend(top_k(priorities, min(remaining_budget, len(priorities))))

    selected_set = set(selected)
    for site in range(SITE_COUNT):
        state.load[site] = update_load(state.load[site], site in selected_set)
    return tuple(sorted(selected_set))


def active_compute(
    depth: int,
    site: int,
    observed: ObservedSite,
    state: NodeState,
) -> Vector:
    """Toy residual block used only for the selected sites."""

    causal_mean = scale(state.causal_total, 1.0 / state.causal_count)
    attention_delta = scale(causal_mean, 0.08 + 0.005 * depth)
    attention_merged = add(observed.payload, attention_delta)
    ffn_delta = tuple(
        0.06 * tanh(value + 0.002 * (site + 1))
        for value in rms_norm(attention_merged)
    )
    return add(attention_merged, ffn_delta)


def emit(
    position: int,
    depth: int,
    site: int,
    payload: Vector,
) -> List[Message]:
    """Emit to the next slice, or to output-boundary slots at final depth."""

    return [
        Message(
            position=position,
            source_depth=depth,
            source_site=site,
            target_site=target,
            source_slot=0,
            payload=scale(payload, 1.0 / len(line_neighbors(site))),
        )
        for target in line_neighbors(site)
    ]


def run_slice(
    depth: int,
    position: int,
    messages: Sequence[Message],
    state: RuntimeState,
) -> Tuple[List[Message], DepthTrace]:
    expected_source_depth = depth - 1
    if any(message.position != position for message in messages):
        raise ValueError("a slice inbox cannot mix input positions")
    if any(message.source_depth != expected_source_depth for message in messages):
        raise ValueError("message did not arrive from the preceding depth")

    merged = merge_inbox(messages)
    observed = {
        site: observe_update_score(
            depth,
            site,
            payload,
            state.node[depth][site],
        )
        for site, payload in sorted(merged.items())
    }
    active = allocate(observed, state.allocator[depth])

    outgoing: List[Message] = []
    for site in active:
        output = active_compute(
            depth,
            site,
            observed[site],
            state.node[depth][site],
        )
        outgoing.extend(emit(position, depth, site, output))

    trace = DepthTrace(
        receiving_sites=tuple(sorted(observed)),
        active_sites=active,
        message_count=len(outgoing),
    )
    return outgoing, trace


def readout(messages: Sequence[Message]) -> Vector:
    """Merge final outbound messages and read two fixed boundary slots."""

    merged = merge_inbox(messages)
    visible = [merged[site] for site in BACKBONE_SITES if site in merged]
    if not visible:
        return zeros()
    return scale(vector_sum(visible), 1.0 / len(visible))


class HBLineV0Reference:
    def __init__(self) -> None:
        self.state = RuntimeState()

    def forward_chunk(
        self,
        tokens: Sequence[int],
    ) -> Tuple[List[Vector], List[TokenTrace]]:
        """Depth-major execution: one slice receives the whole chunk."""

        start = self.state.next_position
        positions = tuple(range(start, start + len(tokens)))
        messages_by_token = [
            input_messages(token, position)
            for token, position in zip(tokens, positions)
        ]
        traces = [PartialTrace(position=position) for position in positions]

        for depth in range(DEPTH_COUNT):
            next_messages: List[List[Message]] = []
            for token_offset, position in enumerate(positions):
                outgoing, trace = run_slice(
                    depth,
                    position,
                    messages_by_token[token_offset],
                    self.state,
                )
                next_messages.append(outgoing)
                traces[token_offset].by_depth.append(trace)
            messages_by_token = next_messages

        outputs = [readout(messages) for messages in messages_by_token]
        self.state.next_position += len(tokens)
        return outputs, [
            TokenTrace(position=trace.position, by_depth=tuple(trace.by_depth))
            for trace in traces
        ]

    def forward_decode(
        self,
        tokens: Sequence[int],
    ) -> Tuple[List[Vector], List[TokenTrace]]:
        """Token-major execution: finish all slices before the next token."""

        outputs: List[Vector] = []
        traces: List[TokenTrace] = []
        for token in tokens:
            position = self.state.next_position
            messages = input_messages(token, position)
            by_depth: List[DepthTrace] = []
            for depth in range(DEPTH_COUNT):
                messages, trace = run_slice(
                    depth,
                    position,
                    messages,
                    self.state,
                )
                by_depth.append(trace)
            outputs.append(readout(messages))
            traces.append(TokenTrace(position=position, by_depth=tuple(by_depth)))
            self.state.next_position += 1
        return outputs, traces


def vectors_close(left: Sequence[Vector], right: Sequence[Vector]) -> bool:
    if len(left) != len(right):
        return False
    return all(
        abs(left_value - right_value) <= 1e-12
        for left_vector, right_vector in zip(left, right)
        for left_value, right_value in zip(left_vector, right_vector)
    )


def assert_equivalent(
    label: str,
    expected_output: Sequence[Vector],
    expected_trace: Sequence[TokenTrace],
    expected_state: RuntimeState,
    actual_output: Sequence[Vector],
    actual_trace: Sequence[TokenTrace],
    actual_state: RuntimeState,
) -> None:
    assert vectors_close(expected_output, actual_output), f"{label}: output mismatch"
    assert expected_trace == actual_trace, f"{label}: route artifact mismatch"
    assert expected_state == actual_state, f"{label}: state mismatch"


def run_demo(tokens: Sequence[int]) -> None:
    prefill = HBLineV0Reference()
    prefill_output, prefill_trace = prefill.forward_chunk(tokens)
    final_prefill_state = copy.deepcopy(prefill.state)

    decode = HBLineV0Reference()
    decode_output, decode_trace = decode.forward_decode(tokens)
    assert_equivalent(
        "chunk vs decode",
        prefill_output,
        prefill_trace,
        final_prefill_state,
        decode_output,
        decode_trace,
        decode.state,
    )

    for split in range(len(tokens) + 1):
        split_prefill = HBLineV0Reference()
        left_output, left_trace = split_prefill.forward_chunk(tokens[:split])
        right_output, right_trace = split_prefill.forward_chunk(tokens[split:])
        assert_equivalent(
            f"chunk composition at {split}",
            prefill_output,
            prefill_trace,
            final_prefill_state,
            left_output + right_output,
            left_trace + right_trace,
            split_prefill.state,
        )

    print("depth-major chunk == token-major decode: PASS")
    print("whole chunk == every two-chunk split: PASS")
    for trace in prefill_trace:
        route = " | ".join(
            f"d{depth}:{','.join(map(str, item.active_sites))}"
            for depth, item in enumerate(trace.by_depth)
        )
        print(f"t={trace.position}  {route}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tokens",
        nargs="*",
        type=int,
        default=[7, 1, 9, 3, 8],
        help="integer token ids used by the toy embedding",
    )
    arguments = parser.parse_args()
    run_demo(arguments.tokens)


if __name__ == "__main__":
    main()
