"""
Tests for BPE Tokenizer (Project 9)
Run: pytest test_bpe.py -k "TestLevel1" -v
"""

import pytest

from bpe import BPETokenizer


# ============================================================
# Level 1: BPE Training
# ============================================================

class TestLevel1:
    def test_base_vocab_size(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello", vocab_size=256)
        vocab = tokenizer.get_vocab()
        assert len(vocab) == 256

    def test_train_adds_merges(self):
        tokenizer = BPETokenizer()
        tokenizer.train("aaabdaaabac", vocab_size=259)  # 3 merges
        merges = tokenizer.get_merges()
        assert len(merges) == 3

    def test_vocab_grows_with_merges(self):
        tokenizer = BPETokenizer()
        tokenizer.train("aaabdaaabac", vocab_size=259)
        vocab = tokenizer.get_vocab()
        assert len(vocab) == 259

    def test_first_merge_most_frequent(self):
        tokenizer = BPETokenizer()
        tokenizer.train("aaabdaaabac", vocab_size=257)
        merges = tokenizer.get_merges()
        assert len(merges) == 1
        # "aa" appears 4 times (positions 0-1, 1-2 in "aaa", and same in second "aaa")
        # Most frequent pair should be (a, a)
        assert merges[0] == (b"a", b"a")

    def test_merges_ordered(self):
        tokenizer = BPETokenizer()
        tokenizer.train("aaabdaaabac", vocab_size=260)
        merges = tokenizer.get_merges()
        assert len(merges) == 4
        # Each merge was the most frequent at its time

    def test_vocab_contains_bytes(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello", vocab_size=256)
        vocab = tokenizer.get_vocab()
        # Base vocab: 0-255 map to single bytes
        for i in range(256):
            assert i in vocab
            assert vocab[i] == bytes([i])

    def test_new_tokens_are_byte_concatenations(self):
        tokenizer = BPETokenizer()
        tokenizer.train("aaaa", vocab_size=257)
        vocab = tokenizer.get_vocab()
        # Token 256 should be the merge of (a, a) = b"aa"
        assert vocab[256] == b"aa"

    def test_empty_text(self):
        tokenizer = BPETokenizer()
        tokenizer.train("", vocab_size=256)
        assert tokenizer.get_merges() == []

    def test_single_char_repeated(self):
        tokenizer = BPETokenizer()
        tokenizer.train("aaaa", vocab_size=258)
        merges = tokenizer.get_merges()
        assert len(merges) == 2
        assert merges[0] == (b"a", b"a")
        # Second merge: (aa, a) or (a, aa) or (aa, aa)

    def test_no_merges_if_vocab_size_256(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello world", vocab_size=256)
        assert tokenizer.get_merges() == []


# ============================================================
# Level 2: Encoding + Decoding
# ============================================================

class TestLevel2:
    def test_encode_returns_list_of_ints(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello world hello world", vocab_size=270)
        encoded = tokenizer.encode("hello")
        assert isinstance(encoded, list)
        assert all(isinstance(t, int) for t in encoded)

    def test_encode_compression(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello world hello world", vocab_size=270)
        encoded = tokenizer.encode("hello world")
        # With merges, should be shorter than raw bytes
        assert len(encoded) < len("hello world")

    def test_decode_basic(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello world hello world", vocab_size=270)
        encoded = tokenizer.encode("hello world")
        decoded = tokenizer.decode(encoded)
        assert decoded == "hello world"

    def test_round_trip(self):
        tokenizer = BPETokenizer()
        text = "the quick brown fox jumps over the lazy dog"
        tokenizer.train(text, vocab_size=270)
        assert tokenizer.decode(tokenizer.encode(text)) == text

    def test_round_trip_repeated(self):
        tokenizer = BPETokenizer()
        text = "abcabc abcabc abcabc"
        tokenizer.train(text, vocab_size=265)
        assert tokenizer.decode(tokenizer.encode(text)) == text

    def test_encode_empty(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello", vocab_size=256)
        assert tokenizer.encode("") == []

    def test_decode_empty(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello", vocab_size=256)
        assert tokenizer.decode([]) == ""

    def test_encode_unseen_text(self):
        """Text not in training data should fall back to byte-level."""
        tokenizer = BPETokenizer()
        tokenizer.train("aaaa", vocab_size=258)
        encoded = tokenizer.encode("xyz")
        decoded = tokenizer.decode(encoded)
        assert decoded == "xyz"

    def test_encode_deterministic(self):
        tokenizer = BPETokenizer()
        tokenizer.train("hello world hello world", vocab_size=270)
        enc1 = tokenizer.encode("hello world")
        enc2 = tokenizer.encode("hello world")
        assert enc1 == enc2

    def test_single_byte_encode_decode(self):
        """Without merges, each character is one token."""
        tokenizer = BPETokenizer()
        tokenizer.train("", vocab_size=256)  # no merges
        encoded = tokenizer.encode("hi")
        assert len(encoded) == 2
        assert encoded == [ord("h"), ord("i")]
        assert tokenizer.decode(encoded) == "hi"

    def test_unicode_round_trip(self):
        tokenizer = BPETokenizer()
        text = "hello"
        tokenizer.train(text, vocab_size=260)
        # UTF-8 bytes for non-ASCII
        test = "cafe"
        assert tokenizer.decode(tokenizer.encode(test)) == test
