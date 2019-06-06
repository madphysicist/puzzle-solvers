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
This is an additional demo of the :py:mod:`puzzle_solvers.elimination`
module. It showcases a solution to the original zebra-puzzle, mentioned
in the :ref:`elimination-api` reference.
"""

from ..elimination import Solver


positions = [1, 2, 3, 4, 5]
nationalities = [
    'Englishman', 'Spaniard', 'Ukrainian', 'Norwegian', 'Japanese'
]
colors = ['red', 'green', 'ivory', 'yellow', 'blue']
pets = ['dog', 'snails', 'fox', 'horse', 'ZEBRA']
drinks = ['coffee', 'tea', 'milk', 'orange juice', 'WATER']
cigarettes = [
    'Old Gold', 'Kools', 'Chesterfields', 'Lucky Strikes', 'Parliaments'
]

problem = {
    'position': positions,
    'nationality': nationalities,
    'color': colors,
    'pet': pets,
    'drink': drinks,
    'cigarette': cigarettes,
}


solver = Solver(problem)


if __name__ == '__main__':
    solver.match('Englishman', 'red')
    solver.match('Spaniard', 'dog')
    solver.match('coffee', 'green')
    solver.match('Ukrainian', 'tea')
    solver.greater_than('green', 'ivory', 'position', 1)
    solver.match('Old Gold', 'snails')
    solver.match('Kools', 'yellow')
    solver.match('milk', 3)
    solver.match('Norwegian', 1)
    solver.adjacent_to('Chesterfields', 'fox', 'position')
    solver.adjacent_to('Kools', 'horse', 'position')
    solver.match('Lucky Strikes', 'orange juice')
    solver.match('Japanese', 'Parliaments')
    solver.adjacent_to('Norwegian', 'blue', 'position')

    solver.draw(show=False, title=f'After Rules: {solver.edges} Edges')

    print(f'Solved? {solver.solved}')
    print(f'{solver.category_for("ZEBRA", "nationality")} owns the ZEBRA')
    print(f'{solver.category_for("WATER", "nationality")} drinks WATER')
