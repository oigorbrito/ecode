import argparse
import glob
import os

from matplotlib import pyplot as plt

from analysis.visualize_archive import get_performance_score
from utils.evo_utils import load_ecode_metadata


def get_run_info(run_dir):
    """Load evolution metadata from a run directory."""
    metadata_path = os.path.join(run_dir, "ecode_metadata.jsonl")
    if not os.path.isfile(metadata_path):
        candidates = glob.glob(os.path.join(run_dir, "*.jsonl"))
        if len(candidates) != 1:
            raise FileNotFoundError(
                f"Expected ecode_metadata.jsonl or one metadata JSONL file in {run_dir}"
            )
        metadata_path = candidates[0]
    archives = load_ecode_metadata(metadata_path)

    iterations = [0]
    best_scores = [get_performance_score(run_dir, "initial")]
    avg_scores = [best_scores[0]]
    total_scores = [best_scores[0]]
    for archive in archives:
        children = archive["children"]
        children_compiled = archive["children_compiled"]
        for node_id in children:
            score = get_performance_score(run_dir, node_id)
            iterations.append(len(best_scores))
            best_scores.append(max(score, best_scores[-1]))
            if node_id in children_compiled:
                total_compiled_score = avg_scores[-1] * len(avg_scores) + score
                avg_scores.append(total_compiled_score / (len(avg_scores) + 1))
            else:
                avg_scores.append(avg_scores[-1])
            total_scores.append(total_scores[-1] + score)

    return iterations, {"best": best_scores, "avg": avg_scores, "total": total_scores}


def make_plot(all_iterations, all_infos, info_label, all_its=False):
    if not all_iterations:
        raise ValueError("Provide at least one run directory to compare.")
    if info_label == "best":
        plt.axhline(
            y=0.51, color="#DB4437", linestyle="--", label="Published open-source reference"
        )

    labels = {
        "seed": ("Seed baseline", "#4285F4"),
        "no_self_improvement": ("Without self-improvement", "#0F9D58"),
        "limited_exploration": ("Limited exploration", "#F4B400"),
        "greedy": ("Greedy search", "#673AB7"),
    }
    min_length = min(len(values) for values in all_iterations.values())
    for run_type, (label, color) in labels.items():
        if run_type not in all_iterations:
            continue
        iterations = all_iterations[run_type]
        values = all_infos[run_type][info_label]
        if not all_its:
            iterations, values = iterations[:min_length], values[:min_length]
        plt.plot(iterations, values, marker=".", color=color, label=label)

    y_label = "Best agent benchmark score" if info_label == "best" else info_label
    plt.xlabel("Iterations", fontsize=15)
    plt.ylabel(y_label, fontsize=15)
    plt.grid()
    plt.legend(fontsize=12)
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    os.makedirs("./analysis/output", exist_ok=True)
    for extension, options in (("png", {}), ("pdf", {"transparent": True})):
        output = f"./analysis/output/ecode_comparisons_{info_label}.{extension}"
        plt.savefig(output, **options)
        print(f"Comparison plot saved at {output}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Compare ECode runs and evaluation baselines.")
    parser.add_argument("--path_seed", help="Path to the seed baseline run.")
    parser.add_argument("--path_no_self_improvement", help="Path to a run without self-improvement.")
    parser.add_argument("--path_limited_exploration", help="Path to a run with limited exploration.")
    parser.add_argument("--path_greedy", help="Path to a greedy-search run.")
    parser.add_argument("--all_its", action="store_true", help="Plot every iteration.")
    args = parser.parse_args()

    run_paths = {
        "seed": args.path_seed,
        "no_self_improvement": args.path_no_self_improvement,
        "limited_exploration": args.path_limited_exploration,
        "greedy": args.path_greedy,
    }
    all_iterations, all_infos = {}, {}
    for run_type, run_path in run_paths.items():
        if run_path:
            all_iterations[run_type], all_infos[run_type] = get_run_info(run_path)

    for metric in ("best", "avg", "total"):
        make_plot(all_iterations, all_infos, metric, all_its=args.all_its)


if __name__ == "__main__":
    main()
