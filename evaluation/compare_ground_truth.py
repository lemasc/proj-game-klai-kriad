#!/usr/bin/env python3
"""
Compare automated punch detections with ground truth observations.

This script analyzes the accuracy of the automated detection system by comparing
detections.jsonl with ground_truth.jsonl from a recording session.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class PunchEvent:
    """Represents a punch event (detection or ground truth)."""
    timestamp: float
    hand: str
    source: str  # 'detection' or 'peer'
    confidence: Optional[float] = None


@dataclass
class MatchResult:
    """Result of matching a ground truth event with detections."""
    ground_truth: PunchEvent
    matched_detection: Optional[PunchEvent] = None
    time_diff: Optional[float] = None


def load_detections(session_dir: Path) -> List[PunchEvent]:
    """Load punch detections from detections.jsonl.

    Args:
        session_dir: Path to session directory

    Returns:
        List of PunchEvent objects from automated detection
    """
    detections_path = session_dir / "detections.jsonl"

    if not detections_path.exists():
        print(f"Warning: No detections.jsonl found in {session_dir}")
        return []

    events = []
    with open(detections_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            if data.get('type') == 'punch':
                events.append(PunchEvent(
                    timestamp=data['timestamp'],
                    hand=data['hand'],
                    source='detection',
                    confidence=data.get('confidence')
                ))

    return sorted(events, key=lambda e: e.timestamp)


def load_ground_truth(session_dir: Path) -> List[PunchEvent]:
    """Load ground truth events from ground_truth.jsonl.

    Args:
        session_dir: Path to session directory

    Returns:
        List of PunchEvent objects from peer observations
    """
    ground_truth_path = session_dir / "ground_truth.jsonl"

    if not ground_truth_path.exists():
        print(f"Warning: No ground_truth.jsonl found in {session_dir}")
        return []

    events = []
    with open(ground_truth_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            events.append(PunchEvent(
                timestamp=data['timestamp'],
                hand=data['hand'],
                source=data.get('source', 'peer')
            ))

    return sorted(events, key=lambda e: e.timestamp)


def match_events(
    detections: List[PunchEvent],
    ground_truth: List[PunchEvent],
    match_window: float = 0.3,
    offset: float = 0.0
) -> Tuple[List[MatchResult], List[PunchEvent], int, int, int]:
    """Match ground truth events with detections within a time window.

    Args:
        detections: List of automated detection events
        ground_truth: List of ground truth events
        match_window: Time window for matching (±seconds)
        offset: Time offset to apply to ground truth (seconds)

    Returns:
        Tuple of (matched_results, unmatched_detections, TP, FP, FN)
    """
    # Apply offset to ground truth timestamps
    adjusted_ground_truth = [
        PunchEvent(
            timestamp=gt.timestamp + offset,
            hand=gt.hand,
            source=gt.source
        )
        for gt in ground_truth
    ]

    matched_results = []
    used_detections = set()

    # For each ground truth event, find the closest detection within the window
    for gt in adjusted_ground_truth:
        best_match = None
        best_time_diff = None
        best_detection_idx = None

        for idx, det in enumerate(detections):
            if idx in used_detections:
                continue

            time_diff = det.timestamp - gt.timestamp

            # Check if within match window and same hand
            if abs(time_diff) <= match_window and det.hand == gt.hand:
                if best_match is None or abs(time_diff) < abs(best_time_diff):
                    best_match = det
                    best_time_diff = time_diff
                    best_detection_idx = idx

        if best_match:
            used_detections.add(best_detection_idx)
            matched_results.append(MatchResult(
                ground_truth=gt,
                matched_detection=best_match,
                time_diff=best_time_diff
            ))
        else:
            # No matching detection found (False Negative)
            matched_results.append(MatchResult(ground_truth=gt))

    # Find unmatched detections (False Positives)
    unmatched_detections = [
        det for idx, det in enumerate(detections)
        if idx not in used_detections
    ]

    # Calculate TP, FP, FN
    true_positives = sum(1 for mr in matched_results if mr.matched_detection is not None)
    false_negatives = sum(1 for mr in matched_results if mr.matched_detection is None)
    false_positives = len(unmatched_detections)

    return matched_results, unmatched_detections, true_positives, false_positives, false_negatives


def calculate_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
    """Calculate precision, recall, and F1 score.

    Args:
        tp: True positives
        fp: False positives
        fn: False negatives

    Returns:
        Dictionary with precision, recall, and F1 score
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1
    }


