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
r"""Bloqs for preparation of the U and V parts of the first quantized chemistry Hamiltonian."""
from functools import cached_property
from typing import Optional, Set, Tuple, TYPE_CHECKING

from attrs import frozen

from qualtran import Bloq, Register, Signature
from qualtran.bloqs.arithmetic import GreaterThan, Product, SumOfSquares
from qualtran.bloqs.basic_gates import Toffoli

if TYPE_CHECKING:
    from qualtran.resource_counting import SympySymbolAllocator


@frozen
class PrepareMuUnaryEncodedOneHot(Bloq):
    r"""Prepare a unary encoded one-hot superposition state over the $\mu$ register for nested boxes

    Prepares the state in Eq. 77

    $$
        \frac{1}{\sqrt{2^{n_p + 2}}} \sum_{\mu=2}^{n_p+1} \sqrt{2^\mu}
        |0\dots0\underbrace{1\dots1}{\mu}\rangle
    $$

    Args:
        num_bits_p: The number of bits to represent each dimension of the momentum register.

    Registers:
        mu: the register to prepare the superposition over.

    References:
        [Fault-Tolerant Quantum Simulations of Chemistry in First Quantization](
            https://arxiv.org/abs/2105.12767) page 21, Eq 77.
    """
    num_bits_p: int

    @cached_property
    def signature(self) -> Signature:
        return Signature.build(mu=self.num_bits_p)

    def bloq_counts(self, ssa: Optional['SympySymbolAllocator'] = None) -> Set[Tuple[int, Bloq]]:
        # controlled hadamards which cannot be inverted at zero Toffoli cost.
        return {((self.num_bits_p - 1), Toffoli())}


@frozen
class PrepareNuSuperPositionState(Bloq):
    r"""Prepare the superposition over $\nu$ following the creation of the $|\mu\rangle$ state.

    Prepares the state in Eq. 78

    $$
        \frac{1}{\sqrt{2^{n_p + 2}}} \sum_{\mu=2}^{n_p+1}
        \sum_{\nu_{x,y,z}=-(2^{\mu-1}-1)}^{2^{\mu-1}-1}
        \frac{1}{2\mu}
        |\mu\rangle|\nu_x\rangle|\nu_y\rangle|\nu_z\rangle
    $$

    Args:
        num_bits_p: The number of bits to represent each dimension of the momentum register.

    Registers:
        mu: the register one-hot encoded $\mu$ register from eq 77.
        nu: the momentum transfer register.

    References:
        [Fault-Tolerant Quantum Simulations of Chemistry in First Quantization](
            https://arxiv.org/abs/2105.12767) page 21, Eq 78.
    """
    num_bits_p: int

    @cached_property
    def signature(self) -> Signature:
        return Signature(
            [Register("mu", self.num_bits_p), Register("nu", self.num_bits_p + 1, shape=(3,))]
        )

    def bloq_counts(self, ssa: Optional['SympySymbolAllocator'] = None) -> Set[Tuple[int, Bloq]]:
        # controlled hadamards which cannot be inverted at zero Toffoli cost.
        return {((3 * (self.num_bits_p - 1)), Toffoli())}


@frozen
class FlagZeroAsFailure(Bloq):
    r"""Bloq to flag if minus zero appears in the $\nu$ state.

    Args:
        num_bits_p: The number of bits to represent each dimension of the momentum register.

    Registers:
        nu: the momentum transfer register.
        flag_minus_zero: a flag bit for failure of the state preparation.

    References:
        [Fault-Tolerant Quantum Simulations of Chemistry in First Quantization](
            https://arxiv.org/abs/2105.12767) page 21, Eq 80.
    """
    num_bits_p: int
    adjoint: bool = False

    @cached_property
    def signature(self) -> Signature:
        return Signature(
            [Register("nu", self.num_bits_p + 1, shape=(3,)), Register("flag_minus_zero", 1)]
        )

    def bloq_counts(self, ssa: Optional['SympySymbolAllocator'] = None) -> Set[Tuple[int, Bloq]]:
        if self.adjoint:
            # This can be inverted with cliffords.
            return {(0, Toffoli())}
        else:
            # Controlled Toffoli each having n_p + 1 controls and 2 Toffolis to
            # check the result of the Toffolis.
            return {((3 * self.num_bits_p + 2), Toffoli())}


@frozen
class TestNuLessThanMu(Bloq):
    r"""Bloq to flag if all components of $\nu$ are smaller in absolute value than $2^{\mu-2}$.

    Args:
        num_bits_p: The number of bits to represent each dimension of the momentum register.

    Registers:
        nu: the momentum transfer register.
        flag_nu_lt_mu: a flag bit for failure of the state preparation.

    References:
        [Fault-Tolerant Quantum Simulations of Chemistry in First Quantization](
            https://arxiv.org/abs/2105.12767) page 21, Eq 80.
    """
    num_bits_p: int
    adjoint: bool = False

    @cached_property
    def signature(self) -> Signature:
        return Signature(
            [
                Register("mu", self.num_bits_p),
                Register("nu", self.num_bits_p + 1, shape=(3,)),
                Register("flag_nu_lt_mu", 1),
            ]
        )

    def bloq_counts(self, ssa: Optional['SympySymbolAllocator'] = None) -> Set[Tuple[int, Bloq]]:
        if self.adjoint:
            # This can be inverted with cliffords.
            return {(0, Toffoli())}
        else:
            # n_p controlled Toffolis with four controls.
            return {(3 * self.num_bits_p, Toffoli())}


