from pdoc.doc_ast import _dedent


def test_dedent():
    # not indented
    assert _dedent("def foo(): pass") == "def foo(): pass"

    # indented
    assert _dedent("""\
    def foo():
        pass""") == "def foo():\n        pass"

    # with decorator
    assert _dedent("""\
    @foo
    def foo():
        pass""") == "@foo\ndef foo():\n        pass"

    # with decorator and comment
    assert _dedent("""\
    @foo
    # hello world
    def foo():
        pass""") == "@foo\n# hello world\ndef foo():\n        pass"
