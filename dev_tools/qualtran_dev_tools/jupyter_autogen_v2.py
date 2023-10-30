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

"""Autogeneration of Jupyter notebooks."""
import abc
import inspect
import textwrap
from types import ModuleType
from typing import List, Optional

import nbformat
from attrs import frozen

from qualtran import BloqDocSpec, BloqExample

from .jupyter_autogen import (
    _code_nbnode,
    _get_title_lines,
    _IMPORTS,
    _init_notebook,
    _K_CQ_AUTOGEN,
    _md_nbnode,
    get_markdown_docstring_lines,
)


@frozen(kw_only=True)
class NotebookSpecV2:
    """Specification for rendering a jupyter notebook for a given module.

    Attributes:
        title: The title of the notebook
        module: The module it documents. This is used to render the module docstring
            at the top of the notebook.
        bloq_specs: A list of gate or bloq specs.
    """

    title: str
    module: ModuleType
    bloq_specs: List[BloqDocSpec]
    directory: str = '.'
    _path_stem: Optional[str] = None

    @property
    def path_stem(self):
        if self._path_stem is None:
            return self.module.__name__.split('.')[-1]
        return self._path_stem


def _get_bloq_example_source_lines(bloq_ex: 'BloqExample') -> List[str]:
    """Parse out the source code from a factory function, so we can render it into a cell.

    Args:
        func: The factory function. Its definition must be one line; its body must be
            indented with four spaces; and it must end with a top-level return statement that
            is one line.

    Returns:
        trimmed_lines: The un-indented body of the function without the return statement.
        obj_expression: The expression used in the terminal `return` statement.
    """
    lines = textwrap.dedent(inspect.getsource(bloq_ex._func)).splitlines()

    if lines[0].startswith('@bloq_example'):
        lines = lines[1:]

    if not lines[0].startswith('def '):
        raise ValueError(
            f"The first line of {bloq_ex} doesn't look like a function definition: {lines[0]}"
        )

    trimmed_lines = []
    for line in lines[1:]:
        if not (line == '' or line.startswith(' ' * 4)):
            raise ValueError(f"Bad indentation in {bloq_ex}: {line}")

        trimmed_line = line[4:]
        if trimmed_line.startswith('return '):
            break
        trimmed_lines.append(line[4:])

    return trimmed_lines


class _Cell(metaclass=abc.ABCMeta):
    """Base class for a jupyter notebook cell with our metadata."""

    @property
    @abc.abstractmethod
    def cell_id(self) -> str:
        """A notebook-unique identifier for this cell.

        This is so we can identify and replace autogenerated content.
        """


@frozen
class _MarkdownCell(_Cell):
    """A jupyter notebook cell containing markdown."""

    text: str
    cell_id: str


@frozen
class _PyCell(_Cell):
    """A jupyter notebook cell containing python code."""

    text: str
    cell_id: str


def get_bloq_doc_cells(bloqdoc: BloqDocSpec, cid_prefix: str) -> List[_MarkdownCell]:
    """Cells introducing the `bloq_cls`"""

    md_doc: str = '\n'.join(get_markdown_docstring_lines(bloqdoc.bloq_cls))
    py_import: str = bloqdoc.import_line

    return [
        _MarkdownCell(text=md_doc, cell_id=f'{cid_prefix}.bloq_doc.md'),
        _PyCell(text=py_import, cell_id=f'{cid_prefix}.bloq_doc.py'),
    ]


def _get_one_ex_instance_cell(bloq_ex: 'BloqExample', cid_prefix):
    """Code cell for one example instance."""
    return _PyCell(
        text='\n'.join(_get_bloq_example_source_lines(bloq_ex)),
        cell_id=f'{cid_prefix}.{bloq_ex.name}',
    )


