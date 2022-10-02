#################################################################################
#
#             Project Title:  Ground Truth Experiments
#             Date:           2022-04-30
#
#################################################################################


#################################################################################
#   Module Imports
#################################################################################

import os
import sys
import copy
from datetime import datetime

ROOT =os.path.abspath(os.path.join(__file__,"../../"))
sys.path.insert(1,ROOT)

import numpy as np
import torch
from collections import defaultdict

from seq_queries.model import get_model
from seq_queries.arguments import get_args, print_args
from seq_queries.train import load_checkpoint
from seq_queries.utils import write_pkl, write_json
from seq_queries.sample import lm_proposal, uniform_proposal, beam_search_lower_bound, mc_estimate, mc_pseudo_gt
from seq_queries.experiments import sample_dynamic_target_token, prep_experiment

#################################################################################
#   Function-Class Declaration
#################################################################################

device=0
sub_estimates = [10,30,50,100,300, 500,1000,3000,5000,10000]
intermediate_seqs = list(range(2,16))
model_budget = False
pseudo_gt = True
max_num_queries = 1000
query_2 = True
folders = ["importance_sampling"] if not pseudo_gt else ['pseudo_gt']
if query_2: folders = ["efficiency_ablation"]
datasets = ['shakespeare','apps','moocs','amazon']
config_path = "config/sample.yaml"

lengths = {

    # Short lengths
    "wikitext":[(h,15) for h in reversed(range(12,14,1))],
    "moocs":[(h,15) for h in reversed(range(12,14,1))],
    "amazon":[(h,15) for h in reversed(range(12,14,1))],
    "apps":[(h,15) for h in reversed(range(12,14,1))],
    "shakespeare":[(h,15) for h in reversed(range(12,14,1))],

}

for dataset_name in datasets:
    len_info = lengths[dataset_name]

    print("====="*10)
    print(f"* Running for dataset {dataset_name}")
    print("====="*10)
    extra_args = {"max_num_queries":max_num_queries}
    prep_dict = prep_experiment(config_path,
                                dataset_name,
                                device=device,
                                extra_args=extra_args)
    prep_dict['args'].text_dict['text'] = None
    args = prep_dict['args']
    args.sub_estimates = sub_estimates
    args.long_seq_ablation=False
    args.intermediate_seqs = intermediate_seqs
    val_dl = prep_dict['val_dl']
    model = prep_dict['model']
    text_dict = args.text_dict
    args.text_dict = None
    print_args(vars(args))
    args.text_dict = text_dict
    args.query_2 = query_2
    print("====="*10)

    for folder in folders:
        for hist_len,total_seq_len in len_info:
            args = copy.deepcopy(prep_dict['args'])
            args.estimate_type = mc_pseudo_gt if pseudo_gt else mc_estimate
            args.variance_epsilon = 1e-7
            args.max_num_mc_samples = 10000
            args.use_gpt2 = (dataset_name == 'wikitext')
            args.proposal_func = lm_proposal
            args.num_mc_samples = args.sub_estimates[-1] if not pseudo_gt else None
            args.hist_len = hist_len
            args.total_seq_len = total_seq_len

            if model_budget:
                args.model_budget_filepath = (f"{ROOT}" +
                                            f"data/beam_search_is_hybrid/{dataset_name}/val_dl/val-dl_" +
                    f"{dataset_name}_beam-search-is-hybrid_{args.hist_len}h_{args.total_seq_len}s_{args.num_mc_samples}mc" +
                    f"{f'_{max_num_queries}q' if max_num_queries else ''}.pkl")
                try:
                    assert os.path.exists(args.model_budget_filepath),\
                        f"Model budget filepath {args.model_budget_filepath} does not exist"
                except Exception as e:
                    print(args.model_budget_filepath)
                    print(e)
                    print("====="*10)
                    continue

            print("[{}] | Dataset: {} | Sample type: {} | Num samples: {} | Hist length {} | Total Seq Length {} | Pseudo GT: {} | Model Budget: {}"\
                  .format(datetime.now(),dataset_name,folder,args.num_mc_samples,args.hist_len,args.total_seq_len, pseudo_gt, model_budget))
            estimates = sample_dynamic_target_token(args, val_dl, model)
            os.makedirs(f"data/{folder}/{dataset_name}/val_dl/",exist_ok=True)
            estimates['metadata']['text_dict']['text'] = None
            args.sub_estimates = sub_estimates
            args.num_mc_samples = sub_estimates[-1]

            # for e,d in estimates.items():
            #     if isinstance(d, (torch.Tensor, torch.LongTensor)):
            #         print(e, d.shape)
            # sys.exit(1)

            write_pkl(estimates,
            f"data/{folder}/{dataset_name}/val_dl/val-dl_{dataset_name}_{folder.replace('_','-')}_" +
            f"{args.hist_len}h_{args.total_seq_len}s_{args.num_mc_samples}mc" +
            f"{'_' + 'model-budget' if args.model_budget_filepath else '_pgt' if pseudo_gt else ''}" +
            f"{f'_{max_num_queries}q' if max_num_queries else ''}.pkl")
            estimates=None
            print("====="*10)
