# -*- coding: utf-8 -*-
import pytest
import glob
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from transformers import BertTokenizer, BertForMaskedLM
from transformers import RobertaTokenizer, RobertaForMaskedLM

from eznlp.sequence_tagging.raw_data import ConllReader
from eznlp.language_modeling import MLMDataset, PMCMLMDataset, MLMTrainer


@pytest.fixture
def BERT4MLM_with_tokenizer():
    tokenizer = BertTokenizer.from_pretrained("assets/transformers_cache/bert-base-cased")
    bert4mlm = BertForMaskedLM.from_pretrained("assets/transformers_cache/bert-base-cased")
    return bert4mlm, tokenizer

@pytest.fixture
def RoBERTa4MLM_with_tokenizer():
    tokenizer = RobertaTokenizer.from_pretrained("assets/transformers_cache/roberta-base")
    roberta4mlm = RobertaForMaskedLM.from_pretrained("assets/transformers_cache/roberta-base")
    return roberta4mlm, tokenizer


class TestMLM(object):
    def test_covid19_mlm(self, BERT4MLM_with_tokenizer, device):
        bert4mlm, tokenizer = BERT4MLM_with_tokenizer
        bert4mlm = bert4mlm.to(device)
        
        reader = ConllReader(text_col_id=0, tag_col_id=3, scheme='BIO1')
        train_data = reader.read("assets/data/conll2003/eng.train")
        train_set = MLMDataset(train_data, tokenizer)
        batch = [train_set[i] for i in range(4)]
        batch012 = train_set.collate(batch[:3]).to(device)
        batch123 = train_set.collate(batch[1:]).to(device)
        
        loss012, MLM_scores012 = bert4mlm(input_ids=batch012.MLM_tok_ids, 
                                          attention_mask=(~batch012.attention_mask).type(torch.long), 
                                          labels=batch012.MLM_lab_ids)
        loss123, MLM_scores123 = bert4mlm(input_ids=batch123.MLM_tok_ids, 
                                          attention_mask=(~batch123.attention_mask).type(torch.long), 
                                          labels=batch123.MLM_lab_ids)
        
        min_step = min(MLM_scores012.size(1), MLM_scores123.size(1))
        delta_MLM_scores = MLM_scores012[1:, :min_step] - MLM_scores123[:-1, :min_step]
        assert delta_MLM_scores.abs().max().item() < 1e-4
        
        optimizer = optim.AdamW(bert4mlm.parameters())
        trainer = MLMTrainer(bert4mlm, optimizer=optimizer, device=device)
        trainer.train_epoch([batch012])
        trainer.eval_epoch([batch012])
        
        
    def test_PMC_mlm(self, RoBERTa4MLM_with_tokenizer, device):
        roberta4mlm, tokenizer = RoBERTa4MLM_with_tokenizer
        roberta4mlm = roberta4mlm.to(device)
        
        files = glob.glob("assets/data/PMC/comm_use/Cells/*.txt")
        train_set = PMCMLMDataset(files=files, tokenizer=tokenizer, max_len=128)
        train_loader = DataLoader(train_set, batch_size=4, collate_fn=train_set.collate)
        for batch in train_loader:
            batch = batch.to(device)
            break
        
        loss012, MLM_scores012 = roberta4mlm(input_ids=batch.MLM_tok_ids[:3], 
                                             attention_mask=(~batch.attention_mask[:3]).type(torch.long), 
                                             labels=batch.MLM_lab_ids[:3])
        loss123, MLM_scores123 = roberta4mlm(input_ids=batch.MLM_tok_ids[1:], 
                                             attention_mask=(~batch.attention_mask[1:]).type(torch.long), 
                                             labels=batch.MLM_lab_ids[1:])
        
        min_step = min(MLM_scores012.size(1), MLM_scores123.size(1))
        delta_MLM_scores = MLM_scores012[1:, :min_step] - MLM_scores123[:-1, :min_step]
        assert delta_MLM_scores.abs().max().item() < 1e-4
        
        optimizer = optim.AdamW(roberta4mlm.parameters(), lr=1e-4)
        trainer = MLMTrainer(roberta4mlm, optimizer=optimizer, device=device)
        trainer.train_epoch([batch])
        trainer.eval_epoch([batch])
        
        # trainer.train_steps(train_loader=[batch, batch], 
        #                     eval_loader=[batch, batch], 
        #                     n_epochs=10, disp_every_steps=2, eval_every_steps=6)
        
        