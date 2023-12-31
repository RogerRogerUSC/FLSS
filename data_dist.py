import math
import torch
import numpy as np
from torch.utils.data import Sampler
# from sinkhorn_knopp import sinkhorn_knopp as skp


def get_data_sampler(dataset, args, rank):
    # Sample data with uniform distribution
    if args.data_dist == "uniform":
        sampler = torch.utils.data.DistributedSampler(
            dataset, num_replicas=args.num_clients, rank=rank, shuffle=True
        )
        return sampler
    # Sample data with Dirichlet distribution
    elif args.data_dist == "dirichlet":
        sampler = DirichletSampler(
            dataset=dataset,
            size=args.num_clients,
            rank=rank,
            alpha=args.alpha,
        )
        return sampler
    else:
        raise Exception("Unsupported Data Distribution. ")


class DirichletSampler(Sampler):
    def __init__(self, dataset, *, size, rank, alpha, random_seed=42, shuffle=True):
        self.dataset = dataset
        if isinstance(dataset.targets, torch.Tensor):
            self.labels = set(dataset.targets.numpy())
        else:
            self.labels = set(dataset.targets)
        if not list(sorted(self.labels)) == list(range(len(self.labels))):
            raise ValueError(
                "Please re-map the labels of dataset into "
                "0 to num_classes-1 integers."
            )
        self.size = size
        self.rank = rank

        # Group the index of same label together
        self.indices_per_label = [[] for _ in range(len(self.labels))]

        for index, label in enumerate(self.dataset.targets):
            self.indices_per_label[label].append(index)

        # Make it into numpy and shuffle if needed
        for i in range(len(self.indices_per_label)):
            if shuffle:
                self.indices_per_label[i] = np.random.permutation(
                    self.indices_per_label[i]
                )
            else:
                self.indices_per_label[i] = np.array(self.indices_per_label[i])

        # Generate the dirichlet dist for each class of all agents
        # IMPORTANT: we need to make sure all agents use the same random seed.
        rng = np.random.default_rng(random_seed)
        # This is a matrix with dimension "size * num_classes"
        self.full_class_prob = rng.dirichlet(alpha * np.ones(len(self.labels)), size)

        # To convert an non-negative square matrix with total support into a doubly stochastic matrix.
        # sk = skp.SinkhornKnopp()
        # doubly_stochastic_matrix = sk.fit(self.full_class_prob)

        # Prepare the dataset via the partition according to the prob.
        self.my_index = []
        for label in self.labels:
            cum_prob = np.cumsum(self.full_class_prob[:, label])
            normalized_cum_prob = (cum_prob / cum_prob[-1]).tolist()
            label_indices = self.indices_per_label[label]
            start_prob = 0 if rank == 0 else normalized_cum_prob[rank - 1]
            end_prob = normalized_cum_prob[rank]
            my_index_start = math.floor(start_prob * len(label_indices))
            my_index_end = math.floor(end_prob * len(label_indices))
            self.my_index.extend(label_indices[my_index_start:my_index_end])
        self.my_index = np.random.permutation(self.my_index)

    def __iter__(self):
        return iter(self.my_index)

    def __len__(self):
        return len(self.my_index)
