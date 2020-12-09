# -*- coding: utf-8 -*-
from eznlp.sequence_tagging.raw_data import ConllReader


class TestRawData(object):
    """
    References
    ----------
    [1] Huang et al. 2015. Bidirectional LSTM-CRF models for sequence tagging. 
    [2] Chiu and Nichols. 2016. Named entity recognition with bidirectional LSTM-CNNs.
    [3] Jie and Lu. 2019. Dependency-guided LSTM-CRF for named entity recognition. 
    """
    def test_conll2003(self):
        reader = ConllReader(text_col_id=0, tag_col_id=3, scheme='BIO1', additional_col_id2name={1: 'pos_tag'})
        train_data = reader.read("assets/data/conll2003/eng.train")
        val_data   = reader.read("assets/data/conll2003/eng.testa")
        test_data  = reader.read("assets/data/conll2003/eng.testb")
        
        assert len(train_data) == 14_987
        assert sum(len(ex['chunks']) for ex in train_data) == 23_499
        assert sum(len(ex['tokens']) for ex in train_data) == 204_567
        assert len(val_data) == 3_466
        assert sum(len(ex['chunks']) for ex in val_data) == 5_942
        assert sum(len(ex['tokens']) for ex in val_data) == 51_578
        assert len(test_data) == 3_684
        assert sum(len(ex['chunks']) for ex in test_data) == 5_648
        assert sum(len(ex['tokens']) for ex in test_data) == 46_666
        
        assert hasattr(train_data[0]['tokens'][0], 'pos_tag')
        assert train_data[0]['tokens'][0].pos_tag == '-X-'
        
        
    def test_ontonotes5(self):
        reader = ConllReader(text_col_id=3, tag_col_id=10, scheme='OntoNotes', line_sep_starts=["#begin", "#end", "pt/"])
        # train_data = reader.read("assets/data/conll2012/train.english.v4_gold_conll", encoding='utf-8')
        val_data   = reader.read("assets/data/conll2012/dev.english.v4_gold_conll", encoding='utf-8')
        test_data  = reader.read("assets/data/conll2012/test.english.v4_gold_conll", encoding='utf-8')
        
        # assert len(train_data) == 59_924
        # assert sum(len(ex['chunks']) for ex in train_data) == 81_828
        # assert sum(len(ex['tokens']) for ex in train_data) == 1_088_503
        assert len(val_data) == 8_528
        assert sum(len(ex['chunks']) for ex in val_data) == 11_066
        assert sum(len(ex['tokens']) for ex in val_data) == 147_724
        assert len(test_data) == 8_262
        assert sum(len(ex['chunks']) for ex in test_data) == 11_257
        assert sum(len(ex['tokens']) for ex in test_data) == 152_728
        
        
    def test_ontonotes5_chinese(self):
        reader = ConllReader(text_col_id=3, tag_col_id=10, scheme='OntoNotes', line_sep_starts=["#begin", "#end", "pt/"])
        # train_data = reader.read("assets/data/conll2012/train.chinese.v4_gold_conll", encoding='utf-8')
        val_data   = reader.read("assets/data/conll2012/dev.chinese.v4_gold_conll", encoding='utf-8')
        test_data  = reader.read("assets/data/conll2012/test.chinese.v4_gold_conll", encoding='utf-8')
        
        # assert len(train_data) == 36_487
        # assert sum(len(ex['chunks']) for ex in train_data) == 62_543
        # assert sum(len(ex['tokens']) for ex in train_data) == 756_063
        assert len(val_data) == 6_083
        assert sum(len(ex['chunks']) for ex in val_data) == 9_104
        assert sum(len(ex['tokens']) for ex in val_data) == 110_034
        assert len(test_data) == 4_472
        assert sum(len(ex['chunks']) for ex in test_data) == 7_494
        assert sum(len(ex['tokens']) for ex in test_data) == 92_308
        
        
        