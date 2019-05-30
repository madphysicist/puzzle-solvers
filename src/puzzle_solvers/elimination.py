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
Process-of-elimination puzzles are implemented in the
:py:mod:`puzzle_solvers.elimination` module. These puzzles generally
take the form of a number of different categories of items that must be
matched uniquely against each other based on rules that direct the
elimination of possibilities. An example of such a puzzle is found in
the corresponding :ref:`elimination-tutorial` section.
"""

from collections import deque
from collections.abc import Mapping
from itertools import combinations, cycle
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
    the range :math:`[0, M * N)`. :py:meth:`match` and :py:meth:`unlink`
    are high level methods. Low level methods support the logic of
    high level methods. :py:meth:`implications` and
    :py:meth:`find_matches` are low level methods.

    Positions used by the low level methods can be converted to an
    index within :py:attr:`categories` and an index within that category
    using :py:func:`divmod`: the quotient with :py:attr:`n` is the
    category index, while the remainder is the index within the
    category.
    """
    def __init__(self, problem, categories=None, debug=False):
        """
        Create a solver for a particular elimination problem.

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
        self._debug = debug

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
        if self._debug:
            print(f'New solver with {self.m} categories, {self.n} items')
            print(f'Matrix is {self.matrix.shape[0]}x{self.matrix.shape[1]}')
            print(f'Items:')
            for i, label in enumerate(self.labels):
                if i % self.n == 0:
                    print(f'    {self.categories[i // self.n]!r}')
                print(
                    f'        {label!r} '
                    f'({"Ambigous" if self.map[label] is None else "Unique"})'
                )
            print()
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

        This method regenerates the adjacency matrix.
        """
        self.matrix.fill(True)
        cat = 0
        while cat < self.n * self.m:
            next = cat + self.n
            self.matrix[cat:next, cat:next] = False
            cat = next
        np.fill_diagonal(self.matrix, True)
        if self._debug:
            print(f'Reset matrix with {self.edges} edges')
            print()

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
        pos1, cat1 = self.item_to_pos(item1)
        pos2, cat2 = self.item_to_pos(item2)

        if items:
            poss, cats = zip(*map(self.item_to_pos, items))
            if len(set(cats)) > 1 or cats[0] != cat2:
                raise ValueError('Item2 categories do not match')
            poss = set(poss)
            poss.add(pos2)
        else:
            poss = set([pos2])

        if cat1 == cat2:
            if len(poss) > 1 or pos1 != pos2:
                raise ValueError('Can not link items in the same category')
            return 0

        if self._debug:
            print(
                f'Matching {self.pos_to_item(pos1, cat1)} with '
                f'({self.categories[cat2]!r}, ',
                end='' if len(poss) == 1 else '{ '
            )
            for pos in poss:
                print(f'{self.labels[pos]!r}',
                      end='' if len(poss) == 1 else ', ')
            if len(poss) > 1:
                print('}', end='')
            print(')')

        links = self.linked_set(pos1, cat2)
        unlink = links - poss

        if self._debug:
            print(f'    {self.pos_to_item(pos1, cat1)} has {len(links)} links '
                  f'to {self.categories[cat2]!r} remaining')

        if unlink:
            if self._debug:
                print(f'    Unlinking {len(unlink)} edges:')

            stack = [(pos1, cat2)]
            for p in unlink:
                self._set_link(pos1, p, False)
                stack.append((p, cat1))
                if self._debug:
                    print(f'        {self.pos_to_item(pos1, cat1)} != '
                          f'{self.pos_to_item(p, cat2)}')
            return len(unlink) + self.implications(stack)

        if self._debug:
            print('    Nothing to unlink!')
            print()

        return 0

    def unlink(self, item1, item2):
        """
        Set two items to be definitely not associated.

        All links between items associated with either one are updated
        as well.

        The inputs may be either item labels or two-element (category,
        label) tuples. The latter is required if items are ambiguous or
        the labels are tuples. The category will be determined
        automatically in the former case.

        Unlinking already unlinked items is a no-op. Unlinking an item
        from itself is an error. The updated relationships are pruned
        recursively according to the description in the he
        :ref:`elimination-logic` section.

        Parameters
        -----------
        item1 :
            An item to unlink.
        item2 :
            The item to unlink it from.

        Return
        ------
        count : int
            The number of links removed. Zero if the items are
            already unlinked.
        """
        pos1, cat1 = self.item_to_pos(item1)
        pos2, cat2 = self.item_to_pos(item2)

        if pos1 == pos2:
            raise ValueError('Please do not unlink an item from itself')

        if self._debug:
            print(f'Unlinking {self.pos_to_item(pos1, cat1)} from '
                  f'{self.pos_to_item(pos2, cat2)}')

        if self.matrix[pos1, pos2]:
            self._set_link(pos1, pos2, False)
            return 1 + self.implications([(pos1, cat2), (pos2, cat1)])

        if self._debug:
            print('    Noting to do, already unlinked!')
            print()
        return 0

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
        if len(links) == 1:
            return self.labels[links.pop()]
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

    def less_than(self, item1, item2, category, *bounds):
        """
        less_than(item1, item2, category[, exact=None])
        less_than(item1, item2, category[, lower, upper])

        Assert that the item in `category` linked to `item1` is less
        then the one linked to `item2`.

        First, `item1` and `item2` will be :py:meth:`unlink`\ ed. After
        that, any possibilities that contradict the assertion at the
        time of invocation are removed. This method may need to be
        called multiple times as more data becomes available, as the
        solver does not record assertions yet. The assertion is applied
        in a loop, which runs as long as edges are being removed.

        The items may or may not be in the same category, but at least
        one of their categories must differ from `category`. All the
        items in `category` must be comparable in a way that makes
        sense.

        `item1` and `item2` may be either a label or a two-element
        (category, label) tuple. The latter is required if a label is
        ambiguous is a tuple. The category will be determined
        automatically in the former case.

        Parameters
        ----------
        item1 :
            The lesser item to compare.
        item2 :
            The greater item to compare.
        category :
            The category in which to make the comparison.
        bounds :
            Optional bounds for the assertion. If one bound is provided,
            it is an exact match: `item1` is exactly `*bounds` less than
            `item2`. If two bounds are provided, they are the inclusive
            limits for the difference. A bound of `None` indicates
            unbounded (only allowed for the upper bound).

        Return
        ------
        count : int
            The total number of links removed. Zero if the items already
            satisfy the assertion.

        Notes
        -----
        If `bounds` are specified, either as an exact match or a range,
        the labels in `category` must support subtraction (``-``
        operator) as well as the ``<`` operator in a meaningful manner.
        Normally, this method will be used for numbers, so the
        restriction is fairly straightforward.
        """
        count = self.unlink(item1, item2)

        if self._debug:
            item1 = self.pos_to_item(*self.item_to_pos(item1))
            item2 = self.pos_to_item(*self.item_to_pos(item2))
            print(f'Asserting {category!r} of {item1} < {item2}')

        nargs = len(bounds)
        if nargs == 0:
            key = lambda x1, x2: x1 < x2
            if self._debug:
                print(f'    Unbounded comparison of {category!r}')
        elif nargs == 1:
            exact = bounds[0]
            key = lambda x1, x2: x2 - x1 == exact
            if self._debug:
                print(f'    Difference in {category!r} == {exact!r}')
        elif nargs == 2:
            lower, upper = bounds
            if upper is None:
                key = lambda x1, x2: x2 - x1 >= lower
                if self._debug:
                    print(f'    Difference in {category!r} >= {lower!r}')
            else:
                key = lambda x1, x2: lower <= x2 - x1 <= upper
                if self._debug:
                    print(f'    {upper!r} >= Difference in '
                          f'{category!r} >= {lower!r}')
        else:
            raise TypeError(f'comparison accepts 0, 1 or 2 bounds '
                            '({nargs} given)')

        options1 = self.available_for(item1, category)
        options2 = self.available_for(item2, category)

        if self._debug:
            print(f'    Options for {item1}: {{ {", ".join(map(repr, options1))} }}')
            print(f'    Options for {item2}: {{ {", ".join(map(repr, options2))} }}')

        prev = count - 1
        while prev != count:
            prev = count

            valid1 = []
            for i1 in options1:
                test = (i for i in (key(i1, i2) for i2 in options2) if i)
                if next(test, None) is None:
                    count += self.unlink(item1, i1)
                else:
                    valid1.append(i1)
    
            valid2 = []
            for i2 in options2:
                test = (i for i in (key(i1, i2) for i1 in options1) if i)
                if next(test, None) is None:
                    count += self.unlink(item2, i2)
                else:
                    valid2.append(i2)

        return count

    def greater_than(self, item1, item2, category, *bounds):
        """
        greater_than(item1, item2, category[, exact=None])
        greater_than(item1, item2, category[, lower, upper])

        Assert that the item in `category` linked to `item1` is greater
        then the one linked to `item2`.

        First, `item1` and `item2` will be :py:meth:`unlink`\ ed. After
        that, any possibilities that contradict the assertion at the
        time of invocation are removed. This method may need to be
        called multiple times as more data becomes available, as the
        solver does not record assertions yet. The assertion is applied
        in a loop, which runs as long as edges are being removed.

        The items may or may not be in the same category, but at least
        one of their categories must differ from `category`. All the
        items in `category` must be comparable in a way that makes
        sense.

        `item1` and `item2` may be either a label or a two-element
        (category, label) tuple. The latter is required if a label is
        ambiguous is a tuple. The category will be determined
        automatically in the former case.

        Parameters
        ----------
        item1 :
            The greater item to compare.
        item2 :
            The lesser item to compare.
        category :
            The category in which to make the comparison.
        bounds :
            Optional bounds for the assertion. If one bound is provided,
            it is an exact match: `item1` is exactly `*bounds` greater
            than `item2`. If two bounds are provided, they are the
            inclusive limits for the difference. A bound of `None`
            indicates unbounded (only allowed for the upper bound).

        Return
        ------
        count : int
            The total number of links removed. Zero if the items already
            satisfy the assertion.

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
        start = cat * self.n
        end = start + self.n

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
        links = self.matrix[start:end].reshape(-1, self.n).sum(
                                                axis=1).reshape(self.n, self.m)
        # Select any rows that have any missing mappings.
        mask = (links != 1).any(axis=1)
        return set(self.labels[x] for x in np.flatnonzero(mask) + start)

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

    def implications(self, stack=()):
        """
        Follow through with/update the logic of relationships between an
        items and different categories.

        `stack` is an iterable of starting relationships containing
        (position, category index) pairs. It is used to seed the stack
        of a recursive process. As edges are removed, additional
        relationships are verified. See the :ref:`elimination-logic`
        section for more information.

        Parameters
        ----------
        stack :
            An iterable contaiing the initial set of (position,
            category index) pairs to update.

        Return
        ------
        count : int
            The total number of links removed.
        """
        def check(keep, pos):
            """
            Check which elements of row ``self.matrix[pos]`` must be
            removed to reduce the row to `keep`. If any elements are
            removed, both the forward and backward links are added to the
            stack for further checkup.
            """
            row = self.matrix[pos]
            unlink = keep ^ row
            count = unlink.sum()
            if count:
                if self._debug:
                    stack_count = len(stack)
                self.matrix[pos, :] = self.matrix[:, pos] = keep
                unlink = np.flatnonzero(unlink)
                stack.update((pos, x // self.n) for x in unlink)
                stack.update((x, pos // self.n) for x in unlink)
                if self._debug:
                    stack_count = len(stack) - stack_count
                    print(f'{count} links removed, {stack_count} items added '
                          'to stack')
            elif self._debug:
                print('Nothing to remove, no change in stack')
                
            return count

        # sets are ordered in py > 3.6, which makes this even nicer
        stack = set(stack)
        count = 0

        if self._debug:
            print('    Assessing implications with initial stack of '
                  f'{len(stack)} items')

        while stack:
            pos, cat = stack.pop()
            p = cat * self.n
            # select connected rows
            rows = self.matrix[p:p + self.n, :]
            connection_mask = rows[:, pos]
            rows = rows[connection_mask, :]
            # find connections in rows
            update = np.logical_or.reduce(rows, axis=0)
            keep = self.matrix[pos] & update

            if self._debug:
                print(f'        {self.pos_to_item(pos)} -> '
                      f'{self.categories[cat]!r} ({len(rows)} links): ',
                      end='')

            count += check(keep, pos)
            if len(rows) == 1:
                # there is a possibility of two way unlinking
                pos2 = p + np.argmax(connection_mask)
                if self._debug:
                    print(f'        [Reverse] {self.pos_to_item(pos2)} -> '
                          f'{self.categories[pos // self.n]!r} '
                          f'({len(rows)} links): ', end='')
                count += check(keep, pos2)

        if self._debug:
            print()

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
        links : set
            All links between `pos` and `cat`, as positions similar to
            `pos`.
        """
        start = cat * self.n
        end = start + self.n
        return set(np.flatnonzero(self.matrix[pos, start:end]) + start)

    def _set_link(self, pos1, pos2, value):
        """
        Create or destroy a link between two items, regardless of
        category or position.

        This method facilitates symmetry. It does no error checking
        whatsoever!
        """
        self.matrix[pos1, pos2] = self.matrix[pos2, pos1] = value

    def _set_swath(self, pos, start, size, value):
        """
        Create or destroy a contiguous set of links to `pos`.

        The first `size` elements starting at `start` are linked to
        `pos`. This method facilitates symmetry. It does no error
        checking whatsoever!
        """
        end = start + size
        self.matrix[pos, start:end] = self.matrix[start:end, pos] = value
