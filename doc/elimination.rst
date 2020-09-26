.. puzzle-solvers: a library of tools for solving puzzles

.. Copyright (C) 2019  Joseph R. Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>

.. Permission is hereby granted, free of charge, to any person obtaining a copy
.. of this software and associated documentation files (the "Software"), to
.. deal in the Software without restriction, including without limitation the
.. rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
.. sell copies of the Software, and to permit persons to whom the Software is
.. furnished to do so, subject to the following conditions:

.. The above copyright notice and this permission notice shall be included in
.. all copies or substantial portions of the Software.

.. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
.. IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
.. FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
.. AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
.. LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
.. FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
.. IN THE SOFTWARE.

.. Author: Joseph Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
.. Version: 28 May 2019: Initial Coding


.. _elimination:

===================
Elimination Puzzles
===================

.. automodule:: puzzle_solvers.elimination


.. _elimination-toc:

.. contents:: Contents:
   :depth: 2
   :local:


.. _elimination-tutorial:

--------
Tutorial
--------

As an example, we will show how to work through the problem in the
[Stack Overflow question][1] that inspired this package in the first place. The
full code can be found among the :ref:`setup-demos` at
`puzzle_solvers.demos.elimination`.

The original problem statement is in German and can be found [here][2] (along
with the [solution][3]). The following is as literal of a translation into
proper English (US) as I could manage:


.. _elimination-tutorial-puzzle:

The Puzzle
==========

There are five friends (Dana, Ingo, Jessica, Sören, Valerie) waiting in line at
the register of a clothing store. They are all of different ages (26, 27, 30,
33, 35), and want to buy different tops (Blouse, Poloshirt, Pullover,
Sweatshirt, T-Shirt) for themselves. The tops have different colors (blue,
yellow, green, red, black) and sizes (XS, S, M, L, XL).


.. _elimination-tutorial-rules:

Rules
=====

1. The top Dana wants to buy is size XL.

    a. She is ahead of (but not directly ahead) of someone who wants to buy a
       black top.

2. Jessica waits directly in front of a person who wants to buy a Poloshirt.
3. The second person in line wants to buy a yellow top.
4. The T-shirt isn't red.
5. Sören wants to buy a Sweatshirt.

    a. The person who waits directly in front of him is older than the one
       behind him.

6. Ingo needs a size L top.
7. The last person in line is 30 years old.
8. The oldest person is going to buy the top with the smallest size.
9. The person who waits directly behind Valerie wants to buy a red top.

    a. The red top is bigger than size S.

10. The youngest person wants to buy a yellow top.
11. Jessica is going to buy a Blouse.
12. The third person in line wants to buy a size M top.
13. The Poloshirt is either red or yellow or green.


.. _elimination-tutorial-solution:

Solution
========


.. _elimination-tutorial-solution-setup:

Setup
-----

First we import a :py:class:`Solver` from the
:py:mod:`puzzle_solvers.elimination` module::

    from puzzles.elimination import Solver

To use the :py:class:`Solver` class, we first provide the problem space as an
input. In this case, we use a dictionary of lists. The keys of the dictionary
are the names of the categories (``'top'``, ``'age'``, etc.). The values are
the items in each category::

    positions = [1, 2, 3, 4, 5]
    names = ['Dana', 'Ingo', 'Jessica', 'Sören', 'Valerie']
    ages = [26, 27, 30, 33, 35]
    tops = ['Blouse', 'Poloshirt', 'Pullover', 'Sweatshirt', 'T-Shirt']
    colors = ['blue', 'yellow', 'green', 'red', 'black']
    sizes = ['XS', 'S', 'M', 'L', 'XL']

    problem = {
        'position': positions,
        'name': names,
        'age': ages,
        'top': tops,
        'color': colors,
        'size': sizes,
    }

The lists of values must be distinct within themselves, but not necessarily
between each other. `None` is forbidden as either a category or item label.

All the lists are sorted as much as makes sense. This is not required by the
solver, but is convenient for us. It allows us to write something like "the
second oldest person" as ``ages[-2]`` instead of having to call a function or
hard-code ``33``.

