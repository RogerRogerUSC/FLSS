import argparse
import sys

import torch

sys.path.append("../../")

from fedlab.core.client import PassiveClientManager
from fedlab.core.network import DistNetwork
from pipeline.client_side import ExampleTrainer
from fedlab.contrib.dataset.pathological_mnist import PathologicalMNIST
from fedlab.models.mlp import MLP
from fedlab.board import fedboard
from fedlab.board.utils.roles import CLIENT_HOLDER

parser = argparse.ArgumentParser(description="Distbelief training example")

parser.add_argument("--ip", type=str, default="127.0.0.1")
parser.add_argument("--port", type=str, default="3002")
parser.add_argument("--world_size", type=int)
parser.add_argument("--rank", type=int)
parser.add_argument("--ethernet", type=str, default=None)

parser.add_argument("--lr", type=float, default=0.01)
parser.add_argument("--epochs", type=int, default=2)
parser.add_argument("--batch_size", type=int, default=100)

args = parser.parse_args()

if torch.cuda.is_available():
    args.cuda = True
else:
    args.cuda = False

model = MLP(784, 10)

fedboard.register(id='mtp-01', process_rank=args.rank, roles=CLIENT_HOLDER,
                  client_ids=[f'{args.rank}-{i}' for i in range(10)])

network = DistNetwork(address=(args.ip, args.port),
                      world_size=args.world_size,
                      rank=args.rank,
                      ethernet=args.ethernet)

trainer = ExampleTrainer(rank=args.rank, model=model, num_clients=10, cuda=args.cuda)

dataset = PathologicalMNIST(root='../../datasets/mnist/',
                            path="../../datasets/mnist/",
                            num_clients=100)

if args.rank == 1:
    dataset.preprocess()

trainer.setup_dataset(dataset)
trainer.setup_optim(args.epochs, args.batch_size, args.lr)

manager_ = PassiveClientManager(trainer=trainer, network=network)
manager_.run()