@frozen
class TestNuInequality(Bloq):
    r"""Bloq to flag if all components of $\nu$ are smaller in absolute value than $2^{\mu-2}$.

    Test

    $$
        (2^{\mu-2})^2 \mathcal{M} > m (\nu_x^2 + \nu_y^2 + \nu_z^2)
    $$

    where $m \in [0, \mathcal{M}-1]$ and is store in an ancilla register.

    Args:
        num_bits_p: The number of bits to represent each dimension of the momentum register.
        num_bits_m: The number of bits for $\mathcal{M}$. Eq 86.
        adjoint: Whether to dagger the bloq or not.

    Registers:
        mu: the one-hot unary superposition register.
        nu: the momentum transfer register.
        m: the ancilla register in unfiform superposition.
        flag_minus_zero: A flag from checking for negative zero.
        flag_nu_lt_mu: A flag from checking $\nu \lt 2^{\mu -2}$.
        flag_ineq: A flag qubit from the inequality test.
        succ: a flag bit for failure of the state preparation.

    References:
        [Fault-Tolerant Quantum Simulations of Chemistry in First Quantization](
            https://arxiv.org/abs/2105.12767) page 21, Eq 80.
    """
    num_bits_p: int
    num_bits_m: int
    adjoint: bool = False

    @cached_property
    def signature(self) -> Signature:
        return Signature(
            [
                Register("mu", self.num_bits_p),
                Register("nu", self.num_bits_p + 1, shape=(3,)),
                Register("m", self.num_bits_m),
                Register("flag_minus_zero", 1),
                Register("flag_nu_lt_mu", 1),
                Register("flag_ineq", 1),
                Register("succ", 1),
            ]
        )

    def bloq_counts(self, ssa: Optional['SympySymbolAllocator'] = None) -> Set[Tuple[int, Bloq]]:
        if self.adjoint:
            return {(0, Toffoli())}
        else:
            # 1. Compute $\nu_x^2 + \nu_y^2 + \nu_z^2$
            cost_1 = (1, SumOfSquares(self.num_bits_p, k=3))
            # 2. Compute $m (\nu_x^2 + \nu_y^2 + \nu_z^2)$
            cost_2 = (1, Product(2 * self.num_bits_p + 2, self.num_bits_m))
            # 3. Inequality test
            cost_3 = (1, GreaterThan(self.num_bits_m, 2 * self.num_bits_p + 2))
            # 4. 3 Toffoli for overall success
            cost_4 = (3, Toffoli())
            return {cost_1, cost_2, cost_3, cost_4}


@frozen
class PrepareNuState(Bloq):
    r"""PREPARE for the $\nu$ state for the $U$ and $V$ components of the Hamiltonian.

    Prepares a state of the form

    $$
        \frac{1}{\sqrt{\mathcal{M}2^{n_p + 2}}}
        \sum_{\mu=2}^{n_p+1}\sum_{\nu \in B_\mu}
        \sum_{m=0}^{\lceil \mathcal M(2^{\mu-2}/\lVert\nu\rVert)^2\rceil-1}
        \frac{1}{2^\mu}|\mu\rangle|\nu_x\rangle|\nu_y\rangle|\nu_z\rangle|m\rangle|0\rangle
    $$

    Args:
        num_bits_p: The number of bits to represent each dimension of the momentum register.
        m_param: $\mathcal{M}$ in the reference.
        lambda_zeta: sum of nuclear charges.
        er_lambda_zeta: eq 91 of the referce. Cost of erasing qrom.

    Registers:
        mu: The state controlling the nested boxes procedure.
        nu: The momentum transfer register.
        m: an ancilla register in a uniform superposition.
        flag_nu: Flag for success of the state preparation.

    References:
        [Fault-Tolerant Quantum Simulations of Chemistry in First Quantization](
            https://arxiv.org/abs/2105.12767) page 19, section B
    """
    num_bits_p: int
    m_param: int
    adjoint: bool = False

    @cached_property
    def signature(self) -> Signature:
        n_m = (self.m_param - 1).bit_length()
        return Signature(
            [
                Register("mu", bitsize=self.num_bits_p),
                Register("nu", bitsize=self.num_bits_p + 1, shape=(3,)),
                Register("m", bitsize=n_m),
                Register("flag_nu", bitsize=1),
            ]
        )

    def bloq_counts(self, ssa: Optional['SympySymbolAllocator'] = None) -> Set[Tuple[int, Bloq]]:
        # 1. Prepare unary encoded superposition state (Eq 77)
        cost_1 = (1, PrepareMuUnaryEncodedOneHot(self.num_bits_p))
        n_m = (self.m_param - 1).bit_length()
        # 2. Prepare mu-nu superposition (Eq 78)
        cost_2 = (1, PrepareNuSuperPositionState(self.num_bits_p))
        # 3. Remove minus zero
        cost_3 = (1, FlagZeroAsFailure(self.num_bits_p, adjoint=self.adjoint))
        # 4. Test $\nu < 2^{\mu-2}$
        cost_4 = (1, TestNuLessThanMu(self.num_bits_p, adjoint=self.adjoint))
        # 5. Prepare superposition over $m$ which is a power of two so only clifford.
        # 6. Test that $(2^{\mu-2})^2\mathcal{M} > m (\nu_x^2 + \nu_y^2 + \nu_z^2)$
        cost_6 = (1, TestNuInequality(self.num_bits_p, n_m, adjoint=self.adjoint))
        return {cost_1, cost_2, cost_3, cost_4, cost_6}
