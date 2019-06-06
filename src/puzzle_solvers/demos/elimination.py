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

    print(f'Initial State: {solver.edges} Edges')
    solver.draw(show=False, title=f'Initial State: {solver.edges} Edges')

    # 1. The top Dana wants to buy is size XL.
    solver.match('Dana', 'XL')
    # 1a. She is ahead of (but not directly ahead) of someone who wants to buy
    # a black top.
    solver.less_than('Dana', 'black', 'position', 2, None)
    # 2. Jessica waits directly in front of a person who wants to buy a
    # Poloshirt.
    solver.less_than('Jessica', 'Poloshirt', 'position', 1)
    # 3. The second person in line wants to buy a yellow top.
    solver.match(2, 'yellow')
    # 4. The T-shirt isn't red.
    solver.unmatch('T-Shirt', 'red')
    # 5. Sören wants to buy a Sweatshirt.
    solver.match('Sören', 'Sweatshirt')
    # 6. Ingo needs a size L top.
    solver.match('Ingo', 'L')
    # 7. The last person in line is 30 years old.
    solver.match(positions[-1], 30)
    # 8. The oldest person is going to buy the top with the smallest size.
    solver.match(ages[-1], sizes[0])
    # 9. The person who waits directly behind Valerie wants to buy a red top.
    solver.less_than('Valerie', 'red', 'position', 1)
    # 9a. The red top is bigger than size S.
    solver.match('red', *sizes[sizes.index('S') + 1:])
    # 10. The youngest person wants to buy a yellow top.
    solver.match(ages[0], 'yellow')
    # 11. Jessica is going to buy a Blouse.
    solver.match('Jessica', 'Blouse')
    # 12. The third person in line wants to buy a size M top.
    solver.match(3, 'M')
    # 13. The Poloshirt is either red or yellow or green.
    solver.match('Poloshirt', 'red', 'yellow', 'green')

    print(f'After Most Rules: {solver.edges} Edges, '
          f'{solver.assertion_count} Assertions')
    solver.draw(show=False, title=f'After Most Rules: {solver.edges} Edges')


    # 5a. The person who waits directly in front of ['Sören'] is older than the
    #     one behind him.

    # Corrolary: Sören can not be first or last in line
    solver.unmatch('Sören', positions[0])
    solver.unmatch('Sören', positions[-1])

    # Corrolary: the person immediately in front of Sören can not be the
    #     youngest
    youngest = solver.category_for(ages[0], 'position')
    if youngest is not None:
        solver.unmatch('Sören', youngest + 1)

    # Corrolary: the person immediately behind Sören can not be the oldest
    oldest = solver.category_for(ages[-1], 'position')
    if oldest is not None:
        solver.unmatch('Sören', oldest - 1)

    print(f'After Preprocessing 5a: {solver.edges} Edges, '
          f'{solver.assertion_count} Assertions')
    solver.draw(show=False,
                title=f'After Preprocessing 5a: {solver.edges} Edges')

    pos = solver.category_for('Sören', 'position')

    print(f'Found position: {pos}')

    ages = solver.find_missing('age')
    solver.match(pos - 1, max(ages))
    solver.match(pos + 1, min(ages))

    print(f'Final Answer: {solver.edges} Edges')
    solver.draw(show=True, title=f'Final Answer: {solver.edges} Edges')

    print(solver.solved)