Notice also that the numerical data, ``positions`` and ``ages`` is represented
as :py:class:`int` rather than :py:class:`str`. This allows meaningful
comparisons to be made when we get a rule that says something like "younger
than" or "standing behind".

Then we create the solver::

    solver = Solver(problem)

Internally, the solver transforms the data into a graph represented as an
adjacency matrix that keeps track of the labels and categories for you. It also
provides some methods for implementing the rules. If you want to see a detailed
report of all the operations the solver performs, pass ``debug=True`` to the
constructor.

We can get a visual output of the state of the solver if `matplotlib`_ is
installed using the :py:meth:`~Solver.draw` method. A quick check shows that
all the categories and items were added and linked correctly (see
:eq:`elimination-complete`). Notice that there are no links within a category::

    >>> solver.edges
    375
    >>> solver.draw()

.. figure:: /_static/elimination-1.png
   :scale: 50%
   :alt: Nearly complete graph

   The initial problem space.


.. _elimination-tutorial-solution-rules:

Rules
-----

The rules are added to the solver by calling the appropriate methods::

    solver.match('Dana', 'XL')

The :py:meth:`~Solver.match` method sets up a 1-to-1 relationship between the
name ``'Dana'`` and the size ``'XL'``. As long as the names are unambiguous,
just a label is sufficient. This is a process-of-elimination problem, so the
solver removes all the possibilities that ``'Dana'`` may be any other size, and
that anyone else might be size ``'XL'``. It then follows through with any
additional :ref:`implications <elimination-logic-implications>` the changes
might have.

If the same label is repeated in more than one category, the category is
mandatory. Items can be specified unambiguously as two-element (category,
label) tuple. The line above could be rewritten as::

    solver.match(('name', 'Dana'), ('size', 'XL'))

Note that all categories and labels must be an exact match with ``==``. In
particular, strings are case sensitive. The first rule was
:ref:`elimination-logic-explicit`. The next two rules are
:ref:`elimination-logic-implicit`::

    solver.less_than('Dana', 'black', 'position', 2, None)
    solver.less_than('Jessica', 'Poloshirt', 'position', 1)

These showcase the :py:meth:`~Solver.less_than` method, which creates an
:py:class:`Assertion` that will keep getting updated as more information is
discovered about the ``position``\ s of ``'Dana'``, ``'black'``, ``'Jessica'``
and ``'Poloshirt'``. The first call asserts that ``'Dana'`` is *at least* two
positions ahead of ``'black'`` in line. The upper bound is `None`. The second
call asserts that ``'Jessica'`` is *exactly* one position ahead of
``'Poloshirt'``. There is a reflected :py:meth:`~Solver.greater_than` method,
as well as an :py:meth:`~Solver.adjacent_to` method that checks similar
conditions regardless of the direction. ::

    solver.match(2, 'yellow')
    solver.unmatch('T-Shirt', 'red')

:py:meth:`~Solver.unmatch` eliminates a single connection. Like
:py:meth:`~Solver.match`, it is :ref:`elimination-logic-explicit`. It updates
the solution with all of the resulting
:ref:`implications <elimination-logic-implications>`. ::

    solver.match('Sören', 'Sweatshirt')
    solver.match('Ingo', 'L')
    solver.match(positions[-1], 30)
    solver.match(ages[-1], sizes[0])
    solver.match('red', *sizes[sizes.index('S') + 1:])

Here, we used the fact that our ``positions``, ``ages`` and ``sizes`` lists are
sorted. The 1-to-many form of :py:meth:`~Solver.match` behaves much like the
usual form, except that the first argument can match *any* of the remaining
ones. ::

    solver.match(ages[0], 'yellow')
    solver.match('Jessica', 'Blouse')
    solver.match(3, 'M')
    solver.match('Poloshirt', 'red', 'yellow', 'green')

The categories of all the items passed to :py:meth:`~Solver.match` except the
first must be the same. At this point, 116 (out of 300 :eq:`elimination-diff`)
edges have been eliminated::

    >>> solver.edges
    259


.. _elimination-tutorial-special:

Special Cases
-------------

Only rule 5a has not been used up to this point. The assertions set up in steps
1a, 2 and 9 still remain, awaiting the additional infomation::

    >>> solver.assertion_count
    3

