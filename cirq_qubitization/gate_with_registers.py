import abc
import sys
import warnings
from typing import Sequence, Dict, Iterable, List, Union, overload, Tuple

import cirq
from attrs import frozen

assert sys.version_info > (3, 6), "https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep468"


class Register(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def name(self):
        ...

    @property
    @abc.abstractmethod
    def left_shape(self) -> Tuple[int, ...]:
        ...

    @property
    @abc.abstractmethod
    def right_shape(self) -> Tuple[int, ...]:
        ...


class IThruRegister(Register, metaclass=abc.ABCMeta):
    @property
    def left_shape(self) -> Tuple[int, ...]:
        return self.shape

    @property
    def right_shape(self) -> Tuple[int, ...]:
        return self.shape

    @property
    @abc.abstractmethod
    def shape(self) -> Tuple[int, ...]:
        ...


@frozen
class ThruRegister(IThruRegister):
    name: str
    bitsize: int

    @property
    def shape(self) -> Tuple[int, ...]:
        return (self.bitsize,)


class Registers:
    def __init__(self, registers: Iterable[Register]):
        self._registers = tuple(registers)
        self._register_dict = {r.name: r for r in self._registers}
        if len(self._registers) != len(self._register_dict):
            raise ValueError("Please provide unique register names.")

    def __repr__(self):
        return f'Registers({repr(self._registers)})'

    @property
    def bitsize(self) -> int:
        warnings.warn("Bitsize only works for `ThruRegister`s", DeprecationWarning)
        s = 0
        for reg in self:
            if not isinstance(reg, ThruRegister):
                raise ValueError(f"`Registers.bitsize` only works for `ThruRegister`s, not {reg}")
            s += reg.bitsize
        return s

    @classmethod
    def build(cls, **registers: int) -> 'Registers':
        return cls(ThruRegister(name=k, bitsize=v) for k, v in registers.items())

    @overload
    def __getitem__(self, key: int) -> Register:
        pass

    @overload
    def __getitem__(self, key: str) -> Register:
        pass

    @overload
    def __getitem__(self, key: slice) -> 'Registers':
        pass

    def __getitem__(self, key):
        if isinstance(key, slice):
            return Registers(self._registers[key])
        elif isinstance(key, int):
            return self._registers[key]
        elif isinstance(key, str):
            return self._register_dict[key]
        else:
            raise IndexError(f"key {key} must be of the type str/int/slice.")

    def __contains__(self, item: str) -> bool:
        return item in self._register_dict

    def __iter__(self):
        yield from self._registers

    def __len__(self) -> int:
        return len(self._registers)

    def _hack_bitsize(self, reg: Register):
        # FIXME: move to left and right shape
        if len(reg.left_shape) != 1:
            raise NotImplementedError("TODO")
        (bitsize,) = reg.left_shape
        return bitsize

    def split_qubits(self, qubits: Sequence[cirq.Qid]) -> Dict[str, Sequence[cirq.Qid]]:
        qubit_regs = {}
        base = 0
        for reg in self:
            bitsize = self._hack_bitsize(reg)
            qubit_regs[reg.name] = qubits[base : base + bitsize]
            base += bitsize
        return qubit_regs

    def split_integer(self, n: int) -> Dict[str, int]:
        """Extracts integer values of individual qubit registers, given a bit-packed integer.

        Considers the given integer as a binary bit-packed representation of `self.bitsize` bits,
        with `n_bin[0 : self[0].bitsize]` representing the integer for first register,
        `n_bin[self[0].bitsize : self[1].bitsize]` representing the integer for second
        register and so on. Here `n_bin` is the `self.bitsize` length binary representation of
        input integer `n`.
        """
        qubit_vals = {}
        base = 0
        n_bin = f"{n:0{self.total_size}b}"
        for reg in self:
            bitsize = self._hack_bitsize(reg)
            qubit_vals[reg.name] = int(n_bin[base : base + bitsize], 2)
            base += bitsize
        return qubit_vals

    def merge_qubits(self, **qubit_regs: Union[cirq.Qid, Sequence[cirq.Qid]]) -> List[cirq.Qid]:
        ret: List[cirq.Qid] = []
        for reg in self:
            bitsize = self._hack_bitsize(reg)
            assert reg.name in qubit_regs, "All qubit registers must pe present"
            qubits = qubit_regs[reg.name]
            qubits = [qubits] if isinstance(qubits, cirq.Qid) else qubits
            assert len(qubits) == bitsize, f"{reg.name} register must of length {bitsize}."
            ret += qubits
        return ret

    def get_named_qubits(self) -> Dict[str, List[cirq.Qid]]:
        def qubits_for_reg(name: str, bitsize: int):
            return (
                [cirq.NamedQubit(f"{name}")]
                if bitsize == 1
                else cirq.NamedQubit.range(bitsize, prefix=name)
            )

        return {reg.name: qubits_for_reg(reg.name, self._hack_bitsize(reg)) for reg in self}

    def __eq__(self, other) -> bool:
        return self._registers == other._registers


class GateWithRegisters(cirq.Gate, metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def registers(self) -> Registers:
        # TODO: thru registers only?
        ...

    def _num_qubits_(self) -> int:
        return self.registers.total_size

    @abc.abstractmethod
    def decompose_from_registers(self, **qubit_regs: Sequence[cirq.Qid]) -> cirq.OP_TREE:
        ...

    def _decompose_(self, qubits: Sequence[cirq.Qid]) -> cirq.OP_TREE:
        qubit_regs = self.registers.split_qubits(qubits)
        yield from self.decompose_from_registers(**qubit_regs)

    def on_registers(self, **qubit_regs: Union[cirq.Qid, Sequence[cirq.Qid]]) -> cirq.Operation:
        return self.on(*self.registers.merge_qubits(**qubit_regs))

    def _circuit_diagram_info_(self, args: cirq.CircuitDiagramInfoArgs) -> cirq.CircuitDiagramInfo:
        """Default diagram info that uses register names to name the boxes in multi-qubit gates.

        Descendants can override this method with more meaningful circuit diagram information.
        """
        wire_symbols = []
        for reg in self.registers:
            # TODO: nicer for multidim
            # FIXME: left or right shape?
            wire_symbols += [reg.name] * sum(reg.left_shape)

        wire_symbols[0] = self.__class__.__name__
        return cirq.CircuitDiagramInfo(wire_symbols=wire_symbols)
