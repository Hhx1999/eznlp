# -*- coding: utf-8 -*-
from collections import OrderedDict, Counter
import argparse
import logging
import glob
import re
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import spacy
import jieba
import torch
import torchtext
import torchvision

import allennlp.modules
import transformers
import flair

import eznlp
from eznlp import auto_device
from eznlp.utils import find_ascending, ChunksTagsTranslator
from eznlp.token import Token, TokenSequence, LexiconTokenizer
from eznlp.metrics import precision_recall_f1_report
from eznlp.vocab import Vocab
from eznlp.vectors import Vectors, GloVe, Senna
from eznlp.wrapper import Batch

from eznlp.io import TabularIO, CategoryFolderIO, ConllIO, BratIO, JsonIO, SQuADIO, ChipIO, KarpathyIO, Src2TrgIO, RawTextIO
from eznlp.io import PostIO

from eznlp.dataset import Dataset, GenerationDataset

from eznlp.nn import SinusoidPositionalEncoding

from eznlp.config import ConfigList, ConfigDict
from eznlp.model import OneHotConfig, MultiHotConfig, EncoderConfig
from eznlp.model import NestedOneHotConfig, CharConfig, SoftLexiconConfig
from eznlp.model import ELMoConfig, BertLikeConfig, FlairConfig
from eznlp.model import ImageEncoderConfig
from eznlp.model.bert_like import truncate_for_bert_like

from eznlp.model import (TextClassificationDecoderConfig, 
                         SequenceTaggingDecoderConfig, 
                         SpanClassificationDecoderConfig, 
                         SpanAttrClassificationDecoderConfig, 
                         SpanRelClassificationDecoderConfig, 
                         BoundarySelectionDecoderConfig, 
                         JointExtractionDecoderConfig, 
                         GeneratorConfig)
from eznlp.model import ExtractorConfig, Text2TextConfig, Image2TextConfig

from eznlp.training import Trainer
from eznlp.training import collect_params, check_param_groups, LRLambda



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    device = auto_device()
    
    # with open("data/multi30k/train.de", encoding='utf-8') as f:
    #     txt = f.readlines()
    #     print(len(txt))

    # batch_tokenized_raw_text = [["I", "like", "it", "."], 
    #                             ["Do", "you", "love", "me", "?"], 
    #                             ["Sure", "!"], 
    #                             ["Future", "it", "out"]]
    
    
    # flair_fw_lm = flair.models.LanguageModel.load_language_model("assets/flair/news-forward-0.4.1.pt")
    # flair_bw_lm = flair.models.LanguageModel.load_language_model("assets/flair/news-backward-0.4.1.pt")
    
    # options_file = "assets/allennlp/elmo_2x1024_128_2048cnn_1xhighway_options.json"
    # weight_file = "assets/allennlp/elmo_2x1024_128_2048cnn_1xhighway_weights.hdf5"
    # elmo = allennlp.modules.Elmo(options_file, weight_file, 1)
    # batch_elmo_ids = allennlp.modules.elmo.batch_to_ids(batch_tokenized_raw_text)
    
    # bert = transformers.BertModel.from_pretrained("assets/transformers/bert-base-uncased")
    # tokenizer = transformers.BertTokenizer.from_pretrained("assets/transformers/bert-base-uncased")
    
    # glove = GloVe("assets/vectors/glove.6B.100d.txt", encoding='utf-8')
    # senna = Senna("assets/vectors/Senna")
    
    # ctb50d = Vectors.load("assets/vectors/ctb.50d.vec", encoding='utf-8')
    # giga_uni = Vectors.load("assets/vectors/gigaword_chn.all.a2b.uni.ite50.vec", encoding='utf-8')
    # giga_bi  = Vectors.load("assets/vectors/gigaword_chn.all.a2b.bi.ite50.vec", encoding='utf-8')
    # # tencent = Vectors.load("assets/vectors/tencent/Tencent_AILab_ChineseEmbedding.txt", encoding='utf-8', skiprows=0, verbose=True)
    
    # conll_io = ConllIO(text_col_id=0, tag_col_id=3, scheme='BIO2')
    # train_data = conll_io.read("data/conll2003/demo.eng.train")
    # dev_data   = conll_io.read("data/conll2003/demo.eng.testa")
    # test_data  = conll_io.read("data/conll2003/demo.eng.testb")
    
    # config = ExtractorConfig('sequence_tagging', 
    #                          ohots=ConfigDict({'text': OneHotConfig(field='text', vectors=glove)}), 
    #                          nested_ohots=ConfigDict({'char': CharConfig()}), 
    #                          elmo=ELMoConfig(elmo=elmo), 
    #                          bert_like=BertLikeConfig(tokenizer=tokenizer, bert_like=bert), 
    #                          flair_fw=FlairConfig(flair_lm=flair_fw_lm), 
    #                          flair_bw=FlairConfig(flair_lm=flair_bw_lm))
    
    # train_set = Dataset(train_data, config)
    # train_set.build_vocabs_and_dims(dev_data, test_data)
    # model = config.instantiate()
    
    # batch = train_set.collate([train_set[i] for i in range(0, 4)])
    # losses, states = model(batch, return_states=True)
    
    # optimizer = torch.optim.AdamW(model.parameters())
    # trainer = Trainer(model, optimizer=optimizer, device=device)
    # res = trainer.train_epoch([batch])
    
    # for model_name in ["hfl/chinese-macbert-base", "hfl/chinese-macbert-large"]:
    #     logging.info(f"Start downloading {model_name}...")
    #     tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
    #     model = transformers.AutoModelForPreTraining.from_pretrained(model_name)
    #     tokenizer.save_pretrained(f"assets/transformers/{model_name}")
    #     model.save_pretrained(f"assets/transformers/{model_name}")
    
    # TODO: Test the MLM model pretrained on HwaMei corpus
    PATH = "assets/transformers/syuoni/bert-base-chinese-vf"
    # PATH = "assets/transformers/syuoni/bert-base-jt-20e"
    bert = transformers.BertForMaskedLM.from_pretrained(PATH)
    tokenizer = transformers.BertTokenizer.from_pretrained(PATH)
    # unmasker = transformers.pipeline("fill-mask", tokenizer=tokenizer, model=bert)
    
    # io = RawTextIO(encoding='utf-8')
    # data = io.read("data/Wikipedia/text-zh/AA/wiki_00.cache")
    