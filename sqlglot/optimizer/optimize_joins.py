from __future__ import annotations
from collections.abc import Iterable

from sqlglot import exp
from sqlglot.errors import OptimizeError
from sqlglot._typing import E
from sqlglot.helper import tsort

JOIN_ATTRS = ("on", "side", "kind", "using", "method")


def optimize_joins(expression: E) -> E:
    """
    Removes cross joins if possible and reorder joins based on predicate dependencies.

    Example:
        >>> from sqlglot import parse_one
        >>> optimize_joins(parse_one("SELECT * FROM x CROSS JOIN y JOIN z ON x.a = z.a AND y.a = z.a")).sql()
        'SELECT * FROM x JOIN z ON x.a = z.a AND TRUE JOIN y ON y.a = z.a'
    """

    for select in expression.find_all(exp.Select):
        joins: list[exp.Join] = select.args.get("joins", [])

        if not _is_reorderable(joins):
            continue

        references: dict[str, list[exp.Join]] = {}
        cross_joins: list[tuple[str, exp.Join]] = []

        for join in joins:
            tables = other_table_names(join)

            if tables:
                for table in tables:
                    references[table] = references.get(table, []) + [join]
            else:
                cross_joins.append((join.alias_or_name, join))

        for name, join in cross_joins:
            for dep in references.get(name, []):
                # An ANTI join's ON clause is negated, i.e. NOT EXISTS(a AND b) is not
                # equivalent to b AND NOT EXISTS(a), so its conjuncts can't be extracted
                if dep.kind == "ANTI":
                    continue

                on = dep.args["on"]

                # Only conjuncts can be extracted, i.e. `a OR b` is not `b AND (a OR TRUE)`
                if isinstance(on, exp.And):
                    if len(other_table_names(dep)) < 2:
                        continue

                    for predicate in on.flatten():
                        if name in exp.column_table_names(predicate):
                            predicate.replace(exp.true())
                            predicate = exp._combine(
                                [join.args.get("on"), predicate], exp.And, copy=False
                            )
                            join.on(predicate, append=False, copy=False)

    expression = reorder_joins(expression)
    expression = normalize(expression)
    return expression


def reorder_joins(expression: E) -> E:
    """
    Reorder joins by topological sort order based on predicate references.
    """
    for from_ in expression.find_all(exp.From):
        parent = from_.parent
        if parent is None:
            raise OptimizeError("FROM clause without parent expression")
        joins: list[exp.Join] = parent.args.get("joins", [])

        if not _is_reorderable(joins):
            continue

        joins_by_name = {join.alias_or_name: join for join in joins}
        dag = {name: other_table_names(join) for name, join in joins_by_name.items()}
        parent.set(
            "joins",
            [
                joins_by_name[name]
                for name in tsort(dag)
                if name != from_.alias_or_name and name in joins_by_name
            ],
        )
    return expression


def normalize(expression: E) -> E:
    """
    Remove INNER and OUTER from joins as they are optional.
    """
    # Comma joins bind less tightly than joins that use the JOIN keyword, i.e. standard SQL
    # groups `x, y RIGHT JOIN z` as `x, (y RIGHT JOIN z)`. Rewriting the comma join as a
    # CROSS JOIN would regroup the FROM clause into `(x CROSS JOIN y) RIGHT JOIN z`, which
    # changes the rows preserved by the RIGHT/FULL join, so comma joins that precede a
    # RIGHT/FULL join in the same FROM clause are left as-is. LEFT joins don't need this
    # guard: `(x CROSS JOIN y) LEFT JOIN z` preserves exactly the rows of `x, (y LEFT JOIN z)`.
    comma_grouped: set[int] = set()
    for select in expression.find_all(exp.Select):
        joins: list[exp.Join] = select.args.get("joins") or []
        last_sided = max(
            (i for i, join in enumerate(joins) if join.side in ("RIGHT", "FULL")), default=0
        )
        comma_grouped.update(
            id(join) for join in joins[:last_sided] if not any(join.args.get(k) for k in JOIN_ATTRS)
        )

    for join in expression.find_all(exp.Join):
        if join.kind == "PASTE" or join.args.get("nearest"):
            continue

        if not any(join.args.get(k) for k in JOIN_ATTRS):
            if id(join) in comma_grouped:
                continue

            join.set("kind", "CROSS")

        if join.kind == "CROSS":
            join.set("on", None)
        else:
            if join.kind in ("INNER", "OUTER"):
                join.set("kind", None)

            if not join.args.get("on") and not join.args.get("using"):
                join.set("on", exp.true())
    return expression


def other_table_names(join: exp.Join) -> set[str]:
    on = join.args.get("on")
    return exp.column_table_names(on, join.alias_or_name) if on else set()


def _is_reorderable(joins: Iterable[exp.Join]) -> bool:
    """
    Checks if joins can be reordered without changing query semantics.

    Joins with a side (LEFT, RIGHT, FULL) cannot be reordered easily,
    the order affects which rows are included in the result.
    PASTE joins pair rows by position, so reordering changes their pairings.
    NEAREST joins select top-k matches, which depend on the input rows.

    Example:
        >>> from sqlglot import parse_one, exp
        >>> from sqlglot.optimizer.optimize_joins import _is_reorderable
        >>> ast = parse_one("SELECT * FROM x JOIN y ON x.id = y.id JOIN z ON y.id = z.id")
        >>> _is_reorderable(ast.find(exp.Select).args.get("joins", []))
        True
        >>> ast = parse_one("SELECT * FROM x LEFT JOIN y ON x.id = y.id JOIN z ON y.id = z.id")
        >>> _is_reorderable(ast.find(exp.Select).args.get("joins", []))
        False
    """
    return not any(join.side or join.kind == "PASTE" or join.args.get("nearest") for join in joins)
