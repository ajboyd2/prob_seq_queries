#################################################################################
#
#             Project Title:  Ground Truth Experiments
#             Author:         Sam Showalter
#             Date:           2022-04-30
#
#################################################################################


#################################################################################
#   Module Imports
#################################################################################

import os
import sys
import copy

sys.path.insert(1, '/home/showalte/research/prob_seq_queries/')

import numpy as np
import torch
from collections import defaultdict


from seq_queries.sample import sample
from seq_queries.model import get_model
from seq_queries.data import load_amazon_data, process_amazon_data, load_app_data, process_app_data
from seq_queries.arguments import get_args, print_args
from seq_queries.train import load_checkpoint
from seq_queries.utils import write_pkl
from seq_queries.sample import lm_proposal, uniform_proposal, beam_search_lower_bound, mc_estimate, beam_search_is_hybrid
from seq_queries.experiments import sample_dynamic_target_token, prep_experiment

#################################################################################
#   Function-Class Declaration
#################################################################################

device=4
num_mc_samples = 100000
folders = ["beam_search"]
datasets = ["shakespeare","amazon","apps"]
config_path = "config/testing/sample.yaml"
lengths_coverage = {
    "amazon":[(13,15,0.98),(12,15,0.95), (11,15,0.9),(10,15,0.85),(9,15,0.8)],
    "apps":[(13,15,0.98),(12,15,0.92), (11,15,0.87),(10,15,0.75)],
    "shakespeare":[(18,20,0.98),(17,20,0.95), (16,20,0.9),(15,20,0.85),(14,20,0.8)],
}

for dataset_name in datasets:
    len_info = lengths_coverage[dataset_name]
    print("====="*10)
    print(f"* Running for dataset {dataset_name}")
    print("====="*10)
    prep_dict = prep_experiment(config_path,
                                dataset_name,
                                device=device)
    args = prep_dict['args']
    val_dl = prep_dict['val_dl']
    model = prep_dict['model']
    args.estimate_type = beam_search_lower_bound
    args.proposal_func = lm_proposal
    text_dict = args.text_dict
    args.text_dict = None
    print_args(vars(args))
    args.text_dict = text_dict
    print("====="*10)

    for folder in folders:
        for hist_len,total_seq_len,coverage in len_info:
            args.hist_len = hist_len
            args.total_seq_len = total_seq_len
            args.num_beams = float(coverage)
            print("Dataset: {} | Sample type: {} | Num Beams: {} | Hist length {} | Total Seq Length {}"\
                  .format(dataset_name,folder,args.num_beams,args.hist_len,args.total_seq_len))
            estimates = sample_dynamic_target_token(args, val_dl, model)
            os.makedirs(f"data/{folder}/{dataset_name}/val_dl/",exist_ok=True)
            write_pkl(estimates,
                    f"data/{folder}/{dataset_name}/val_dl/val-dl_{dataset_name}_{folder.replace('_','-')}_{args.hist_len}h_{args.total_seq_len}s_{args.num_beams}b.pkl")
            print("====="*10)





#################################################################################
#   Main Method
#################################################################################


