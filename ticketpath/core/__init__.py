"""Pure computation: no network, no chain, no ambient clock.

Everything importable from here takes its inputs as arguments, including `now`
where time matters, so it can be unit-tested without a server or a fixture file.
"""
