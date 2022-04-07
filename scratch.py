#################################################################################
#
#             Project Title:  Scratch Work
#             Author:         Sam Showalter
#             Date:           2022-03-25
#
#################################################################################


#################################################################################
#   Module Imports
#################################################################################

import os
import sys
import copy

import numpy as np
import torch

# from experiments.train.shakespeare import main as shakespeare_main
# from experiments.train.stacks import main as stacks_main

from seq_queries.sample import sample, evaluate_samples
from seq_queries.model import get_model
from seq_queries.data import load_text, process_data
from seq_queries.arguments import get_args
from seq_queries.train import load_checkpoint
from seq_queries.utils import write_pkl
#################################################################################
#   Function-Class Declaration
#################################################################################


if __name__ == "__main__":

    args = get_args(manual_config="config/testing/sample.yaml")
    text_dict= load_text(args.data_path)
    args.text_dict = text_dict
    print(text_dict['char_to_id'])
    train_dl, val_dl, test_dl = process_data(text_dict, args)
    model = get_model(args)
    if args.checkpoint_path:
        load_checkpoint(args, model)
    model.eval()
    output = sample(val_dl, args, model)

    # print(output['seqs'][0].shape)
    # print([''.join([text_dict['id_to_char'][c]
    #                 for c in output['seqs'][0][i,:].tolist()])
    #                for i in range(min(5,output['seqs'][0].shape[0]))]
    #         )

    estimates_or_lbs = evaluate_samples(args, model, output)
    plot_estimates = [est_lbs[0].item() for est_lbs in estimates_or_lbs]
    # print(len(plot_estimates), plot_estimates)
    # write_pkl(plot_estimates,"data/importance_sampling/shakespeare/mc_importance_estimate-a_rt-t_hou?_1000s_1024m.pkl")




#################################################################################
#   Main Method
#################################################################################



