import os
import csv
import dataclasses
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="PyTorch MNIST trainning")
parser.add_argument(
    "--sampling_type",
    type=str,
    default="beta",
)
parser.add_argument("--alpha", type=float, default=0.5)
args = parser.parse_args()


@dataclasses.dataclass
class Params:
    sampling_type: str
    q: float
    alpha: float
    num_clients: int


def parse_filename(filename: str) -> Params:
    tokens = filename.replace(".csv", "").split("+")
    params = Params(
        sampling_type=tokens[0].replace("run-mnist_", ""),
        q=float(tokens[1].replace("q_", "")),
        alpha=float(tokens[2].replace("alpha_", "")),
        num_clients=int(
            tokens[3].replace("num_clients_", "").replace("-tag-Accuracy_test", "")
        ),
    )
    return params


fig, ax = plt.subplots(figsize=(6, 5))
plt.rc("font", size=12)
markers = "os*xdXDHhPp12348<>"
k = 0
filenames = os.listdir("results/alpha_" + str(args.alpha) + "/")


for filename in filenames:
    params = parse_filename(filename)
    print(params.sampling_type)
    # Select sampling_type to plot
    if args.sampling_type in params.sampling_type or params.sampling_type == "uniform":
        df = pd.read_csv("results/alpha_" + str(args.alpha) + "/" + filename)
        if "_" in params.sampling_type:
            ax.plot(
                df["Step"],
                df["Value"],
                label=params.sampling_type + ",q=" + str(params.q),
                marker=markers[k],
                linewidth="1.1",
                markersize=3,
                markevery=2,
            )
        else:
            ax.plot(
                df["Step"],
                df["Value"],
                label=params.sampling_type,
                marker=markers[k],
                linewidth="1.1",
                markersize=3,
                markevery=2,
            )
        k += 1


plt.xlabel("Communication Round", fontsize=12)
plt.ylabel("Accuracy", fontsize=12)
plt.title("dataset=MNIST, alpha=" + str(args.alpha) + ", num_clients=100")
plt.grid("on")
plt.tight_layout()
plt.savefig(
    os.path.join(
        "figures", args.sampling_type + "_multi_q_alpha_" + str(args.alpha) + ".pdf"
    )
)
plt.legend()
plt.show()