Looking at ``solver.assertions`` will tell us which rules are still not fully
satisfied. You will see six mappings rather than 3, because each
:py:class:`Assertion` object is mapped twice. Assertions will remove themselves
from the :py:attr:`~Solver.assertions` dictionary as they are satisfied.

Before we continue, let us pre-process the information about ``'Sören'`` a
little bit based on the remaining rule. These steps are mainly due to a failing
of the solver, which can't currently handle multi-level implicit rules like
that. First, we can glean that ``'Sören'`` can not be first or last, because he
has people before and behind him::

    solver.unmatch('Sören', positions[0])
    solver.unmatch('Sören', positions[-1])

This still does not establish ``'Sören'``\ 's position. We can check using
:py:meth:`~Solver.category_for`::

    >>> solver.category_for('Sören', 'position')
    

This method will return a non-`None` value only if there is a 1-to-1 mapping
between ``'Sören'`` in the category ``'position'``.

Next, we can ensure that ``'Sören'`` is not behind the youngest person, since
the person ahead of him must be older than the one behind::

    youngest = solver.category_for(ages[0], 'position')
    if youngest is not None:
        solver.unmatch('Sören', youngest + 1)

Here, we use :py:meth:`~Solver.category_for` to find the position of he
youngest person, and unlink the preceding one from ``'Sören'`` if it has been
established. Similarly, ``'Sören'`` can not be directly in front of the oldest
person::

    oldest = solver.category_for(ages[-1], 'position')
    if oldest is not None:
        solver.unmatch('Sören', oldest - 1)

This leaves us with only 10 more edges to go::

    >>> solver.edges
    85

The important thing is that ``'Sören'``\ 's position has been fixed, along with
everyone else's::

    >>> solver.category_for('Sören', 'position')
    2
    >>> solver.assertion_count
    0

We can also check there are two remaining age options and two remaining
positions, both around ``'Sören'``::

    >>> solver.find_missing('position')
    {1, 3}
    >>> solver.find_missing('age')
    {27, 33}

This is just a check. :py:meth:`~Solver.find_missing` returns all the items in
category ``'position'`` that do not have all their 1-to-1 mappings. Here is how
we code the final step::

    pos = solver.category_for('Sören', 'position')
    ages = solver.find_missing('age')
    solver.match(pos - 1, max(ages))
    solver.match(pos + 1, min(ages))

.. _elimination-tutorial-solution-check:

Solution Verification
---------------------

There are no more edges to remove (see :eq:`elimination-final`)::

    >>> solver.edges
    75
    >>> solver.solved
    True
    >>> solver.draw()

.. figure:: /_static/elimination-2.png
   :scale: 50%
   :alt: Fully disconnected graph

   The components of the final answer.


.. _elimination-logic:

-----
Logic
-----


.. _elimination-logic-structure:

Structure
=========

The data is presented as :math:`N` items in each of :math:`M` categories. We
can treat it as a graph with :math:`N * M` nodes. Initially, all nodes are
connected except those within a given category, for a total of

.. math::
   :label: elimination-complete

   \frac{M * N * (M * N - 1)}{2} - \frac{M * N * (N - 1)}{2} = \frac{M * N^2 * (M - 1)}{2}

The first term on the left is the number of edges in the complete graph. The
second term on the left is the number of edges between nodes within each of the
:math:`M` categories.

The goal of the problem is to remove edges based on provided information until
the graph ends up with :math:`N` connected components, each of which is a
complete subgraph linking exactly one item from each category. The total number
of edges in the final solution is

.. math::
   :label: elimination-final

   \frac{N * M * (M - 1)}{2}

The number of edges that the information must account for is therefore

.. math::
   :label: elimination-diff

   \frac{M * N^2 * (M - 1)}{2} - \frac{N * M * (M - 1)}{2} = \frac{M * N * (M - 1) * (N - 1)}{2}


.. _elimination-logic-operations:

Operations
==========

This solver is a process of elimination one. Naturally, the fundamental
operation it currently recognizes is severing an edge. Operations are preformed
in response to rules.


.. _elimination-logic-rules:

Rules
=====

