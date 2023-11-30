#  Copyright 2023 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Autogeneration of Jupyter notebooks.

For each module listed in the `NOTEBOOK_SPECS` global variable (in this file)
we write a notebook with a title, module docstring,
standard imports, and information on each bloq listed in the
`bloq_specs` field. For each gate, we render a docstring and diagrams.

## Adding a new gate.

 1. Create a new function that takes no arguments
    and returns an instance of the desired gate.
 2. If this is a new module: add a new key/value pair to the NOTEBOOK_SPECS global variable
    in this file. The key should be the name of the module with a `NotebookSpec` value. See
    the docstring for `NotebookSpec` for more information.
 3. Update the `NotebookSpec` `bloq_specs` field to include a `BloqNbSpec` for your new gate.
    Provide your factory function from step (1).

## Autogen behavior.

Each autogenerated notebook cell is tagged, so we know it was autogenerated. Each time
this script is re-run, these cells will be re-rendered. *Modifications to generated _cells_
will not be persisted*.

If you add additional cells to the notebook it will *preserve them* even when this script is
re-run

Usage as a script:
    python dev_tools/autogenerate-bloqs-notebooks.py
"""

from typing import List

from qualtran_dev_tools.git_tools import get_git_root
from qualtran_dev_tools.jupyter_autogen_v2 import NotebookSpecV2, render_notebook

import qualtran.bloqs.and_bloq
import qualtran.bloqs.apply_gate_to_lth_target
import qualtran.bloqs.basic_gates.swap
import qualtran.bloqs.chemistry.df.double_factorization
import qualtran.bloqs.chemistry.pbc.first_quantization.projectile.select_and_prepare
import qualtran.bloqs.chemistry.sparse.prepare
import qualtran.bloqs.chemistry.sparse.select
import qualtran.bloqs.factoring.mod_exp
import qualtran.bloqs.prepare_uniform_superposition
import qualtran.bloqs.sorting
import qualtran.bloqs.swap_network

SOURCE_DIR = get_git_root() / 'qualtran/'


NOTEBOOK_SPECS: List[NotebookSpecV2] = [
    NotebookSpecV2(
        title='Swap Network',
        module=qualtran.bloqs.swap_network,
        bloq_specs=[
            qualtran.bloqs.basic_gates.swap._CSWAP_DOC,
            qualtran.bloqs.swap_network._APPROX_CSWAP_DOC,
            qualtran.bloqs.swap_network._SWZ_DOC,
            qualtran.bloqs.swap_network._MULTIPLEXED_CSWAP_DOC,
        ],
        directory=f'{SOURCE_DIR}/bloqs',
        path_stem='swap_network_2',
    ),
    NotebookSpecV2(
        title='Modular Exponentiation',
        module=qualtran.bloqs.factoring.mod_exp,
        bloq_specs=[qualtran.bloqs.factoring.mod_exp._MODEXP_DOC],
        directory=f'{SOURCE_DIR}/bloqs/factoring',
    ),
    NotebookSpecV2(
        title='Modular Multiplication',
        module=qualtran.bloqs.factoring.mod_mul,
        bloq_specs=[qualtran.bloqs.factoring.mod_mul._MODMUL_DOC],
        directory=f'{SOURCE_DIR}/bloqs/factoring',
    ),
    NotebookSpecV2(
        title='Prepare Uniform Superposition',
        module=qualtran.bloqs.prepare_uniform_superposition,
        bloq_specs=[qualtran.bloqs.prepare_uniform_superposition._PREP_UNIFORM_DOC],
        directory=f'{SOURCE_DIR}/bloqs/',
    ),
    NotebookSpecV2(
        title='Apply to Lth Target',
        module=qualtran.bloqs.apply_gate_to_lth_target,
        bloq_specs=[qualtran.bloqs.apply_gate_to_lth_target._APPLYLTH_DOC],
        directory=f'{SOURCE_DIR}/bloqs/',
    ),
    NotebookSpecV2(
        title='First Quantized Hamiltonian with Quantum Projectile',
        module=qualtran.bloqs.chemistry.pbc.first_quantization.projectile,
        bloq_specs=[
            qualtran.bloqs.chemistry.pbc.first_quantization.projectile.select_and_prepare._FIRST_QUANTIZED_WITH_PROJ_PREPARE_DOC,
            qualtran.bloqs.chemistry.pbc.first_quantization.projectile.select_and_prepare._FIRST_QUANTIZED_WITH_PROJ_SELECT_DOC,
        ],
        directory=f'{SOURCE_DIR}/bloqs/chemistry/pbc/first_quantization/projectile',
    ),
    NotebookSpecV2(
        title='Sorting',
        module=qualtran.bloqs.sorting,
        bloq_specs=[
            qualtran.bloqs.sorting._COMPARATOR_DOC,
            qualtran.bloqs.sorting._BITONIC_SORT_DOC,
        ],
        directory=f'{SOURCE_DIR}/bloqs/',
    ),
    NotebookSpecV2(
        title='Double Factorization',
        module=qualtran.bloqs.chemistry.df.double_factorization,
        bloq_specs=[
            qualtran.bloqs.chemistry.df.double_factorization._DF_ONE_BODY,
            qualtran.bloqs.chemistry.df.double_factorization._DF_BLOCK_ENCODING,
        ],
        directory=f'{SOURCE_DIR}/bloqs/chemistry/df',
    ),
    NotebookSpecV2(
        title='Sparse',
        module=qualtran.bloqs.chemistry.sparse,
        bloq_specs=[
            qualtran.bloqs.chemistry.sparse.prepare._SPARSE_PREPARE,
            qualtran.bloqs.chemistry.sparse.select._SPARSE_SELECT,
        ],
        directory=f'{SOURCE_DIR}/bloqs/chemistry/sparse',
    ),
    NotebookSpecV2(
        title='And',
        module=qualtran.bloqs.and_bloq,
        bloq_specs=[qualtran.bloqs.and_bloq._AND_DOC, qualtran.bloqs.and_bloq._MULTI_AND_DOC],
        directory=f'{SOURCE_DIR}/bloqs/',
    ),
]


def render_notebooks():
    for nbspec in NOTEBOOK_SPECS:
        render_notebook(nbspec)


if __name__ == '__main__':
    render_notebooks()
