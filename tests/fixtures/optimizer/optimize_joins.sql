SELECT * FROM x JOIN y ON y.a = 1 JOIN z ON x.a = z.a AND y.a = z.a;
SELECT * FROM x JOIN z ON x.a = z.a AND TRUE JOIN y ON y.a = 1 AND y.a = z.a;

SELECT * FROM x JOIN y ON y.a = 1 JOIN z ON x.a = z.a;
SELECT * FROM x JOIN y ON y.a = 1 JOIN z ON x.a = z.a;

SELECT * FROM x CROSS JOIN y JOIN z ON x.a = z.a AND y.a = z.a;
SELECT * FROM x JOIN z ON x.a = z.a AND TRUE JOIN y ON y.a = z.a;

SELECT * FROM x LEFT JOIN y ON y.a = 1 JOIN z ON x.a = z.a AND y.a = z.a;
SELECT * FROM x LEFT JOIN y ON y.a = 1 JOIN z ON x.a = z.a AND y.a = z.a;

SELECT * FROM x INNER JOIN z ON x.id = z.id;
SELECT * FROM x JOIN z ON x.id = z.id;

SELECT * FROM x LEFT OUTER JOIN z;
SELECT * FROM x LEFT JOIN z ON TRUE;

SELECT * FROM x CROSS JOIN z;
SELECT * FROM x CROSS JOIN z;

SELECT * FROM x JOIN z;
SELECT * FROM x CROSS JOIN z;

SELECT * FROM x FULL JOIN z;
SELECT * FROM x FULL JOIN z ON TRUE;

SELECT * FROM x NATURAL JOIN z;
SELECT * FROM x NATURAL JOIN z ON TRUE;

SELECT * FROM x RIGHT JOIN z;
SELECT * FROM x RIGHT JOIN z ON TRUE;

SELECT * FROM x JOIN z USING (id);
SELECT * FROM x JOIN z USING (id);

SELECT * FROM x CROSS JOIN z ON TRUE;
SELECT * FROM x CROSS JOIN z;

SELECT * FROM x LEFT ANTI JOIN y ON x.a = y.a; 
SELECT * FROM x LEFT ANTI JOIN y ON x.a = y.a;

SELECT * FROM x CROSS JOIN y ANTI JOIN z ON x.a = z.a AND y.a = x.a;
SELECT * FROM x CROSS JOIN y ANTI JOIN z ON x.a = z.a AND y.a = x.a;

SELECT * FROM x CROSS JOIN y JOIN z ON x.a = z.a OR y.a = x.a;
SELECT * FROM x CROSS JOIN y JOIN z ON x.a = z.a OR y.a = x.a;

SELECT * FROM x CROSS JOIN y SEMI JOIN z ON x.a = z.a OR y.a = x.a;
SELECT * FROM x CROSS JOIN y SEMI JOIN z ON x.a = z.a OR y.a = x.a;

SELECT * FROM x LEFT SEMI JOIN y ON x.a = y.a; 
SELECT * FROM x LEFT SEMI JOIN y ON x.a = y.a;

-- Comma joins bind less tightly than JOIN, so `x, y RIGHT JOIN z` groups as `x, (y RIGHT JOIN z)`.
-- Rewriting the comma as CROSS JOIN would regroup it into `(x CROSS JOIN y) RIGHT JOIN z` and
-- change the rows preserved by the outer join, so such comma joins are kept as-is.
SELECT * FROM x, y RIGHT JOIN z ON y.a = z.a;
SELECT * FROM x, y RIGHT JOIN z ON y.a = z.a;

SELECT * FROM x, y FULL JOIN z ON y.a = z.a;
SELECT * FROM x, y FULL JOIN z ON y.a = z.a;

-- LEFT joins don't need the guard: `(x CROSS JOIN y) LEFT JOIN z` preserves exactly
-- the rows of `x, (y LEFT JOIN z)`, so the comma join can still be rewritten.
SELECT * FROM x, y LEFT JOIN z ON y.a = z.a;
SELECT * FROM x CROSS JOIN y LEFT JOIN z ON y.a = z.a;

SELECT * FROM x, y, z RIGHT JOIN w ON z.a = w.a;
SELECT * FROM x, y, z RIGHT JOIN w ON z.a = w.a;

SELECT * FROM x, y LEFT SEMI JOIN z ON y.a = z.a;
SELECT * FROM x CROSS JOIN y LEFT SEMI JOIN z ON y.a = z.a;

-- Comma joins after the last sided join are top-level cross products and can be rewritten.
SELECT * FROM x RIGHT JOIN y ON x.a = y.a, z;
SELECT * FROM x RIGHT JOIN y ON x.a = y.a CROSS JOIN z;

SELECT * FROM x, y RIGHT JOIN z ON y.a = z.a, w;
SELECT * FROM x, y RIGHT JOIN z ON y.a = z.a CROSS JOIN w;

-- Comma joins followed only by inner joins are safe to rewrite.
SELECT * FROM x, y JOIN z ON y.a = z.a;
SELECT * FROM x CROSS JOIN y JOIN z ON y.a = z.a;
