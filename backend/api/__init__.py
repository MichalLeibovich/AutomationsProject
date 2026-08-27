"""HTTP layer: blueprints, middleware and serializers.

The only package that imports Flask. It parses requests, delegates to a service,
and serialises the result. No business rule lives here.
"""