def generate_report(
    session_dir: Path,
    matched_results: List[MatchResult],
    unmatched_detections: List[PunchEvent],
    tp: int,
    fp: int,
    fn: int,
    metrics: Dict[str, float],
    match_window: float,
    offset: float
) -> str:
    """Generate a detailed markdown report.

    Args:
        session_dir: Path to session directory
        matched_results: List of match results
        unmatched_detections: List of false positive detections
        tp: True positives
        fp: False positives
        fn: False negatives
        metrics: Calculated metrics
        match_window: Match window used
        offset: Offset used

    Returns:
        Markdown formatted report string
    """
    report = []
    report.append(f"# Ground Truth Comparison Report\n")
    report.append(f"**Session**: `{session_dir.name}`\n")
    report.append(f"**Match Window**: ±{match_window}s\n")
    report.append(f"**Time Offset**: {offset:+.3f}s\n")
    report.append("")

    # Summary metrics
    report.append("## Summary Metrics\n")
    report.append(f"- **Precision**: {metrics['precision']:.2%} ({tp}/{tp+fp} detections were correct)")
    report.append(f"- **Recall**: {metrics['recall']:.2%} ({tp}/{tp+fn} ground truth events were detected)")
    report.append(f"- **F1 Score**: {metrics['f1_score']:.3f}")
    report.append("")
    report.append(f"- **True Positives (TP)**: {tp}")
    report.append(f"- **False Positives (FP)**: {fp}")
    report.append(f"- **False Negatives (FN)**: {fn}")
    report.append("")

    # Matched events
    if matched_results:
        report.append("## Matched Events\n")
        successful_matches = [mr for mr in matched_results if mr.matched_detection is not None]

        if successful_matches:
            report.append("| Ground Truth Time | Detection Time | Time Diff | Hand |")
            report.append("|-------------------|----------------|-----------|------|")
            for mr in successful_matches:
                report.append(
                    f"| {mr.ground_truth.timestamp:6.3f}s | "
                    f"{mr.matched_detection.timestamp:6.3f}s | "
                    f"{mr.time_diff:+.3f}s | "
                    f"{mr.ground_truth.hand} |"
                )
            report.append("")

            # Time difference statistics
            time_diffs = [mr.time_diff for mr in successful_matches]
            avg_diff = sum(time_diffs) / len(time_diffs)
            report.append(f"**Average Time Difference**: {avg_diff:+.3f}s")
            report.append("")

    # False Negatives
    false_negatives = [mr for mr in matched_results if mr.matched_detection is None]
    if false_negatives:
        report.append("## False Negatives (Missed Detections)\n")
        report.append("Ground truth events that were NOT detected:\n")
        report.append("| Time | Hand |")
        report.append("|------|------|")
        for mr in false_negatives:
            report.append(f"| {mr.ground_truth.timestamp:6.3f}s | {mr.ground_truth.hand} |")
        report.append("")

    # False Positives
    if unmatched_detections:
        report.append("## False Positives (Extra Detections)\n")
        report.append("Detections that did NOT match any ground truth:\n")
        report.append("| Time | Hand | Confidence |")
        report.append("|------|------|------------|")
        for det in unmatched_detections:
            conf_str = f"{det.confidence:.3f}" if det.confidence is not None else "N/A"
            report.append(f"| {det.timestamp:6.3f}s | {det.hand} | {conf_str} |")
        report.append("")

    # Tuning suggestions
    report.append("## Tuning Suggestions\n")
    if false_negatives and not unmatched_detections:
        report.append("- **High False Negatives, Low False Positives**: Detection threshold may be too strict. Consider lowering thresholds.")
    elif unmatched_detections and not false_negatives:
        report.append("- **High False Positives, Low False Negatives**: Detection may be too sensitive. Consider raising thresholds.")
    elif false_negatives and unmatched_detections:
        successful_matches = [mr for mr in matched_results if mr.matched_detection is not None]
        if successful_matches:
            time_diffs = [mr.time_diff for mr in successful_matches]
            avg_diff = sum(time_diffs) / len(time_diffs)
            if abs(avg_diff) > 0.05:  # More than 50ms systematic delay
                report.append(f"- **Systematic Time Offset**: Average difference is {avg_diff:+.3f}s. Try using `--offset {-avg_diff:.3f}`")
        report.append("- **Both FP and FN present**: Review detection parameters and ground truth accuracy.")
    else:
        report.append("- **Perfect Detection**: All ground truth events matched with no false positives!")

    report.append("")

    # Hand-specific breakdown
    hand_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    for mr in matched_results:
        hand = mr.ground_truth.hand
        if mr.matched_detection:
            hand_stats[hand]['tp'] += 1
        else:
            hand_stats[hand]['fn'] += 1

    for det in unmatched_detections:
        hand_stats[det.hand]['fp'] += 1

    if hand_stats:
        report.append("## Performance by Hand\n")
        report.append("| Hand | TP | FP | FN | Precision | Recall |")
        report.append("|------|----|----|----|-----------| -------|")
        for hand in sorted(hand_stats.keys()):
            stats = hand_stats[hand]
            tp_h = stats['tp']
            fp_h = stats['fp']
            fn_h = stats['fn']
            prec = tp_h / (tp_h + fp_h) if (tp_h + fp_h) > 0 else 0.0
            rec = tp_h / (tp_h + fn_h) if (tp_h + fn_h) > 0 else 0.0
            report.append(f"| {hand} | {tp_h} | {fp_h} | {fn_h} | {prec:.2%} | {rec:.2%} |")
        report.append("")

    return "\n".join(report)


