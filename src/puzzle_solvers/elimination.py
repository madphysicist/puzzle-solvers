# -*- coding: utf-8 -*-

# puzzle-solvers: a library of tools for solving puzzles
#
# Copyright (C) 2019  Joseph R. Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Author: Joseph Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
# Version: 28 May 2019: Initial Coding

"""
Process-of-elimination puzzles, sometimes known as zebra puzzles, or
just logic puzzles, are implemented in the
:py:mod:`puzzle_solvers.elimination` module. These puzzles generally
take the form of a number of different categories of items that must be
matched uniquely against each other based on rules that direct the
elimination of possibilities. An example of such a puzzle is found in
the corresponding :ref:`elimination-tutorial` section.

The original "zebra puzzle" is a particular instance of this type of
puzzle that originated in the December 17, 1962 issue of
*Life Interational*. This particular formulation is ascribed to Albert
Enistein, and sometimes to Lewis Carroll. A solution to this puzzle can
be found among the :ref:`setup-demos` at
`puzzle_solvers.demos.elimination_zebra`.
"""

from collections import deque
from collections.abc import Mapping
from itertools import chain, combinations, cycle
from math import copysign
import re
from types import MappingProxyType

try:
    from matplotlib import pyplot as plt
    from matplotlib.lines import Line2D
except ImportError:
    plt = None
import numpy as np


