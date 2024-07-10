def __dir__():
    # invalid: returns non-str members.
    return [RuntimeError]