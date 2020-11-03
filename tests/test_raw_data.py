# -*- coding: utf-8 -*-
from eznlp.sequence_tagging.raw_data import parse_conll_file


class TestParseConllFile(object):
    def test_conll2003(self):
        conll_config = {'raw_scheme': 'BIO1', 
                        'scheme': 'BIOES', 
                        'columns': ['text', 'pos_tag', 'chunking_tag', 'ner_tag'], 
                        'trg_col': 'ner_tag', 
                        'attach_additional_tags': True, 
                        'skip_docstart': False, 
                        'lower_case_mode': 'None'}
        
        train_data = parse_conll_file("assets/data/conll2003/eng.train", **conll_config)
        val_data   = parse_conll_file("assets/data/conll2003/eng.testa", **conll_config)
        test_data  = parse_conll_file("assets/data/conll2003/eng.testb", **conll_config)
        
        assert len(train_data) == 14_987
        assert sum(len(ex['tokens']) for ex in train_data) == 204_567
        assert len(val_data) == 3_466
        assert sum(len(ex['tokens']) for ex in val_data) == 51_578
        assert len(test_data) == 3_684
        assert sum(len(ex['tokens']) for ex in test_data) == 46_666
        
        