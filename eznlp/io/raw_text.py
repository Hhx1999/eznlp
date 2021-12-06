# -*- coding: utf-8 -*-
from typing import List
import logging
import tqdm
import json

from .base import IO
from ..utils.transition import ChunksTagsTranslator, _token2wwm_tag
from ..utils.segmentation import segment_text_uniformly

logger = logging.getLogger(__name__)


class RawTextIO(IO):
    """An IO interface of raw text files. 
    Note: The wwm strategy currently supports Chinese only. 
    
    document_sep_starts: List[str]
        * For Conll2003, `document_sep_starts` should be `["-DOCSTART-"]`
        * For Wikipedia, `document_sep_starts` should be `["<doc", "</doc"]`
    """
    def __init__(self, 
                 tokenize_callback=None, 
                 zh_tokenize_callback=None, 
                 max_len: int=None, 
                 document_sep_starts=None, 
                 encoding=None, 
                 verbose: bool=True):
        super().__init__(is_tokenized=False, tokenize_callback=tokenize_callback, encoding=encoding, verbose=verbose)
        
        if tokenize_callback is not None:
            assert zh_tokenize_callback is not None
            assert max_len is not None
        
        self.zh_tokenize_callback = zh_tokenize_callback
        self.translator = ChunksTagsTranslator(scheme='zh-wwm', breaking_for_types=False)
        self.en_wwm_span_max_len = 4
        self.min_len = 10
        self.max_len = max_len
        self.document_sep_starts = [] if document_sep_starts is None else document_sep_starts
        
        
    def _detect_wwm_spans(self, tokenized_text: List[str]):
        wwm_tags = [_token2wwm_tag(tok) for tok in tokenized_text]
        chunks = self.translator.tags2chunks(wwm_tags)
        wwm_spans = []
        for ck_type, start, end in chunks:
            if ck_type == 'ZH':
                assert all(len(c) == 1 for c in tokenized_text[start:end])
                wwm_spans.extend([(start+tok_start, start+tok_end)
                                  for _, tok_start, tok_end 
                                  in self.zh_tokenize_callback("".join(tokenized_text[start:end]))])
            elif ck_type in ('EN', 'ETC'):
                if end - start <= self.en_wwm_span_max_len:
                    wwm_spans.append((start, end))
                else:
                    wwm_spans.extend([(start+sub_start, start+sub_end)
                                      for sub_start, sub_end 
                                      in segment_text_uniformly(tokenized_text[start:end], max_span_size=self.en_wwm_span_max_len)])
            else:
                wwm_spans.append((start, end))
        
        assert wwm_spans[0][0] == 0
        assert wwm_spans[-1][1] == len(tokenized_text)
        assert all(pre_end == next_start for (_, pre_end), (next_start, _) in zip(wwm_spans[:-1], wwm_spans[1:]))
        return wwm_spans
        
        
    def _parse_raw(self, byte_lines: List[bytes]):
        data = []
        
        tokenized_doc = []
        for byte_line in tqdm.tqdm(byte_lines, disable=not self.verbose, ncols=100, desc="Loading raw text data"):
            line = byte_line.decode(self.encoding)
            
            if self._is_breaking(line):
                if len(tokenized_doc) >= self.min_len:
                    for start, end in segment_text_uniformly(tokenized_doc, max_span_size=self.max_len):
                        tokenized_text = tokenized_doc[start:end]
                        data.append({'rejoined_text': " ".join(tokenized_text), 
                                     'wwm_spans': self._detect_wwm_spans(tokenized_text)})
                tokenized_doc = []
                
            elif self.tokenize_callback is None:
                tokenized_doc.extend(line.split(" "))
            else:
                tokenized_doc.extend(self.tokenize_callback(line))
        
        if len(tokenized_doc) >= self.min_len:
            for start, end in segment_text_uniformly(tokenized_doc, max_span_size=self.max_len):
                tokenized_text = tokenized_doc[start:end]
                data.append({'rejoined_text': " ".join(tokenized_text), 
                             'wwm_spans': self._detect_wwm_spans(tokenized_text)})
        
        return data
        
        
    def _parse_json(self, byte_lines: List[bytes]):
        data = []
        for byte_line in tqdm.tqdm(byte_lines, disable=not self.verbose, ncols=100, desc="Loading raw text data"):
            # `tokenize_callback` must be None
            entry = json.loads(byte_line.decode(self.encoding))
            # json does not natively support serialization for tuple
            entry['wwm_spans'] = [tuple(span) for span in entry['wwm_spans']]
            data.append(entry)
        return data
        
        
    def read(self, file_path):
        with open(file_path, 'rb') as f:
            byte_lines = [line for line in f if len(line.rstrip()) > 0]
        
        if self.tokenize_callback is None:
            return self._parse_json(byte_lines)
        else:
            return self._parse_raw(byte_lines)
        
        
    def _is_document_seperator(self, line: str):
        for start in self.document_sep_starts:
            if line.startswith(start):
                return True
        return False
        
    def _is_breaking(self, line: str):
        return self._is_document_seperator(line)
        
        
    def write(self, data, file_path):
        with open(file_path, 'w', encoding=self.encoding) as f:
            for line in data:
                f.write(json.dumps(line, ensure_ascii=False))
                f.write("\n")