# -*- coding: utf-8 -*-
import os
import glob
import re
import argparse
import logging
import datetime
import zipfile
import pandas


dict_re = re.compile("\{[^\{\}]+\}")
metircs_re = {'acc': re.compile("(?<=Accuracy: )\d+\.\d+(?=%)"), 
              'micro_f1': re.compile("(?<=Micro F1-score: )\d+\.\d+(?=%)")}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dataset', type=str, default='conll2003', 
                        help="dataset name")
    parser.add_argument('--format', type=str, default='xlsx', 
                        help="output format", choices=['xlsx', 'zip'])
    args = parser.parse_args()
    
    
    logging.basicConfig(level=logging.INFO, 
                        format="[%(asctime)s %(levelname)s] %(message)s", 
                        datefmt="%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger(__name__)
    
    logging_fns = glob.glob(f"cache/{args.dataset}/*/training.log")
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    
    if args.format == 'xlsx':
        exp_results = []
        for fn in logging_fns:
            with open(fn) as f:
                log_text = f.read()
                
            try:
                exp_res = dict_re.search(log_text).group()
                exp_res = eval(exp_res)
                exp_res['logging_timestamp'] = fn.split(os.path.sep)[2]
                
                num_metrics = 0
                for m_name, m_re in metircs_re.items():
                    metirc_list = m_re.findall(log_text)
                    curr_num_metrics, num_res = divmod(len(metirc_list), 2)
                    assert num_res == 0
                    num_metrics += curr_num_metrics
                    
                    for k in range(curr_num_metrics):
                        exp_res[f'dev_{m_name}_{k}'] = float(metirc_list[k])
                        exp_res[f'test_{m_name}_{k}'] = float(metirc_list[curr_num_metrics+k])
                
                if num_metrics == 0:
                    raise RuntimeError("Results not found")
                
            except:
                logger.warning(f"Failed to parse {fn}")
            else:
                exp_results.append(exp_res)
                
        df = pandas.DataFrame(exp_results)
        df.to_excel(f"cache/{args.dataset}-collected-{timestamp}.xlsx", index=False)
        
    elif args.format == 'zip':
        with zipfile.ZipFile(f"cache/{args.dataset}-collected-{timestamp}.zip", 'w') as zipf:
            for fn in logging_fns:
                zipf.write(fn, fn.split('/', 1)[1])
            
    