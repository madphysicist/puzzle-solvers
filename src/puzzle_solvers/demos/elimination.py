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
This is a demo of the :py:mod:`puzzle_solvers.elimination` module. It is
documented in detail in the corresponding :ref:`elimination-tutorial`
section.
"""

from ..elimination import Solver


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


solver = Solver(problem) #, debug=True)

if __name__ == '__main__':
    """
    Run the tutorial example. This block is purposely not placed in a
    function. Running the script in IPython will leave the variables in
    the user workspace for additional experimentation.
    """

    print(solver.edges)
    solver.draw(show=False, title='Initial State')

    solver.match('Dana', 'XL')

    solver.match(2, 'yellow')
    solver.unlink('T-Shirt', 'red')

    solver.match('Sören', 'Sweatshirt')
    solver.match('Ingo', 'L')
    solver.match(positions[-1], 30)
    solver.match(ages[-1], sizes[0])
    solver.match('red', *sizes[2:])

    solver.match(ages[0], 'yellow')
    solver.match('Jessica', 'Blouse')
    solver.match(3, 'M')
    solver.match('Poloshirt', 'red', 'yellow', 'green')

    print(solver.edges)
    solver.draw(show=False, title='After Explicit Rules')

    solver.unlink('Sören', 1)
    solver.unlink('Sören', 5)

    youngest = solver.category_for(ages[0], 'position')
    if youngest is not None:
        solver.unlink('Sören', youngest + 1)
    oldest = solver.category_for(ages[-1], 'position')
    if oldest is not None:
        solver.unlink('Sören', oldest - 1)

    count = 1
    while count:
        count = solver.less_than('Dana', 'black', 'position', 2, None)
        count += solver.less_than('Jessica', 'Poloshirt', 'position', 1)
        count += solver.less_than('Valerie', 'red', 'position', 1)

    print(solver.edges)
    solver.draw(show=False, title='After Some Implicit Rules')

    pos = solver.category_for('Sören', 'position')
    ages = solver.find_missing('age')
    solver.match(pos - 1, max(ages))
    solver.match(pos + 1, min(ages))

    print(solver.edges)
    solver.draw(show=True, title='Final Answer')

    print(solver.solved)
