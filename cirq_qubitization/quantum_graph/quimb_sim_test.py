from functools import cached_property
from typing import Dict

import cirq
import numpy as np
import pytest
import quimb.tensor as qtn
from attrs import frozen
from numpy.typing import NDArray

from cirq_qubitization.bloq_algos.basic_gates import XGate
from cirq_qubitization.quantum_graph.bloq import Bloq
from cirq_qubitization.quantum_graph.composite_bloq import CompositeBloqBuilder, SoquetT
from cirq_qubitization.quantum_graph.fancy_registers import FancyRegister, FancyRegisters, Side
from cirq_qubitization.quantum_graph.quantum_graph import DanglingT, RightDangle, Soquet
from cirq_qubitization.quantum_graph.quimb_sim import (
    _bloq_defines_add_my_tensors,
    _get_dangling_soquets,
    cbloq_to_quimb,
    get_right_and_left_inds,
)
from cirq_qubitization.quantum_graph.util_bloqs import Join


def test_get_soquets():
    soqs = _get_dangling_soquets(Join(10).registers, right=True)
    assert list(soqs.keys()) == ['join']
    soq = soqs['join']
    assert soq.binst == RightDangle
    assert soq.reg.bitsize == 10

    soqs = _get_dangling_soquets(Join(10).registers, right=False)
    assert list(soqs.keys()) == ['join']
    soq = soqs['join']
    assert soq.shape == (10,)
    assert soq[0].reg.bitsize == 1


@frozen
class TensorAdderTester(Bloq):
    @cached_property
    def registers(self) -> 'FancyRegisters':
        return FancyRegisters(
            [
                FancyRegister('x', bitsize=2, side=Side.LEFT),
                FancyRegister('qubits', bitsize=1, wireshape=(2,)),
                FancyRegister('y', bitsize=1, side=Side.RIGHT),
            ]
        )

    def add_my_tensors(
        self,
        tn: qtn.TensorNetwork,
        tag,
        *,
        incoming: Dict[str, SoquetT],
        outgoing: Dict[str, SoquetT],
    ):
        assert sorted(incoming.keys()) == ['qubits', 'x']
        in_qubits = incoming['qubits']
        assert in_qubits.shape == (2,)
        assert incoming['x'].reg.bitsize == 2

        assert sorted(outgoing.keys()) == ['qubits', 'y']
        out_qubits = outgoing['qubits']
        assert out_qubits.shape == (2,)
        assert outgoing['y'].reg.bitsize == 1

        data = np.zeros((2**2, 2, 2, 2, 2, 2))
        data[3, 0, 1, 0, 1, 0] = 1
        tn.add(
            qtn.Tensor(
                data=data,
                inds=(
                    incoming['x'],
                    in_qubits[0],
                    in_qubits[1],
                    outgoing['y'],
                    out_qubits[0],
                    out_qubits[1],
                ),
                tags=[tag],
            )
        )


def _old_bloq_to_dense(bloq: Bloq) -> NDArray:
    """Old code for tensor-contracting a bloq without wrapping it in length-1 composite bloq."""
    tn = qtn.TensorNetwork([])
    lsoqs = _get_dangling_soquets(bloq.registers, right=False)
    rsoqs = _get_dangling_soquets(bloq.registers, right=True)
    bloq.add_my_tensors(tn, None, incoming=lsoqs, outgoing=rsoqs)

    inds = get_right_and_left_inds(bloq.registers)
    matrix = tn.to_dense(*inds)
    return matrix


def test_bloq_to_dense():
    mat1 = _old_bloq_to_dense(TensorAdderTester())
    mat2 = TensorAdderTester().tensor_contract()
    np.testing.assert_allclose(mat1, mat2, atol=1e-8)

    # Right inds: qubits=(1,0), y=0
    right = 1 * 2**2 + 0 * 2**1 + 0 * 2**0

    # Left inds: x=3, qubits=(0,1)
    left = 3 * 2**2 + 0 * 2**1 + 1 * 2**0

    assert np.where(mat2) == (right, left)


@frozen
class TensorAdderSimple(Bloq):
    @cached_property
    def registers(self) -> 'FancyRegisters':
        return FancyRegisters.build(x=1)

    def add_my_tensors(
        self,
        tn: qtn.TensorNetwork,
        tag,
        *,
        incoming: Dict[str, SoquetT],
        outgoing: Dict[str, SoquetT],
    ):
        assert list(incoming.keys()) == ['x']
        assert list(outgoing.keys()) == ['x']
        tn.add(qtn.Tensor(data=np.eye(2), inds=(incoming['x'], outgoing['x']), tags=[tag]))


def test_cbloq_to_quimb():
    bb = CompositeBloqBuilder()
    x = bb.add_register('x', 1)
    (x,) = bb.add(TensorAdderSimple(), x=x)
    (x,) = bb.add(TensorAdderSimple(), x=x)
    (x,) = bb.add(TensorAdderSimple(), x=x)
    (x,) = bb.add(TensorAdderSimple(), x=x)
    cbloq = bb.finalize(x=x)

    tn, _ = cbloq_to_quimb(cbloq)
    assert len(tn.tensors) == 4
    for oi in tn.outer_inds():
        assert isinstance(oi, Soquet)
        assert isinstance(oi.binst, DanglingT)


@frozen
class XNest(Bloq):
    @cached_property
    def registers(self) -> 'FancyRegisters':
        return FancyRegisters.build(r=1)

    def build_composite_bloq(
        self, bb: 'CompositeBloqBuilder', r: 'SoquetT'
    ) -> Dict[str, 'SoquetT']:
        (r,) = bb.add(XGate(), q=r)
        return {'r': r}


@frozen
class XDoubleNest(Bloq):
    @cached_property
    def registers(self) -> 'FancyRegisters':
        return FancyRegisters.build(s=1)

    def build_composite_bloq(
        self, bb: 'CompositeBloqBuilder', s: 'SoquetT'
    ) -> Dict[str, 'SoquetT']:
        (s,) = bb.add(XNest(), r=s)
        return {'s': s}


def test_nest():
    x = XNest()
    should_be = cirq.unitary(cirq.X)
    np.testing.assert_allclose(should_be, x.tensor_contract())
    np.testing.assert_allclose(should_be, x.decompose_bloq().tensor_contract())


def test_bloq_defines_add_my_tensors():
    assert not _bloq_defines_add_my_tensors(XNest())
    assert not _bloq_defines_add_my_tensors(XDoubleNest())
    assert not _bloq_defines_add_my_tensors(XNest().decompose_bloq())
    assert not _bloq_defines_add_my_tensors(XDoubleNest().decompose_bloq())
    assert _bloq_defines_add_my_tensors(TensorAdderSimple())
    assert _bloq_defines_add_my_tensors(XGate())

    with pytest.raises(NotImplementedError):
        XNest().add_my_tensors(qtn.TensorNetwork([]), None, incoming={}, outgoing={})


def test_double_nest():
    xx = XDoubleNest()
    should_be = cirq.unitary(cirq.X)
    np.testing.assert_allclose(should_be, xx.tensor_contract())
    np.testing.assert_allclose(should_be, xx.decompose_bloq().tensor_contract())

    with pytest.raises(AttributeError, match=r".*has no attribute 'iter_bloqnections'"):
        cbloq_to_quimb(xx)

    with pytest.raises(NotImplementedError):
        cbloq_to_quimb(xx.decompose_bloq())