There are two types of supported rules: explicit and implicit.


.. _elimination-logic-explicit:

Explicit
--------

Explicit rules are ones that can be completely satisfied at once, and whose
consequences become an integral part of the state as soon as the relevant
operations are carried out. An example of a direct rule is "Red is 5". All the
necessary links can be severed immediately. Any further operations can fully
take this rule into account based solely on the state it leaves behind.

Another way to look at it is that explicit rules set a direct node-to-node
relationship. Because of that, explicit rules make immediate changes to the
state. Any further rules must use that state to follow through with their
:ref:`elimination-logic-implications`.


.. _elimination-logic-implicit:

Implicit
--------

Implicit rules are ones that can not be satisfied without additional
information in the general case. That is not to say that the solver may not be
in a state that allows such a rule to be satisfied immediately when it is
encountered. An example of an implicit rule is "The position of Red is less
than the position of 5". Until the links between Red and 5 and the position
category are fully specified through other rules, this rule can provide some
information, but can not be completely represented in the state.

Implicit rules set up a relationship between nodes through a category. While
this allows for *some* direct changes, like unlinking the two nodes in
question, implicit rules must be revisited once more information becomes
available. Implicit rules are stored in :py:class:`Assertion` objects and
re-evaluated whenever any potential endpoints change.


.. _elimination-logic-implications:

Implications
============

The most important aspect of this solver is its ability to follow through with
the implications of an edge removal. To illustrate exactly what this means,
let's say we have categories :math:`A` and :math:`B` with an item :math:`X` in
:math:`A` and :math:`Y` in :math:`B`. When edge :math:`XY` is severed, it
affects the relationship between :math:`X` and :math:`B`. The nodes in
:math:`B` that :math:`X` is still connected to determine the entire set of
connections that are allowed for :math:`X` elsewhere. Any connections that
:math:`X` has to nodes not also connected to the nodes it is connected to in
:math:`B` must be severed. The process is recursive. It applies to :math:`Y`
and :math:`A` by symmetry.

Single-edge removal is implemented in the :py:meth:`Solver.unmatch` method.

A 1-to-many match between two categories is equivalent to removing multiple
edges. Mapping node :math:`X` in category :math:`A` to a number of
possibilities in category :math:`B` is equivalent to severing all the edges to
nodes in :math:`B` that :math:`X` does not map to. A slight optimization is
possible by processing the severance from :math:`X` as a single unit.

An even more specialized application is creating a 1-to-1 match this is the
symmetrical extension of a 1-to-many match. All the nodes connected to one
matched node must share an edge with the other as well. Any edges not meeting
this criterion must be severed.

Matching to a single element of one category, both 1-to-1 and 1-to-many, is
implemented in the :py:meth:`Solver.match` method.

The final aspect of implications is that all affected categories must be
checked against the implicit rules encountered up to that point. In the
examples above, all the indirect rules linked through *either* :math:`A` *or*
:math:`B` would have to be re-verified. Any edge removal affects the indirect
rules at both ends, since the contents of the categories changes.


.. _elimination-api:

---
API
---

.. autoclass:: Solver
   :members:
   :special-members: __init__

.. autoclass:: Assertion
   :members:
   :special-members: __init__, __repr__, __str__

.. autoclass:: OffsetAssertion
   :members:
   :special-members: __init__, __repr__, __str__

.. autoclass:: AdjacencyOffsetAssertion
   :members:
   :special-members: __init__, __repr__, __str__

.. autoclass:: BoundedAssertion
   :members:
   :special-members: __init__, __repr__, __str__

.. autoclass:: BoundedExclusiveAssertion
   :members:
   :special-members: __init__, __repr__, __str__

.. autoclass:: BandedAssertion
   :members:
   :special-members: __init__, __repr__, __str__

.. autoclass:: SymmetricAssertionMixin
   :members:

.. autoclass:: AsymmetricAssertionMixin
   :members:


.. [1]: https://stackoverflow.com/q/56284249/2988730
.. [2]: https://i.imgur.com/1Bsi3Fu.jpg
.. [3]: https://i.imgur.com/vIKnhj0.jpg


.. include:: /link-defs.rst