class Solver:
    """
    The solver class represents an elimination problem as an adjacency
    matrix of size :math:`M * N`, where :math:`M` is the number of
    categories and :math:`N` is the number of elements. The matrix is
    symmetrical, with size-:math:`N` identity matrices all along the
    diagonal.

    The class provides two types of operations: high level and low
    level. High level operations accept item labels or (category, item)
    tuples as inputs. They make it easy to implement the elimination
    rules of the puzzle. Low level methods accept matrix coordinates in
    the range :math:`[0, M * N)`. :py:meth:`match` and
    :py:meth:`unmatch` are examples of high-level methods. Low-level
    methods support the logic of high level methods. :py:meth:`unlink`
    and :py:meth:`find_matches` are low level methods.

    Positions used by the low level methods can be converted to an
    index within :py:attr:`categories` and an index within that category
    using :py:func:`divmod`: the quotient with :py:attr:`n` is the
    category index, while the remainder is the index within the
    category.
    """
    def __init__(self, problem, categories=None, debug=False):
        """
        Create a solver for a particular incarnation of the zebta
        puzzle.

        The problem can be specified as either a mapping of category
        labels to iterables of items or an iterable of iterables. In the
        latter case, the category labels can be the first element of
        each iterable, or supplied independently. In either case, all
        labels may be of any hashable type. All item iterables must
        contain the same number of elements. The labels for each item
        must be unique within a category, but may be repeated between
        categories. So a ``'Height'`` of ``72`` and an ``'Age'`` of
        ``72`` are possible in the same problem, but two items can't
        both have a ``'Height'`` of ``72``. Category labels must be
        unique as well, but a category and any item can have the same
        label.

        Completely unique item labels can be supplied to the high level
        methods as just the item label (unless the label itself is a
        tuple). Item labels that are repeated between categories must
        always be supplied as a two-element (category, item) tuple.

        No item or category labels may be `None`.

        Parameters
        -----------
        problem :
            The problem is specified as either a mapping of iterables,
            or an iterable of iterables.
        categories :
            If `problem` is a mapping, this parameter is ignored.
            Otherwise, if supplied, the iterables in `problem` are
            interpreted as having :math:`N` elements, while this
            iterable supplies the :math:`M` category labels. If missing,
            and first element of each iterable in `problem` is the
            category label. Must be the same length as `problem` if
            used.
        debug : bool
            A flag indicating whether or not detailed messages should be
            printed by all the methods.
        """
        # Having an integer is important because it controls indentation
        self._debug = bool(debug)

        # Check the input data, make a category list and a list of iterables
        # Set categories, normalize problem data
        if isinstance(problem, Mapping):
            self.__dict__['categories'] = tuple(problem.keys())
            data = [problem[key] for key in self.categories]
        else:
            if categories is not None:
                data = list(problem)
                self.__dict__['categories'] = tuple(categories)
                if len(self.categories) != len(data):
                    raise ValueError(
                        f'Category count in problem ({len(data)}) and '
                        f'labels ({len(categories)}) does not match'
                    )
            else:
                data = []
                categories = []
                for items in problem:
                    it = iter(items)
                    categories.append(next(it))
                    data.append(it)
                self.__dict__['categories'] = tuple(categories)
            if len(set(self.categories)) != len(self.categories):
                raise ValueError('Categories must be unique')

        if None in self.categories:
            raise ValueError('None may not be a category label')

        # Compute basic properties (m, n, labels)
        self.__dict__['m'] = len(self.categories)
        self.__dict__['n'] = None
        labels = []
        prev = 0
        for category, items in zip(self.categories, data):
            labels.extend(items)
            size = len(labels) - prev
            if len(set(labels[-size:])) != size:
                raise ValueError(f'Duplicate items found in {category!r}')
            if self.n is None:
                self.__dict__['n'] = size
            elif size != self.n:
                raise ValueError(
                    'All categories must have the same number of items '
                    f'({self.n} != {size})'
                )
            prev += size

        self.__dict__['labels'] = tuple(labels)

        if None in self.labels:
            raise ValueError('None may not be an item label')

        # Compute mapping of unique labels
        mapping = {}
        for index, label in enumerate(labels):
            if label in mapping:
                mapping[label] = None
            else:
                mapping[label] = index

        self.__dict__['map'] = MappingProxyType(mapping)

        # Create adjacency matrix
        self.__dict__['matrix'] = np.empty((len(labels),) * 2, dtype=np.bool)
        if debug:
            print(f'New solver with {self.m} categories, {self.n} items')
            print(f'Matrix is {"x".join(str(s) for s in self.matrix.shape)}')
            print('Items: (ambiguous entries marked with an asterisk)')
            for i, label in enumerate(self.labels):
                if i % self.n == 0:
                    print(f'    Category = {self.categories[i // self.n]!r}')
                print(f'      {"*" if self.map[label] is None else " "} '
                      f'{label!r}')
            print()

        # Create assertions
        self.__dict__['assertions'] = {}

        self.reset()

    @property
    def m(self):
        """
        The number of categories in this problem (read-only).
        """
        return self.__dict__['m']

    @property
    def n(self):
        """
        The number of items in this problem (read-only).
        """
        return self.__dict__['n']

    @property
    def matrix(self):
        """
        The current state of the solver represented as a square numpy
        array with :py:attr:`m` * :py:attr:`n` elements to a side. The
        array is a boolean, symmetric adjacency matrix with `True` all
        along the main diagonal.

        .. warning::

           :py:attr:`matrix` is maintained as perfectly symmetrical,
           with blocks of :py:attr:`n`-by-:py:attr:`n` identity matrices
           along the main diagonal. Accessing :py:attr:`matrix` outside
           the provided methods is allowed, but must be done with
           extreme care to retain these properties. Failure to do so is
           likely to result in an infinite loop.
        """
        return self.__dict__['matrix']

    @property
    def assertions(self):
        """
        A mapping of (position, category IDs) pairs to
        :py:class:`Assertion`\ s.

        This mapping is mutable. It is checked whenever an edge is
        removed. Assertions should be added via methods like
        :py:meth:`greater_than` and :py:meth:`adjacent_to`. Removal
        should be automatic when they are
        :py:attr:`~Assertion.satisfied`, via the
        :py:meth:`remove_assertion` method.

        Each assertion object appears under two keys in the mapping: one
        for each of the items that it links together. Assertions are
        stored in a list under each key.
        """
        return self.__dict__['assertions']

    @property
    def assertion_count(self):
        """
        The number of active :py:attr:`assertions`.
        """
        return sum(map(len, self.assertions.values())) // 2

    @property
    def categories(self):
        """
        The labels of the categories in this problem.

        This is a tuple of length :py:attr:`m`, containing unique
        elements.
        """
        return self.__dict__['categories']

    @property
    def labels(self):
        """
        The data labels corresponding to each row/column of
        :py:attr:`matrix`.

        This is a tuple of :py:attr:`m` * :py:attr:`n` elements, not all
        of which are guaranteed to be unique. Theelements in each
        successive subsequence of :py:attr:`n` *are* unique though.
        """
        return self.__dict__['labels']

    @property
    def map(self):
        """
        A mapping of the unambiguous item labels to their index in
        :py:attr:`matrix`.

        Ambiguous labels are mapped to `None`. This mapping is
        read-only.
        """
        return self.__dict__['map']

    @property
    def edges(self):
        """
        The total number of edges remaining in the solution.
        """
        return (self.matrix.sum() - self.matrix.shape[0]) // 2

    @property
    def solved(self):
        """
        Indicates whether the number of remaining edges matches what it
        would have to be for a complete solution.
        """
        return (self.matrix.sum(axis=1) == self.m).all()

    def reset(self):
        """
        Resets the solver to its initial state.

        This method regenerates the adjacency matrix and removes all
        assertions.
        """
        self.matrix.fill(True)
        for cat in range(len(self.categories)):
            s = self.cat_slice(cat)
            self.matrix[s, s] = False
        np.fill_diagonal(self.matrix, True)
        self.assertions.clear()
        self._log(f'Reset matrix with {self.edges} edges\n')

    def draw(self, show=True, title=None):
        """
        Draw the adjecency matrix as a diagram using matplotlib.

        Each category is displayed in its own row. Items within the
        category appear in the order they were passed in to the
        constructor in.

        Edges representing 1-to-1 mapping between categories are
        highlighted. A solved problem will contain only highlighted
        edges.

        This method is disabled (raises a :py:exc:`NotImplementedError`
        if matplotlib is not found),

        Parameters
        ----------
        show : bool
            Whether or not to show the figure after drawing it. Default
            is `True`.
        title :
            An optional title to assign to the figure.

        Return
        ------
        fig : 
            The figure that the diagram was drawn on.
        ax : 
            The axes that the diagram was drawn on.
        """
        # Check that method is available
        if plt is None:
            raise NotImplementedError('Matplotlib not found')

        # Create plotting surface
        fig, ax = plt.subplots()
        ax.set_axis_off()
        ax.invert_yaxis()

        # Draw the items in rows
        ax.scatter(*np.meshgrid(np.arange(self.n), np.arange(self.m)),
                   marker='o', color='r', zorder=10)

        # Draw labels for items and attributes
        for pos, label in enumerate(self.labels):
            y, x = divmod(pos, self.n)
            # Attribute label for entire row
            if x == 0:
                cat = self.categories[y].upper()
                ax.annotate(
                    cat, (0, y), (-40, 0), textcoords='offset pixels',
                    zorder=10, va='center', ha='right', weight='bold'
                )
            # Item label for each point
            ax.annotate(
                str(label), (x, y), (0, 4), textcoords='offset pixels',
                zorder=5, backgroundcolor=(1, 1, 1, 0.75),
                va='bottom', ha='center', weight='black'
            )

        # Draw the connections
        for start, end in combinations(range(len(self.labels)), 2):
            if self.matrix[start, end]:
                sy, sx = divmod(start, self.n)
                ey, ex = divmod(end, self.n)
                ax.add_line(Line2D([sx, ex], [sy, ey], zorder=0))

        # Draw the known components
        visited = set()
        colors = cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])
        color = next(colors)
        for start in range(len(self.labels)):
            if start in visited:
                continue
            stack = deque([start])
            while stack:
                start = stack.popleft()
                visited.add(start)
                matches = self.find_matches(start)
                sy, sx = divmod(start, self.n)
                for end in matches:
                    if end in visited:
                        continue
                    ey, ex = divmod(end, self.n)
                    ax.add_line(
                        Line2D([sx, ex], [sy, ey], color=color + '80',
                               linewidth=20, zorder=-10)
                    )
                    stack.append(end)
            color = next(colors)

        # Final tweak and show
        ax.set_xlim(left=-0.5)
        if title:
            fig.suptitle(title)
        if show:
            plt.show()

        return fig, ax

    def match(self, item1, item2, *items):
        """
        Associate `item1` exclusively with `item2` and possibly some
        other items in the same category as `item2`.

        A 1-to-1 mapping is one that sets up an equivalence, for example
        "the person in the Green shirt is 72" tall". 72" can connect
        only to Green in the Color category, and Green can connect only
        to 72" in the height category. Their other connections must be
        shared as well. This method recursively applies the logical
        implications of that pruning.

        A 1-to-many mapping is a partial equivalence, like "the person
        in the Green shirt can be 70", 72", or 75" tall". Green can
        connect only to those three items in the Height category, but
        they can (and two of them must) connect to other items in the
        Color category. All connections to other categories that Green
        has must be present in at least one of the Height items as well.
        This method recursively applies the logical implications of that
        pruning as well.

        The inputs may be either item labels or two-element (category,
        label) tuples. The latter is required if items are ambiguous or
        the labels are tuples. The category will be determined
        automatically in the former case.

        The category of `item1` and `item2` may not be the same unless
        they are the same item. Any additional `items` must have the
        same category as `item2`.

        This method removes all possible links from `item1` to items in
        the the category of `item2` that are not in the set comprised of
        `item2` and `items`. See the :ref:`elimination-logic` section
        for more information.

        Parameters
        -----------
        item1 :
            A single item to match.
        item2 :
            Either a single item or one item of a number from the same
            category to match.
        items :
            Optional additional items from the same category as `item2`.

        Return
        ------
        count : int
            The total number of links removed. Zero if the items already
            satisfy the match.
        """
        self._indent()

        pos1, cat1 = self.item_to_pos(item1)
        pos2, cat2 = self.item_to_pos(item2)

        mask = self.cat_mask(cat2)
        mask[pos2] = False

        if items:
            for pos, cat in map(self.item_to_pos, items):
                if cat != cat2:
                    raise ValueError('Item2 categories do not match')
                mask[pos] = False

        if cat1 == cat2:
            if mask.sum() < self.n - 1 or pos1 != pos2:
                raise ValueError('Can not link items in the same category')
            self._log('Matching {0:P:I} against itself: no-op',
                      pos1, start=True)
            return 0

        cm = self.cat_mask(cat2)
        self._log('Matching {0:P:I} with {1:N:C}: {2:M:L}',
                  pos1, cat2, mask ^ cm, start=True)

        unlink = self.matrix[pos1] & mask

        self._log('{0:L:I} has {0:L:X} links to {0:L:C} remaining\n',
                  (pos1, cat2), cont=True)

        count = self._implications(pos1, cat2, unlink)
        self._dedent()
        return count

    def unmatch(self, item1, item2):
        """
        Set two items to be definitely not associated.

        All links between items associated with either one are updated
        as well.

        The inputs may be either item labels or two-element (category,
        label) tuples. The latter is required if items are ambiguous or
        the labels are tuples. The category will be determined
        automatically in the former case.

        Unmatching already unmatched items is a no-op. Unmatching an
        item from itself is an error. The updated relationships are
        pruned recursively according to the description in the he
        :ref:`elimination-logic` section.

        Parameters
        -----------
        item1 :
            An item to unmatch.
        item2 :
            The item to unmatch it from.

        Return
        ------
        count : int
            The number of edges removed. Zero if the items are
            already unmatched.
        """
        self._indent()

        pos1, cat1 = self.item_to_pos(item1)
        pos2, cat2 = self.item_to_pos(item2)

        self._log('Unmatching {0:P:I} from {1:P:I}', pos1, pos2, start=True)
        count = self.unlink(pos1, pos2)

        self._dedent()
        return count

    def less_than(self, item1, item2, category, *bounds):
        """
        .. py:function:: less_than(item1, item2, category[, exact])
        .. py:function:: less_than(item1, item2, category[, lower, upper])

        Assert that the item in `category` linked to `item1` is less
        than the one linked to `item2`.

        The items may or may not be in the same category, but at least
        one of their categories must differ from `category`. All the
        item labels in `category` must be comparable in a way that makes
        sense, which usually means that they are numbers.

        `item1` and `item2` may be either a label or a two-element
        (category, label) tuple. The latter is required if a label is
        ambiguous is a tuple. The category will be determined
        automatically in the former case.

        First, `item1` and `item2` will be :py:meth:`unmatch`\ ed.
        After that, any possibilities that contradict the assertion at
        the time of invocation are removed. If the assertion is not
        fully satisfied, a listener in the shape of an
        :py:class:`Assertion` is set up to continue monitoring for
        additional link removals. The :py:class:`Assertion` removes
        itself as soon as it is satisfied.

        The exact type of assertion depends on the bounds that are
        specified:

        No bounds :
            :py:class:`BoundedExclusiveAssertion`
        Single, `exact` bound :
            :py:class:`OffsetAssertion`
        Two Bounds, `upper` and `lower` :
            :py:class:`BoundedAssertion`

        Parameters
        ----------
        item1 :
            The lesser item to compare.
        item2 :
            The greater item to compare.
        category :
            The category in which to make the comparison.
        bounds :
            Optional bounds for the difference being asserted. If one
            bound is provided, it is an exact match: `item1` is exactly
            `*bounds` less than `item2`. If two bounds are provided,
            they are the inclusive limits for the difference. A bound of
            `None` indicates unbounded (only allowed for the `upper`
            bound).

        Return
        ------
        count : int
            The total number of links removed. Zero if the items already
            satisfy the assertion. Any further removals are made in
            response to additional explicit rules being added to the
            solver.

        Notes
        -----
        If `bounds` are specified, either as an exact match or a range,
        the labels in `category` must support subtraction (``-``
        operator) as well as the ``<`` operator in a meaningful manner.
        Normally, this method will be used for numbers, so the
        restriction is fairly straightforward.
        """
        self._indent()

        self._log('Asserting {0:C:C} for {1:I:I} < {2:I:I}',
                  category, item1, item2, start=True)

        count = self.unmatch(item1, item2)

        nargs = len(bounds)
        if nargs == 0:
            assertion = BoundedExclusiveAssertion(self, item1, item2,
                                                  category, 0, None)
        elif nargs == 1:
            assertion = OffsetAssertion(self, item1, item2,
                                        category, bounds[0])
        elif nargs == 2:
            assertion = BoundedAssertion(self, item1, item2,
                                         category, *bounds)
        else:
            raise TypeError(f'comparison accepts 0, 1 or 2 bounds '
                            '({nargs} given)')

        count += assertion.verify()
        self._indent()
        if not assertion.satisfied:
            self._log('Assertion not fully satisfied: adding')
            self.register_assertion(assertion)
        else:
            self._log('Assertion fully satisfied: not adding')

        self._dedent()
        self._dedent()

        return count

    def greater_than(self, item1, item2, category, *bounds):
        """
        .. py:function:: greater_than(item1, item2, category[, exact])
        .. py:function:: greater_than(item1, item2, category[, lower, upper])

        Assert that the item in `category` linked to `item1` is greater
        than the one linked to `item2`.

        The items may or may not be in the same category, but at least
        one of their categories must differ from `category`. All the
        item labels in `category` must be comparable in a way that makes
        sense, which usually means that they are numbers.

        `item1` and `item2` may be either a label or a two-element
        (category, label) tuple. The latter is required if a label is
        ambiguous is a tuple. The category will be determined
        automatically in the former case.

        First, `item1` and `item2` will be :py:meth:`unmatch`\ ed.
        After that, any possibilities that contradict the assertion at
        the time of invocation are removed. If the assertion is not
        fully satisfied, a listener in the shape of an
        :py:class:`Assertion` is set up to continue monitoring for
        additional link removals. The :py:class:`Assertion` removes
        itself as soon as it is satisfied.

        The exact type of assertion depends on the bounds that are
        specified:

        No bounds :
            :py:class:`BoundedExclusiveAssertion`
        Single, `exact` bound :
            :py:class:`OffsetAssertion`
        Two Bounds, `upper` and `lower` :
            :py:class:`BoundedAssertion`

        Parameters
        ----------
        item1 :
            The greater item to compare.
        item2 :
            The lesser item to compare.
        category :
            The category in which to make the comparison.
        bounds :
            Optional bounds for the difference being asserted. If one
            bound is provided, it is an exact match: `item1` is exactly
            `*bounds` less than `item2`. If two bounds are provided,
            they are the inclusive limits for the difference. A bound of
            `None` indicates unbounded (only allowed for the `upper`
            bound).

        Return
        ------
        count : int
            The total number of links removed. Zero if the items already
            satisfy the assertion. Any further removals are made in
            response to additional explicit rules being added to the
            solver.

        Notes
        -----
        If `bounds` are specified, either as an exact match or a range,
        the labels in `category` must support subtraction (``-``
        operator) as well as the ``<`` operator in a meaningful manner.
        Normally, this method will be used for numbers, so the
        restriction is fairly straightforward.

        This method is a convenience wrapper for ::

            solver.less_than(item2, item1, category, *bounds)

        This is generally not a problem, unless you happen to have
        labels in `category` whose comparison operations do not reflect
        properly.
        """
        return self.less_than(item2, item1, category, *bounds)

    def adjacent_to(self, item1, item2, category, *bounds):
        """
        .. py:function:: adjacent_to(item1, item2, category[, exact=1])
        .. py:function:: adjacent_to(item1, item2, category[, lower, upper])

        Assert that the item in `category` linked to `item1` is within
        some bounds on either side of the one linked to `item2`.

        The items may or may not be in the same category, but at least
        one of their categories must differ from `category`. All the
        item labels in `category` must be comparable in a way that makes
        sense, which usually means that they are numbers.

        `item1` and `item2` may be either a label or a two-element
        (category, label) tuple. The latter is required if a label is
        ambiguous is a tuple. The category will be determined
        automatically in the former case.

        First, `item1` and `item2` will be :py:meth:`unmatch`\ ed.
        After that, any possibilities that contradict the assertion at
        the time of invocation are removed. If the assertion is not
        fully satisfied, a listener in the shape of an
        :py:class:`Assertion` is set up to continue monitoring for
        additional link removals. The :py:class:`Assertion` removes
        itself as soon as it is satisfied.

        The exact type of assertion depends on the bounds that are
        specified:

        No bounds :
            :py:class:`AdjacencyOffsetAssertion`
        Single, `exact` bound :
            :py:class:`AdjacencyOffsetAssertion`
        Two Bounds, `upper` and `lower` :
            :py:class:`BoundedAssertion`

        Parameters
        ----------
        item1 :
            The lesser item to compare.
        item2 :
            The greater item to compare.
        category :
            The category in which to make the comparison.
        bounds :
            Optional bounds for the difference being asserted. If one
            bound is provided, it is an exact match: `item1` is exactly
            `*bounds` less than `item2`. If two bounds are provided,
            they are the inclusive limits for the difference. A bound of
            `None` indicates unbounded (only allowed for the `upper`
            bound).

        Return
        ------
        count : int
            The total number of links removed. Zero if the items already
            satisfy the assertion. Any further removals are made in
            response to additional explicit rules being added to the
            solver.

        Notes
        -----
        If `bounds` are specified, either as an exact match or a range,
        the labels in `category` must support subtraction (``-``
        operator) as well as the ``<`` operator in a meaningful manner.
        Normally, this method will be used for numbers, so the
        restriction is fairly straightforward.
        """
        self._indent()

        self._log('Asserting {0:C:C} for {1:I:I} ~ {2:I:I}',
                  category, item1, item2, start=True)

        count = self.unmatch(item1, item2)

        nargs = len(bounds)
        if nargs == 0:
            assertion = AdjacencyOffsetAssertion(self, item1, item2,
                                                 category, 1)
        elif nargs == 1:
            assertion = AdjacencyOffsetAssertion(self, item1, item2,
                                                 category, bounds[0])
        elif nargs == 2:
            assertion = BandedAssertion(self, item1, item2,
                                        category, *bounds)
        else:
            raise TypeError(f'adjacency accepts 0, 1 or 2 bounds '
                            '({nargs} given)')

        count += assertion.verify()
        self._indent()
        if not assertion.satisfied:
            self._log('Assertion not fully satisfied: adding')
            self.register_assertion(assertion)
        else:
            self._log('Assertion fully satisfied: not adding')

        self._dedent()
        self._dedent()

        return count

    def category_for(self, item, category):
        """
        Determine if `item` has a 1-to-1 mapping to `category`.

        1-to-1 mappings can be set up with :py:meth:`match`, or occur
        naturally as a consequence of other link removals.

        `item` may be either a label or a two-element (category, label)
        tuple. The latter is required if item is ambiguous or the label
        is a tuple. The category will be determined automatically in the
        former case.

        Parameters
        ----------
        item :
            The item to search for links with.
        category :
            The category to search in.

        Return
        ------
        If a mapping is found, return it as an item label. Otherwise,
        return `None`.
        """
        pos1, cat1 = self.item_to_pos(item)
        cat2 = self.categories.index(category)
        links = self.linked_set(pos1, cat2)
        if links.size == 1:
            return self.labels[links[0]]
        return None

    def available_for(self, item, category):
        """
        Find all the items in `category` that `item` can still link to.

        `item` may be either a label or a two-element (category, label)
        tuple. The latter is required if the label is ambiguous or a
        tuple. The category will be determined automatically in the
        former case.

        Parameters
        ----------
        item :
            The item to search for links with.
        category :
            The category to search in.

        Return
        ------
        labels : tuple
            The item labels in `category` that `item` can still link to.
        """
        pos1, cat1 = self.item_to_pos(item)
        cat2 = self.categories.index(category)
        links = self.linked_set(pos1, cat2)
        return tuple(self.labels[p] for p in links)

    def find_missing(self, category):
        """
        Retrieve a set of all the items in category that do not have
        all of their 1-to-1 mappings set.

        Parameters
        ----------
        category :
            The category to search in.

        Return
        ------
        missing : set
            A set of item labels in `category` that still require work.
        """
        cat = self.categories.index(category)
        s = self.cat_slice(cat)

        # 1. Take the N rows in the selected category: self.matrix[start:end]
        # 2. Make it so you have (M * N, N) containing the links between each
        #    item and a given category. Each block of N rows is for the links
        #    between an item and a different category. The N columns are the
        #    items in the *other* category: ...reshape(-1, self.n)
        # 3. Sum across the rows. This gives a count of items that each item
        #    links to in another category: ...sum(axis=1)
        # 4. Reshape into an NxM matrix, where each row corresponds to a row
        #    in the original slice (the selected category) and columns are the
        #    number of links to each other category: ...reshape(self.n, self.m)
        links = self.matrix[s].reshape(-1, self.n).sum(
                                                axis=1).reshape(self.n, self.m)
        # Select any rows that have any missing mappings.
        mask = (links != 1).any(axis=1)
        return set(self.labels[x] for x in np.flatnonzero(mask) + s.start)

    def pos_to_item(self, pos, cat=None):
        """
        Convert a matrix position to a (category, label) tuple.

        Parameters
        ----------
        pos : int
            The index of the item in :py:attr:`matrix`.
        cat : int
            An optional index of the category in :py:attr:`categories`.
            If omitted, it is computed as ``pos // n``.

        Return
        ------
        item : tuple
            A two-element (category, label) tuple providing an
            unambiguous high-level reference to the item.
        """
        if cat is None:
            cat = pos // self.n
        return self.categories[cat], self.labels[pos]

    def item_to_pos(self, item):
        """
        Convert a two-element (category, value) item tuple into a matrix
        position and category index.

        Parameters
        ----------
        item :
            Either a two-element (category, label) tuple, or just an
            item label. Item labels are only accepted if they are not
            tuples and are unambiguous across the entire problem space.

        Return
        ------
        pos : int
            The index of the item within the :py:attr:`matrix`.
        cat : int
            The index of the item's category within
            :py:attr:`categories`.
        """
        if isinstance(item, tuple):
            cat = self.categories.index(item[0])
            pos = self.labels.index(item[1], self.n * cat, self.n * (cat + 1))
        else:
            pos = self.map[item]
            if pos is None:
                raise ValueError(f'Ambiguous item label {item!r}')
            cat = pos // self.n
        return pos, cat

    def unlink(self, pos1, pos2):
        """
        Set two items to be definitely not associated.

        All edges between items associated with either one are updated
        as well.

        This is the low-level equivalent of :py:meth:`unmatch`: the
        inputs are matrix positions.

        Unlinking already unlinked items is a no-op. Unlinking an item
        from itself is an error. The updated relationships are pruned
        recursively according to the description in the he
        :ref:`elimination-logic` section.

        Parameters
        -----------
        pos1 :
            The matrix position of an item to unmatch.
        pos2 :
            The matrix position of the item to unmatch it from.

        Return
        ------
        count : int
            The number of edges removed. Zero if the items are
            already unlinked.
        """
        return self._implications(pos1, pos2 // self.n, self.pos_mask(pos2))

    def find_matches(self, pos):
        """
        Find all items with single links across categories to `pos`.

        A matching item is one that is the only one in its category that
        shares an edge with the item at `pos`.

        Parameters
        ----------
        pos : int
            A row or column in :py:attr:`matrix`.

        Return
        ------
        matches : numpy.ndarray
            A numpy array containing the matching positions.

        """
        # reshape so rows are categories
        row = self.matrix[pos].reshape(self.m, self.n)
        # find indices of the attributes that are linked
        m = np.flatnonzero(row.sum(axis=1) == 1)
        # indices of the items within each linked attribute
        n = np.argmax(row[m, :], axis=1)
        return m * self.n + n

    def _implications(self, pos, cat_hint, mask):
        """
        Remove links between an item and other items, and follow through
        with the logical implications of the removal.

        This method handles removals starting with a single node at
        `pos`. The other endpoints of the edges are given in `mask`.
        `mask` is an array of bits, where `True` elements correspond to
        edges that should be removed. The mask must be `False` at `pos`,
        since a node can not be unlinked from itself. It may contain any
        number of links that have already been removed.

        In addition to the implications of
        :ref:`elimination-logic-explicit` rules, this method will check
        each removed edge against the currently registered assertions.

        See the :ref:`elimination-logic` section for more information.

        Parameters
        ----------
        pos : int
            The matrix position of the starting item to unlink from.
        cat_hint : int or None
            If known, the category in which all items in `mask` belong
            to. `None` if unknown. Any bits in `mask` outside this
            category will be ignored.
        mask : numpy.ndarray
            An array of the same length as a row in :py:attr:`matrix`,
            inidcating the links to remove from `pos`.

        Return
        ------
        count : int
            The total number of links removed.
        """
        self._indent()

        def check(pos, unlink):
            """
            Add the `unlink` array to the stack if it has any elements.
            """
            if unlink.any():
                self._log('Need to remove {0:M:X} edges from {1:P:I}\n',
                          unlink, pos, cont=True)
                stack.append((pos, None, unlink))
            else:
                self._log('All links already shared: nothing to remove\n',
                          cont=True)

        def update_assertions(pos, cat, mask):
            """
            Call the :py:meth:`~Assertion.update` methods of any
            matching :py:class:`Assertion`\ s found in
            :py:attr:`assertions`.
    
            Parameters
            ----------
            pos : int
                One of the potential endpoints of the assertion.
            cat : int
                The linking category of the assertion.
            mask : int or numpy.ndarray
                Either an integer containing a single value for the
                second endpoint, or a mask containing flags marking
                multiple endpoints.

            Return
            ------
            count :
                The number of edges actually removed from the graph as a
                result of this operation.
            """
            key = (pos, cat)
            mask = np.array(mask, ndmin=1)
            if mask.dtype.type is np.bool_:
                mask = np.flatnonzero(mask)
            count = 0
            if key in self.assertions:
                assertions = self.assertions[key]
                self._log('{0:P:P} assertions for {1:P:I} -> {2:N:C}',
                          assertions, pos, cat, cont=True)
                self._indent()
                for pos2 in mask:
                    self._log('Updating all for {0:P:I} x {1:P:I}', pos, pos2)
                    for assertion in assertions:
                        count += assertion.update(pos, pos2)
                self._dedent()
            else:
                self._log('No assertions for {0:P:I} -> {1:N:C}',
                          pos, cat, cont=True)
            return count

        def update(pos, cat, mask):
            """
            Update assertions and check implications of recently deleted
            links.

            This method gets called twice, once for each direction of
            the link. This means that the assertion check only needs to
            happen once per call.

            Parameters
            ----------
            pos : int
                The source node
            cat : int
                The category to check against
            mask : numpy.ndarray or int
                The sink nodes in `cat` that were just removed. If an
                integer, only one sink node. Otherwise, all bits
                represent sink nodes.

            Return
            ------
            count : int
                The number of nodes removed by assersions.
            """
            self._indent()

            self._log('Updating links based on {0:P:I} -> {1:N:C}', pos, cat)

            count = update_assertions(pos, cat, mask)

            # Select items in `cat` that link to `pos`
            rows = self.matrix[self.cat_slice(cat), :]
            selection = rows[:, pos]
            rows = rows[selection]
            other = np.logical_or.reduce(rows, axis=0)

            # Find all shared links
            row = self.matrix[pos]
            matches = row & other

            # Ensure that `pos` only links to those links
            check(pos, matches ^ row)

            if len(rows) == 1:
                pos2 = np.argmax(selection) + cat * self.n
                self._log('{0:P:I} to {1:P:I} is 1-to-1', pos, pos2)
                check(pos2, matches ^ other)

            self._dedent()
            return count

        stack = deque([(pos, cat_hint, mask)])
        count = 0

        self._log('Assessing implications', start=True)

        while stack:
            pos1, cat2, mask = stack.pop()
            cat1 = pos1 // self.n

            if mask[pos1]:
                raise ValueError('Please do not attempt to unlink an item '
                                 f'from itself: {self.pos_to_item(pos1)}')

            if cat2 is None:
                self._log('No category specified for {0:P:I}: splitting', pos1)
                # Check which blocks have items turned on
                for cat in range(len(self.categories)):
                    if cat == cat1:
                        continue
                    ms = mask[self.cat_slice(cat)]
                    if ms.any():
                        if cat2 is None:
                            self._log(
                                'Processing {2:M:X} links from {0:P:I} to '
                                '{1:N:C} now', pos1, cat, ms, cont=True
                            )
                            cat2 = cat
                        else:
                            self._log(
                                'Processing {2:M:X} links from {0:P:I} to '
                                '{1:N:C} later', pos1, cat, ms, cont=True
                            )
                            stack.appendleft((pos1, cat, mask))

                # If no one-bits were found
                if cat2 is None:
                    self._log('Nothing to do!\n', cont=True)
                    continue
                self._log('')

            unlink = self.matrix[pos1] & mask & self.cat_mask(cat2)

            self._log('Removing links from {0:P:I} to {1:N:C}: {2:M:L}',
                      pos1, cat2, unlink)

            delta = unlink.sum()
            count += delta

            if not delta:
                self._log('Nothing to do!', cont=True)
                continue

            self._log('Found {0:M:X} links to {1:N:C}: {0:M:L}\n',
                      unlink, cat2, cont=True)
            self.matrix[pos1, unlink] = self.matrix[unlink, pos1] = False

            count += update(pos1, cat2, unlink)
            for pos2 in np.flatnonzero(mask):
                count += update(pos2, cat1, pos1)

        self._dedent()

        return count

    def linked_set(self, pos, cat):
        """
        Find all links between the specified position and category.

        Parameters
        ----------
        pos : int
            The index of an item within the :py:attr:`matrix`.
        cat : int
            The index of a category within :py:attr:`categories`.

        Return
        ------
        links : numpy.ndarray
            All items in `cat` linked to `pos`, as indices within
            :py:attr:`matrix`.
        """
        s = self.cat_slice(cat)
        return np.flatnonzero(self.matrix[pos, s]) + s.start

    def register_assertion(self, assertion):
        """
        Add `assertion` to :py:attr:`assertions` so that it can be
        triggered as part of
        :ref:`implication <elimination-logic-implications>` analysis.

        This is a utility method that should not be called by the user
        directly under normal circumstances. It is used by the methods
        that implement :ref:`elimination-logic-implicit` rules.
        """
        assertions = self.assertions
        def register(key):
            if key not in assertions:
                assertions[key] = []
            if assertion not in assertions[key]:
                assertions[key].append(assertion)
        register((assertion.pos1, assertion.cat))
        register((assertion.pos2, assertion.cat))

    def remove_assertion(self, assertion):
        """
        Remove `assertion` from :py:attr:`assertions` so that it will no
        longer be triggered in
        :ref:`implication <elimination-logic-implications>` analysis.


        This is a utility method that should not be called by the user
        directly under normal circumstances. It is used by
        :py:class:`Assertion.update` when the assertion is
        :py:attr:`~Assertion.satisfied`.
        """
        assertions = self.assertions
        def remove(key):
            if key in assertions:
                assertions[key].remove(assertion)
                if not assertions[key]:
                    del assertions[key]
        remove((assertion.pos1, assertion.cat))
        remove((assertion.pos2, assertion.cat))

    def cat_slice(self, cat):
        """
        Create a slice that represents the block corresponding to `cat`
        in :py:attr:`matrix`.
        """
        start = cat * self.n
        end = start + self.n
        return slice(start, end)

    def cat_mask(self, cat):
        """
        Create a mask that is ones in the block of :py:attr:`n` elements
        corresponding to `cat`, and `False` elsewhere.
        """
        mask = np.zeros(len(self.labels), dtype=np.bool)
        mask[self.cat_slice(cat)] = True
        return mask

    def pos_mask(self, pos):
        """
        Create a mask that only has the bit at `pos` set to `True`.
        """
        mask = np.zeros(len(self.labels), dtype=np.bool)
        mask[pos] = True
        return mask

    def _indent(self):
        """
        Increase the indentation level if debugging output is enabled.
        """
        if self._debug:
            self._debug += 1

    def _dedent(self):
        """
        Decrease the indentation level if debugging output is enabled.
        """
        if self._debug > 1:
            self._debug -= 1

    def _log(self, fmt, *args, start=False, cont=False):
        """
        If debugging is enabled, print the formatted message, with
        format replacements.

        The :py:attr:`_debug` variable determines the level of
        indentation of the output.

        Arguments are formatted in curly braces. There is an index, an
        input format and an output format, separated by a colon::

            {Index:InputFormat:OutputFormat}

        Index :
            The index of the argument in `args`.
        InputFormat :
            One of the items in the following table.

            +========+=================================+=======================+
            | Format |             Description         |  Valid OutputFormats  |
            +========+=================================+=======================+
            | P      | Matrix position (or int)        | P, I, L, C, N         |
            +--------+---------------------------------+-----------------------+
            | I      | Item: either a label or a tuple | P, I, L, C, N         |
            +--------+---------------------------------+-----------------------+
            | C      | Category label                  | C, N                  |
            +--------+---------------------------------+-----------------------+
            | N      | Category index                  | C, N                  |
            +--------+---------------------------------+-----------------------+
            | M      | Bit Mask                        | P, I, L, X            |
            +--------+---------------------------------+-----------------------+
            | S      | Iterable (set) of positions     | P, I, L, X            |
            +--------+---------------------------------+-----------------------+
            | T      | Tuple with category label set   | P, I, L, C, N, X      |
            +--------+---------------------------------+-----------------------+
            | L      | (position, category) tuple      | P, I, L, C, N, X      |
            +--------+---------------------------------+-----------------------+

        OutputFormat:
            One of the items in the following table.

            +========+==========================+======================+
            | Format |        Description       |  Valid InputFormats  |
            +========+==========================+======================+
            | P      | Matrix position (or int) | P, I, M, S, L        |
            +--------+--------------------------+----------------------+
            | I      | Item as "category:label" | P, I, M, S, L        |
            +--------+--------------------------+----------------------+
            | L      | Item as "label" only     | P, I, M, S, L        |
            +--------+--------------------------+----------------------+
            | C      | Category label           | P, I, C, N, M, S, L  |
            +--------+--------------------------+----------------------+
            | N      | Category index           | P, I, C, N, M, S, L  |
            +--------+--------------------------+----------------------+
            | X      | Count                    | M, S, L              |
            +--------+--------------------------+----------------------+
            | S      | str() representation     | * (iterable if S)    |
            +--------+--------------------------+----------------------+
            | R      | repr() representation    | * (iterable if S)    |
            +--------+--------------------------+----------------------+
            
        """
        if not self._debug:
            return

        def make_iterable(it, func):
            return '{' + ', '.join(func(i) for i in it) + '}'

        def cat_out(cat, fout):
            if fout == 'c':
                return repr(self.categories[cat])
            elif fout == 'n':
                return repr(cat)
            raise ValueError(f'Invalid category format "{fout.upper()}"')

        def pos_out(pos, fout):
            if fout == 'p':
                return repr(pos)
            if fout == 'i':
                return ':'.join(map(repr, self.pos_to_item(pos)))
            if fout == 'l':
                return repr(self.labels[pos])
            raise ValueError(f'Invalid position format "{fout.upper()}"')

        def poss_out(poss, fout):
            if fout == 'x':
                return repr(len(poss))
            return make_iterable(poss, lambda pos: pos_out(pos, fout))

        def sub(index, fin, fout):
            arg = args[index]

            if fout == 'r':
                if fin == 's':
                    return make_iterable(arg, repr)
                return repr(arg)
            if fout == 's':
                if fin == 's':
                    return make_iterable(arg, str)
                return str(arg)

            if fin in 'cn':
                if fin == 'c':
                    arg = self.categories.index(arg)
                return cat_out(arg, fout)

            if fin in 'lmst':
                if fin == 'l':
                    pos, cat = arg
                    if fout in 'cn':
                        return cat_out(cat, fout)
                    if fout in 'pil':
                        return pos_out(pos, fout)
                    arg = np.flatnonzero(self.matrix[pos] & self.cat_mask(cat))
                elif fin == 'm':
                    arg = np.flatnonzero(arg)
                elif fin == 't':
                    category, items = arg
                    arg = [self.item_to_pos((category, item))[0]
                           for item in items]
                    if fout in 'cn':
                        cat = self.categories.index[category]
                        return cat_out(cat, fout)
                arg = sorted(set(arg))
                if len(arg) == 1 and fout != 'x':
                    return pos_out(arg[0], fout)
                return poss_out(arg, fout)
            elif fin == 'i':
                arg = self.item_to_pos(arg)[0]
            elif fin != 'p':
                raise ValueError(f'Invalid input format "{fin.upper()}"')

            if fout in 'cn':
                return cat_out(arg // self.n, fout)
            return pos_out(arg, fout)

        def replace(match):
            index = int(match.group(1))
            fin = match.group(2).lower()
            fout = match.group(3).lower()
            return sub(index, fin, fout)

        output = re.sub('{(\d+):(.):(.)}', replace, fmt)

        print(' ' * (4 * (self._debug - 2)), end='')
        if start:
            print('*** ', end='')
        if cont:
            print('|-> ', end='')
        print(output, end='')
        if start:
            print(' ***')
        print()


class Assertion:
    """
    Implements indirect rules for the solver.

    Assertions do not exist independently of a :py:class:`Solver`. They
    are registered through high-level methods like
    :py:meth:`Solver.greater_than`, and removed once they are
    :py:attr:`satisfied`.

    An example of an assertion is "The green thing is next to the 78lb
    thing". Until the implicit position of both "green" and "78lb" are
    known, the assertion will hang around and hopefully help prune some
    edges here and there.

    In general, assertions link two nodes through a category. The
    category may be the category of either linked item, but usually is
    not in practice.

    This class is abstract. Child classes are provided to implement the
    various comparisons supported by the solver. The list of assertions
    currently provided by the module is based on the instances of
    puzzles that inspired it rather than completeness. Feel free to add
    more, and give examples of the sorts of rules they implement.
    """
    def __init__(self, solver, item1, item2, category, key=None):
        """
        Set up an assertion linking two items of interest via a
        category.

        `item1` and `item2` may be either a label or a two-element
        (category, label) tuple. The latter is required if a label is
        ambiguous is a tuple. The category will be determined
        automatically in the former case.

        Depending on the assertion, the order of the items may matter.

        Parameters
        ----------
        solver : Solver
            The solver that this assertion operates in.
        item1 :
            The first item of interest.
        item2 :
            The second item of interest.
        category :
            The label of the category that links the items.
        """
        self._dict__['solver'] = solver
        self.__dict__['pos1'], self.__dict__['cat1'] = \
            solver.item_to_pos(item1)
        self.__dict__['pos2'], self.__dict__['cat2'] = \
            solver.item_to_pos(item2)
        self.__dict__['cat'] = solver.categories.index(category)
        self.__dict__['key'] = self.default_key if key is None else key
        self.__dict__['_cat_slice'] = solver.cat_slice(self.cat)
        self._depth = 0

    def __repr__(self):
        """
        Return a computer-readable-ish string representation.
        """
        return f'{type(self).__name__}(solver, {", ".join(self._rlabels())})'

    def __str__(self):
        """
        Return a human readable string representation.

        The default implementation delegates to :py:meth:`__repr__`, so
        child classes should override it.
        """
        return repr(self)

    @property
    def solver(self):
        """
        The :py:class:`Solver` that this assertion is part of.
        """
        return self.__dict__['solver']

    @property
    def pos1(self):
        """
        The index of the first item this assertion links, as a position
        in :py:attr:`solver`\ 's :py:attr:`~Solver.matrix`.
        """
        return self.__dict__['pos1']

    @property
    def cat1(self):
        """
        The category index of the first item this assertion links, as an
        index into :py:attr:`solver`\ 's :py:attr:`~Solver.categories`.

        This may or may not be the same as :py:attr:`cat` and
        :py:attr:`cat2`.
        """
        return self.__dict__['cat1']

    @property
    def pos2(self):
        """
        The index of the second item this assertion links, as a position
        in :py:attr:`solver`\ 's :py:attr:`~Solver.matrix`.
        """
        return self.__dict__['pos2']

    @property
    def cat2(self):
        """
        The category index of the second item this assertion links, as
        an index into :py:attr:`solver`\ 's :py:attr:`~Solver.categories`.

        This may or may not be the same as :py:attr:`cat` and
        :py:attr:`cat1`.
        """
        return self.__dict__['cat2']

    @property
    def cat(self):
        """
        The index of the category through which the items in this
        assertion are linked.

        This may or may not be the same as either of :py:attr:`cat1` and
        :py:attr:`cat2`, but it can't be the same as both.
        """
        return self.__dict__['cat']

    @property
    def key(self):
        """
        A function that maps the items in :py:attr:`cat` to comparable
        values.

        This function must accept a :py:class:`Solver` and a matrix
        position as arguments. The return value is the type of key that
        :py:meth:`op` supports. The default implementation of this
        method is :py:meth:`default_key`, which just maps the position
        to the corresponding label.

        All currently implemented assertions have a built-in assumption
        that the result of this function will be a number, but this is
        not a requirement in the general case.
        """
        return self.__dict__['key']

    @property
    def satisfied(self):
        """
        Determines if this assertion has been satisfied based on the
        additional information provided to the solver.

        An assertion is satisfied when the number of links between each
        of the items of interest and the linking category is one.
        """
        s1 = self.solver.matrix[self.pos1, self._cat_slice].sum()
        s2 = self.solver.matrix[self.pos2, self._cat_slice].sum()
        return s1 == s2 == 1

    @property
    def _cat_slice(self):
        """
        A :py:class:`slice` object used to access the elements that
        correspond to :py:attr:`cat` in a matrix row.

        This is provided as a convenience to avoid calling
        :py:meth:`Solver._cat_slice` multiple times.
        """
        return self.__dict__['_cat_slice']

    def verify(self):
        """
        Check the assertion for all available links from the items to
        the category, and remove any invalid possibilities.

        This method may end up being recursive if a link removal
        triggers a re-verification of this assertion. In that case, the
        current execution will be aborted in favor of the updated one.
        """
        self.solver._indent()

        # Initialize the 
        self._depth += int(copysign(self._depth, 1))
        depth = self._depth

        self.solver._log('Verifying assertion {0:*:S}', self, start=True)
        self.solver._log('Current Depth = {0:P:P}', depth, cont=True)

        count = 0

        options1 = {self.key(self.solver, pos): pos 
                    for pos in self.solver.linked_set(self.pos1, self.cat)}
        options2 = {self.key(self.solver, pos): pos
                    for pos in self.solver.linked_set(self.pos2, self.cat)}
        to_check2 = options2.copy()

        self.solver._log('{0:N:C} options for {1:P:I}: {2:S:L}',
                         self.cat, self.pos1, options1, cont=True)
        self.solver._log('{0:N:C} options for {1:P:I}: {2:S:L}\n',
                         self.cat, self.pos2, options2, cont=True)

        self.solver._log('Checking options for {0:P:I}', self.pos1)
        self.solver._indent()

        for i1 in options1:
            i2 = self.is_valid(i1, options2.keys())
            p1 = options1[i1]
            if i2 is None:
                self.solver._log('No match for {0:P:I}: unlinking from {1:P:I}',
                                 p1, self.pos1)
                count += self.solver.unlink(p1, self.pos1)
                if not self._check_depth(depth):
                    return count
            else:
                p2 = options2[i2]
                self.solver._log('{0:P:I} matches {1:P:I}', p1, p2)
                to_check2.pop(i2, None)

        self.solver._dedent()
        self.solver._log('Checking remaining options for {0:P:I}', self.pos2)
        self.solver._indent()

        for i2 in to_check2:
            i1 = self.is_valid(i2, options1.keys(), reverse=True)
            p2 = to_check2[i2]
            if i1 is None:
                self.solver._log('No match for {0:P:I}: unlinking from {1:P:I}',
                                 p2, self.pos2)
                count += self.solver.unlink(p2, self.pos2)
                if not self._check_depth(depth):
                    return count
            else:
                p1 = options1[i1]
                self.solver._log('{0:P:I} matches {1:P:I}', p2, p1)

        self.solver._dedent()

        if self._depth > 0 and self.satisfied:
            self.solver.remove_assertion(self)
            self._depth = -self._depth

        if depth == 1:
            self._depth = 0

        self.solver._dedent()
        return count

    def op(self, key1, key2):
        """
        The comparison operation that this assertion represents.

        This method is applied to items in the linking category after
        the key function has been applied to them. The key function is
        just the item label by default, but does not have to be. The
        order of the inputs matters (in the general case).

        Parameters
        ----------
        key1 :
            The first (left) item key to compare.
        key2 :
            The second (right) item key to compare.

        Return
        ------
        bool :
            A flag determining if the comparison succeeded or not.
        """
        raise NotImplementedError('Please implement this method in a '
                                  'child class')

    def is_valid(self, key, options, reverse=False):
        """
        Verify that there is at least one option ``opt`` in `options`
        that returns `True` for ``op(key, opt)``.

        The key is just the item label by default, but does not have to
        be.

        The default implementation performs a linear search of
        `options` using :py:meth:`op`. This method is provided to allow
        children to optimize the comparison.

        Parameters
        ----------
        key :
            The item key to check.
        options : set
            A set of options to compare against.
        reverse : bool
            If `True`, the comparison is ``op(opt, key)`` instead of
            the usual ``op(key, opt)``.

        Return
        ------
        opt :
            The first encountered option that makes `item` valid, or
            `None` if invalid.
        """
        op = (lambda key, opt: self.op(opt, key)) if reverse else self.op
        checker = (opt for opt in options if op(key, opt))
        return next(checker, None)

    def update(self, pos12, posC):
        """
        Called when a link that is between either :py:attr:`pos1` or
        :py:attr:`pos2` and `posC` in :py:attr:`cat` is severed.

        The default is to re-:py:meth:`verify` the assersion as long as
        `pos12` is indeed either :py:attr:`pos1` or :py:attr:`pos2` and
        `posC` is in :py:attr:`cat`.

        An assertion must remove itself if it is satisfied by an update.
        """
        self.solver._indent()
        if pos12 not in (self.pos1, self.pos2):
            self.solver._log('Skipping update: {0:P:I} is neither{1:P:I} '
                             'nor {2:P:I}', pos12, self.pos1, self.pos2)
            self._dedent()
            return 0
        if posC // self.solver.n != self.cat:
            self.solver._log('Skipping update: {0:P:I} is not in {2:N:C}',
                             posC, self.cat)
            self._dedent()
            return 0
        self.solver._log('Triggering Verification')
        count = self.verify()
        self.solver._dedent()
        if self.satisfied:
            self.solver.remove_assertion(self)
        return count

    def default_key(self, solver, pos):
        """
        The default value for comparison is just the `solver`\ 's label
        at `pos`.

        The key function can either be passed in the constructor or
        overriden in a child class. In either case, it must accept a
        :py:class:`Solver` object and a matrix position as arguments.
        """
        return solver.labels[pos]

    def _check_depth(self, depth):
        """
        Check if :py:meth:`verify` has been called since the current
        `depth` was entered.

        If the current :py:attr:`_depth` does not match `depth`, return
        `False`. If `depth` is 0 or 1, reset :py:attr:`_depth` to 0
        since the stack is unwound.
        """
        if depth != self._depth:
            if depth == 1:
                self._depth = 0
            return False
        return True

    def _labels(self):
        """
        Retrieves the labels for :py:attr:`pos1`, :py:attr:`pos2` and
        :py:attr:`cat`, for use with :py:meth:`__str__`.
        """
        i1 = ':'.join(map(repr, self.solver.pos_to_item(self.pos1)))
        i2 = ':'.join(map(repr, self.solver.pos_to_item(self.pos2)))
        c = repr(self.solver.categories[self.cat])
        return i1, i2, c

    def _rlabels(self):
        """
        Retrieves the labels for :py:attr:`pos1`, :py:attr:`pos2` and
        :py:attr:`cat`, for use with :py:meth:`__repr__`.
        """
        i1 = '(' + ', '.join(map(repr,
                                 self.solver.pos_to_item(self.pos1))) + ')'
        i2 = '(' + ', '.join(map(repr,
                                 self.solver.pos_to_item(self.pos2))) + ')'
        c = repr(self.solver.categories[self.cat])
        return i1, i2, c


class AsymmetricAssertionMixin:
    """
    A mixin class for assertions that care about the direction of the
    difference between keys.
    """
    def value(self, key1, key2):
        """
        Return the signed difference ``key2 - key1``.
        """
        return key2 - key1


class SymmetricAssertionMixin:
    """
    A mixin class for assertions that care only about the magnitude of
    the difference between keys.
    """
    def value(self, key1, key2):
        """
        Return the absolute value of the difference ``|key2 - key1|``.
        """
        return abs(key2 - key1)


class OffsetAssertion(AsymmetricAssertionMixin, Assertion):
    """
    Assert that two items are a fixed distance from each other in a
    particular order.
    """
    def __init__(self, solver, item1, item2, category, offset):
        """
        Set up an assertion that ``item2 - item1 == offset``.

        Parameters
        ----------
        solver : Solver
            The solver that this assertion operates in.
        item1 :
            The first item of interest.
        item2 :
            The second item of interest.
        category :
            The label of the category that links the items.
        offset :
            The required difference between the items, with sign and
            magnitude.
        """
        super().__init__(solver, item1, item2, category)
        self.__dict__['offset'] = offset

    def __repr__(self):
        """
        Return a computer-readable-ish string representation.
        """
        return f'{super().__repr__()[:-1]}, {self.offset!r})'

    def __str__(self):
        """
        Return a human readable string representation.
        """
        i1, i2, c = self._labels()
        return f'Assert that {c} of {i1} + {self.offset} == {c} of {i2}'

    @property
    def offset(self):
        """
        The offset separating the items.
        """
        return self.__dict__['offset']

    def op(self, key1, key2):
        """
        Checks if the difference between two items is :py:attr:`offset`.

        The difference is computed by
        :py:meth:`AsymmetricAssertionMixin.value`.
        """
        return self.value(key1, key2) == self.offset

    def is_valid(self, key, options, reverse=False):
        """
        An optimized version of the default
        :py:meth:`Assertion.is_valid` method.

        Since :py:attr:`.offset` is fixed, a simple check as to whether
        ``key + offset`` is in `options` suffices. For the `reverse`
        case, we check ``key - offset``.
        """
        key = key - self.offset if reverse else key + self.offset
        if key in options:
            return key
        return None


class AdjacencyOffsetAssertion(SymmetricAssertionMixin, OffsetAssertion):
    """
    Assert that two items are a fixed distance from each other,
    regardless of direction.
    """
    def is_valid(self, key, options, reverse=False):
        """
        An optimized version of the default
        :py:meth:`Assertion.is_valid` method.

        Since :py:attr:`.offset` is fixed, a simple check as to whether
        one of ``key + offset`` or ``key - offset`` is in `options`
        suffices.
        """
        key1 = key + self.offset
        if key1 in options:
            return key1
        key2 = key - self.offset
        if key2 in options:
            return key2
        return None

    def __str__(self):
        """
        Return a human readable string representation.
        """
        i1, i2, c = self._labels()
        return f'Assert that {i1} and {i2} are {self.offset} apart in {c}'


class BoundedAssertion(AsymmetricAssertionMixin, Assertion):
    """
    Assert that two items are withn a range of values from each other,
    like :py:class:`BoundedExclusiveAssertion`, but inclusive of both
    ends.

    The direction matters for this assertion.
    """
    def __init__(self, solver, item1, item2, category, lower, upper):
        """
        Set up an assertion that
        ``[lower <=] item2 - item1 [<= upper]``.

        Parameters
        ----------
        solver : Solver
            The solver that this assertion operates in.
        item1 :
            The first item of interest.
        item2 :
            The second item of interest.
        category :
            The label of the category that links the items.
        lower :
            The optional lower bound for the comparison. If omitted the
            difference just has to be less than or equal to `upper`.
        upper :
            The optional upper bound for the comparison. If omitted the
            difference just has to be greater than or equal to `lower`.
        """
        super().__init__(solver, item1, item2, category)
        self.__dict__['lower'] = lower
        self.__dict__['upper'] = upper

    def __repr__(self):
        """
        Return a computer-readable-ish string representation.
        """
        return f'{super().__repr__()[:-1]}, {self.lower!r}, {self.upper!r})'

    def __str__(self):
        """
        Return a human readable string representation.
        """
        i1, i2, c = self._labels()
        l = '' if self.lower is None else f'{self.lower!r} <= '
        u = '' if self.upper is None else f' <= {self.upper!r}'
        return f'Assert that {l}{i1} - {i2}{u} in {c}'

    @property
    def lower(self):
        """
        The inclusive lower bound of the comparison.

        If `None`, the comparison is unbounded on the low end.
        """
        return self.__dict__['lower']

    @property
    def upper(self):
        """
        The inclusive upper bound of the comparison.

        If `None`, the comparison is unbounded on the high end.
        """
        return self.__dict__['upper']

    def op(self, key1, key2):
        """
        Check if the difference between two items is between
        :py:attr:`lower` and :py:attr:`upper`, inclusive.

        Unset bounds are not checked. That part of the test always
        evaluates to `True`.

        The difference is computed by
        :py:meth:`AsymmetricAssertionMixin.value`.
        """
        diff = self.value(key1, key2)
        if self.lower is not None and diff < self.lower:
            return False
        if self.upper is not None and diff > self.upper:
            return False
        return True

    def is_valid(self, key, options, reverse=False):
        """
        In some cases, it is possible to optimize the default
        :py:meth:`Assertion.is_valid` method.

        If both bounds are :py:class:`int`, meaning that the search
        space is finite and discrete, it may be faster to check the
        range of offsets rather than finding a match in `options`
        directly. The reverse case is computed by swapping the bounds
        and their signs.

        If an optimization is possible, the bounds of the search space
        are is computed by :py:meth:`bounds`, the iterator over the
        space by :py:meth:`space`, and the size of it by
        :py:meth:`nspace`.
        """
        if not isinstance(self.upper, int) or not isinstance(self.lower, int) \
                        or self.nspace() > len(options):
            return super().is_valid(key, options, reverse)

        self.solver._indent()
        self.solver._log('Optimized search possible for {0:*:R} among {1:S:R}',
                         key, options)

        lower, upper = self.bounds(reverse)
        space = self.space(key, lower, upper)
        checker = (s for s in space if s in options)

        self.solver._dedent()
        return next(checker, None)

    def bounds(self, reverse):
        """
        Compute the bounds of the space of possibilities for the
        difference between the items.

        This method should only be used after checking that
        :py:attr:`lower` and :py:attr:`upper` can both be negated. It
        allows child classes to override the type of difference the
        assertion checks for.

        If `reverse` is set, the bounds are reversed and negated.
        """
        if reverse:
            return -self.upper, -self.lower
        return self.lower, self.upper

    def space(self, key, lower, upper):
        """
        Create an iterator of all valid possibilities with `key` as the
        first item in the comparison.

        This method should only be used after ensuring that `lower` and
        `upper` are both integers. It allows child classes to override
        the type of difference that the assertion checks for.
        """
        return range(key + lower, key + upper + 1)

    def nspace(self):
        """
        The number of elements in the iterator returned by
        :py:meth:`space`.

        This method allows a check to determine if the search can be
        optimized before actually creating the iterator. This method
        should only be used after ensuring that :py:attr:`lower` and
        :py:attr:`upper` are both integers. It allows child classes to
        override the type of difference that the assertion checks for.
        """
        return self.upper - self.lower + 1


class BoundedExclusiveAssertion(BoundedAssertion):
    """
    Assert that two items are withn a range of values from each other,
    like :py:class:`BoundedAssertion`, but exclusive of both ends.

    The direction matters for this assertion.
    """
    def __str__(self):
        """
        Return a human readable string representation.
        """
        i1, i2, c = self._labels()

        if self.lower == 0 and self.upper is None:
            return f'Assert that {i1} < {i2} in {c}'
        if self.lower is None and self.upper == 0:
            return f'Assert that {i1} > {i2} in {c}'

        l = '' if self.lower is None else f'{self.lower!r} < '
        u = '' if self.upper is None else f' < {self.upper!r}'
        return f'Assert that {l}{i1} - {i2}{u} in {c}'

    def op(self, key1, key2):
        """
        Check if the difference between two items is between
        :py:attr:`~BoundedAssertion.lower` and
        :py:attr:`~BoundedAssertion.upper`, exclusive.

        Unset bounds are not checked. That part of the test always
        evaluates to `True`.

        The difference is computed by
        :py:meth:`AsymmetricAssertionMixin.value`.
        """
        diff = self.value(key1, key2)
        if self.lower is not None and diff <= self.lower:
            return False
        if self.upper is not None and diff >= self.upper:
            return False
        return True

    def space(self, key, lower, upper):
        """
        Create an iterator of all valid possibilities with `key` as the
        first item in the comparison.

        This method should only be used after ensuring that `lower` and
        `upper` are both integers. It allows child classes to override
        the type of difference that the assertion checks for.
        """
        return range(key + lower + 1, key + upper)

    def nspace(self):
        """
        The number of elements in the iterator returned by
        :py:meth:`space`.

        This method allows a check to determine if the search can be
        optimized before actually creating the iterator. This method
        should only be used after ensuring that
        :py:attr:`~BoundedAssertion.lower` and
        :py:attr:`~BoundedAssertion.upper` are both integers. It allows
        child classes to override the type of difference that the
        assertion checks for.
        """
        return self.upper - self.lower - 1


class BandedAssertion(SymmetricAssertionMixin, BoundedAssertion):
    """
    Assert that two items are with a range of values from eachother,
    irrespective of direction, inclusive of both bounds.
    """
    def __str__(self):
        """
        Return a human readable string representation.
        """
        i1, i2, c = self._labels()

        if self.upper is None:
            return ('Assert that distance between '
                    f'{i1} and {i2} >= {self.lower} in {c}')
        if self.lower is None:
            return ('Assert that distance between '
                    f'{i1} and {i2} <= {self.lower} in {c}')

        l = '' if self.lower is None else f'{self.lower} <= '
        u = '' if self.upper is None else f' <= {self.upper}'
        return f'Assert that distance between {l}{i1} and {i2}{u} in {c}'

    def bounds(self, reverse):
        """
        Compute the bounds of the space of possibilities for the
        difference between the items.

        This method ignores `reverse` because the bounds are symmetric
        about the origin. Both bounds should be positive.
        """
        return self.lower, self.upper

    def space(self, key, lower, upper):
        """
        Create an iterator of all valid possibilities with `key` as the
        first item in the comparison.

        The iterator will contain two distjoined portions.

        This method should only be used after ensuring that `lower` and
        `upper` are both integers. It allows child classes to override
        the type of difference that the assertion checks for.
        """
        if lower == 0:
            return range(key - upper, key + upper + 1)
        return chain(range(key - upper, key - lower + 1),
                     range(key + lower, key + upper + 1))

    def nspace(self):
        """
        The number of elements in the iterator returned by
        :py:meth:`space`.

        The value returned by this method is twice the one returned by
        :py:meth:`BoundedAssertion.nspace` because it is symmetric about
        the origin.

        This method allows a check to determine if the search can be
        optimized before actually creating the iterator. This method
        should only be used after ensuring that
        :py:attr:`~BoundedAssertion.lower` and
        :py:attr:`~BoundedAssertion.upper` are both integers. It allows
        child classes to override the type of difference that the
        assertion checks for.
        """
        return 2 * (self.upper - self.lower + 1)