def get_example_instances_cells(bloqdoc: BloqDocSpec, cid_prefix: str) -> List[_Cell]:
    """Cells constructing example instances of the bloq class."""
    examples = bloqdoc.examples
    if not examples:
        return []

    cells: List[_Cell] = [
        _MarkdownCell('### Example Instances', cell_id=f'{cid_prefix}.example_instances.md')
    ]
    return cells + [_get_one_ex_instance_cell(ex, cid_prefix) for ex in examples]


def get_graphical_signature_cells(bloqdoc: BloqDocSpec, cid_prefix: str) -> List[_Cell]:
    """Cells showing a 'graphical signature' for the bloq examples."""
    if not bloqdoc.examples:
        return []

    varnames = [f'{ex.name}' for ex in bloqdoc.examples]
    comma_varnames = ', '.join(varnames)
    comma_str_varnames = ', '.join(f"'`{vn}`'" for vn in varnames)
    newline = '\n' + (' ' * len('show_bloqs('))
    code = 'from qualtran.drawing import show_bloqs\n'
    code += f'show_bloqs([{comma_varnames}],{newline}[{comma_str_varnames}])'
    return [
        _MarkdownCell(
            text='#### Graphical Signature', cell_id=f'{cid_prefix}.graphical_signature.md'
        ),
        _PyCell(text=code, cell_id=f'{cid_prefix}.graphical_signature.py'),
    ]


def get_cells(bloqdoc: BloqDocSpec) -> List[_Cell]:
    cells = []
    cid_prefix = f'{bloqdoc.bloq_cls.__name__}'
    cells += get_bloq_doc_cells(bloqdoc, cid_prefix)
    cells += get_example_instances_cells(bloqdoc, cid_prefix)
    cells += get_graphical_signature_cells(bloqdoc, cid_prefix)
    return cells


def _cell_to_nbnode(cell: _Cell) -> nbformat.NotebookNode:
    """Turn our typed `_Cell` into a `nbformat.NotebookNode` cell."""
    if isinstance(cell, _MarkdownCell):
        return _md_nbnode(cell.text, cell.cell_id)
    elif isinstance(cell, _PyCell):
        return _code_nbnode(cell.text, cell.cell_id)
    else:
        raise ValueError()


def render_notebook(nbspec: NotebookSpecV2) -> None:
    # 1. get a notebook (existing or empty)
    nb, nb_path = _init_notebook(path_stem=nbspec.path_stem, directory=nbspec.directory)

    # 2. Render all the cells we can render
    cells = {
        'title_cell': _MarkdownCell(
            '\n'.join(_get_title_lines(nbspec.title, nbspec.module)), cell_id='title_cell'
        ),
        'top_imports': _PyCell(_IMPORTS, cell_id='top_imports'),
    }
    for bds in nbspec.bloq_specs:
        cells |= {c.cell_id: c for c in get_cells(bds)}

    # 3. Merge rendered cells into the existing notebook.
    #     -> we use the cells metadata field to match up cells.
    cqids_to_render: List[str] = list(cells.keys())
    for i in range(len(nb.cells)):
        nb_node = nb.cells[i]
        if _K_CQ_AUTOGEN in nb_node.metadata:
            cqid: str = nb_node.metadata[_K_CQ_AUTOGEN]
            new_cell = cells.get(cqid, None)
            if new_cell is None:
                print(f'[{nbspec.path_stem}] Superfluous {cqid} cell.')
                continue
            print(f"[{nbspec.path_stem}] Replacing {cqid} cell.")
            new_nbnode = _cell_to_nbnode(new_cell)
            new_nbnode.id = nb_node.id  # keep id from existing cell
            nb.cells[i] = new_nbnode
            cqids_to_render.remove(cqid)

    # 4. Any rendered cells that weren't already there, append.
    for cqid in cqids_to_render:
        print(f"[{nbspec.path_stem}] Adding {cqid}")
        new_cell = cells[cqid]
        new_nbnode = _cell_to_nbnode(new_cell)
        nb.cells.append(new_nbnode)

    # 5. Write the notebook.
    with nb_path.open('w') as f:
        nbformat.write(nb, f)