def main():
    """Main entry point for the comparison script."""
    parser = argparse.ArgumentParser(
        description="Compare automated punch detections with ground truth observations"
    )
    parser.add_argument(
        "--session",
        type=Path,
        required=True,
        help="Path to session directory containing detections.jsonl and ground_truth.jsonl"
    )
    parser.add_argument(
        "--match-window",
        type=float,
        default=0.3,
        help="Time window for matching events in seconds (default: 0.3)"
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="Time offset to apply to ground truth in seconds (default: 0.0)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for report (default: print to console)"
    )

    args = parser.parse_args()

    # Validate session directory
    if not args.session.exists():
        print(f"Error: Session directory not found: {args.session}")
        return 1

    # Load data
    print(f"Loading data from {args.session}...")
    detections = load_detections(args.session)
    ground_truth = load_ground_truth(args.session)

    print(f"Loaded {len(detections)} detections and {len(ground_truth)} ground truth events")

    if not ground_truth:
        print("Error: No ground truth data found. Cannot perform comparison.")
        return 1

    # Match events
    print(f"Matching events (window: ±{args.match_window}s, offset: {args.offset:+.3f}s)...")
    matched_results, unmatched_detections, tp, fp, fn = match_events(
        detections,
        ground_truth,
        match_window=args.match_window,
        offset=args.offset
    )

    # Calculate metrics
    metrics = calculate_metrics(tp, fp, fn)

    # Generate report
    report = generate_report(
        args.session,
        matched_results,
        unmatched_detections,
        tp, fp, fn,
        metrics,
        args.match_window,
        args.offset
    )

    # Output report
    if args.output:
        args.output.write_text(report)
        print(f"\nReport saved to: {args.output}")
    else:
        print("\n" + "="*80)
        print(report)
        print("="*80)

    # Print quick summary
    print(f"\n✓ Precision: {metrics['precision']:.2%}")
    print(f"✓ Recall: {metrics['recall']:.2%}")
    print(f"✓ F1 Score: {metrics['f1_score']:.3f}")

    return 0


if __name__ == "__main__":
    exit(main())
