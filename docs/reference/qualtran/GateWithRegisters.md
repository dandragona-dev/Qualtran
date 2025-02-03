# GateWithRegisters
`qualtran.GateWithRegisters`


<table class="tfo-notebook-buttons tfo-api nocontent" align="left">
<td>
  <a target="_blank" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L203-L533">
    <img src="https://www.tensorflow.org/images/GitHub-Mark-32px.png" />
    View source on GitHub
  </a>
</td>
</table>



`cirq.Gate`s extension with support for composite gates acting on multiple qubit registers.

Inherits From: [`Bloq`](../qualtran/Bloq.md)

<!-- Placeholder for "Used in" -->

Though Cirq was nominally designed for circuit construction for near-term devices the core
concept of the `cirq.Gate`, a programmatic representation of an operation on a state without
a complete qubit address specification, can be leveraged to describe more abstract algorithmic
primitives. To define composite gates, users derive from `cirq.Gate` and implement the
`_decompose_` method that yields the sub-operations provided a flat list of qubits.

This API quickly becomes inconvenient when defining operations that act on multiple qubit
registers of variable sizes. Qualtran extends the `cirq.Gate` idea by introducing a new abstract
base class `GateWithRegisters` containing abstract methods `registers` and optional
method `decompose_from_registers` that provides an overlay to the Cirq flat address API.

As an example, in the following code snippet we use the `GateWithRegisters` to
construct a multi-target controlled swap operation:

```
>>> import attr
>>> import cirq
>>> import qualtran
>>>
>>> @attr.frozen
... class MultiTargetCSwap(qualtran.GateWithRegisters):
...     bitsize: int
...
...     @property
...     def signature(self) -> qualtran.Signature:
...         return qualtran.Signature.build(ctrl=1, x=self.bitsize, y=self.bitsize)
...
...     def decompose_from_registers(self, context, ctrl, x, y) -> cirq.OP_TREE:
...         yield [cirq.CSWAP(*ctrl, qx, qy) for qx, qy in zip(x, y)]
...
>>> op = MultiTargetCSwap(2).on_registers(
...     ctrl=[cirq.q('ctrl')],
...     x=cirq.NamedQubit.range(2, prefix='x'),
...     y=cirq.NamedQubit.range(2, prefix='y'),
... )
>>> print(cirq.Circuit(op))
ctrl: ───MultiTargetCSwap───
         │
x0: ─────x──────────────────
         │
x1: ─────x──────────────────
         │
y0: ─────y──────────────────
         │
y1: ─────y──────────────────
```



<h2 class="add-link">Attributes</h2>

`signature`<a id="signature"></a>
: The input and output names and types for this bloq.
  
  This property can be thought of as analogous to the function signature in ordinary
  programming. For example, it is analogous to function declarations in a
  C header (`*.h`) file.
  
  This is the only mandatory method (property) you must implement to inherit from
  `Bloq`. You can optionally implement additional methods to encode more information
  about this bloq.




## Methods

<h3 id="decompose_bloq"><code>decompose_bloq</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L253-L293">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>decompose_bloq() -> 'CompositeBloq'
</code></pre>

Decompose this Bloq into its constituent parts contained in a CompositeBloq.

Bloq users can call this function to delve into the definition of a Bloq. The function
returns the decomposition of this Bloq represented as an explicit compute graph wrapped
in a `CompositeBloq` object.

Bloq authors can specify the bloq's decomposition by overriding any of the following two
methods:

- `build_composite_bloq`: Override this method to define a bloq-style decomposition using a
    `BloqBuilder` builder class to construct the `CompositeBloq` directly.
- `decompose_from_registers`: Override this method to define a cirq-style decomposition by
    yielding cirq style operations applied on qubits.

Irrespective of the bloq author's choice of backend to implement the
decomposition, bloq users will be able to access both the bloq-style and Cirq-style
interfaces. For example, users can call:

- `cirq.decompose_once(bloq.on_registers(**cirq_quregs))`: This will yield a `cirq.OPTREE`.
    Bloqs will be wrapped in `BloqAsCirqGate` as needed.
- `bloq.decompose_bloq()`: This will return a `CompositeBloq`.
   Cirq gates will be be wrapped in `CirqGateAsBloq` as needed.

Thus, `GateWithRegisters` class provides a convenient way of defining objects that can be used
interchangeably with both `Cirq` and `Bloq` constructs.

Returns




Raises

`DecomposeNotImplementedError`
: If there is no decomposition defined; namely if both:
  - `build_composite_bloq` raises a `DecomposeNotImplementedError` and
  - `decompose_from_registers` raises a `DecomposeNotImplementedError`.




<h3 id="as_cirq_op"><code>as_cirq_op</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L295-L311">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>as_cirq_op(
    qubit_manager: 'cirq.QubitManager', **in_quregs
) -> Tuple[Union['cirq.Operation', None], Dict[str, 'CirqQuregT']]
</code></pre>

Allocates/Deallocates qubits for RIGHT/LEFT only registers to construct a Cirq operation


Args

`qubit_manager`
: For allocating/deallocating qubits for RIGHT/LEFT only registers.

`in_quregs`
: Mapping from LEFT register names to corresponding cirq qubits.




Returns




<h3 id="wire_symbol"><code>wire_symbol</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L313-L320">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>wire_symbol(
    reg: Optional[<a href="../qualtran/Register.html"><code>qualtran.Register</code></a>],
    idx: Tuple[int, ...] = tuple()
) -> 'WireSymbol'
</code></pre>

On a musical score visualization, use this `WireSymbol` to represent `soq`.

By default, we use a "directional text box", which is a text box that is either
rectangular for thru-registers or facing to the left or right for non-thru-registers.

If reg is specified as `None`, this should return a Text label for the title of
the gate. If no title is needed (as the wire_symbols are self-explanatory),
this should return `Text('')`.

Override this method to provide a more relevant `WireSymbol` for the provided soquet.
This method can access bloq attributes. For example: you may want to draw either
a filled or empty circle for a control register depending on a control value bloq
attribute.

<h3 id="decompose_from_registers"><code>decompose_from_registers</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L327-L330">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>decompose_from_registers(
    *, context: 'cirq.DecompositionContext', **quregs
) -> 'cirq.OP_TREE'
</code></pre>




<h3 id="on"><code>on</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L355-L359">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>on(
    *qubits
) -> 'cirq.Operation'
</code></pre>

A `cirq.Operation` of this bloq operating on the given qubits.

This method supports an alternative decomposition backend that follows a 'Cirq-style'
association of gates with qubits to form operations. Instead of wiring up `Soquet`s,
each gate operates on qubit addresses (`cirq.Qid`s), which are reused by multiple
gates. This method lets you operate this bloq on qubits and returns a `cirq.Operation`.

The primary, bloq-native way of writing decompositions is to override
`build_composite_bloq`. If this is what you're doing, do not use this method.

To provide a Cirq-style decomposition for this bloq, implement a method (typically named
`decompose_from_registers` for historical reasons) that yields a list of `cirq.Operation`s
using `cirq.Gate.on(...)`, <a href="../qualtran/Bloq.html#on"><code>Bloq.on(...)</code></a>, <a href="../qualtran/GateWithRegisters.html#on_registers"><code>GateWithRegisters.on_registers(...)</code></a>, or
<a href="../qualtran/Bloq.html#on_registers"><code>Bloq.on_registers(...)</code></a>.

See Also




<h3 id="on_registers"><code>on_registers</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L361-L364">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>on_registers(
    **qubit_regs
) -> 'cirq.Operation'
</code></pre>

A `cirq.Operation` of this bloq operating on the given qubit registers.

This method supports an alternative decomposition backend that follows a 'Cirq-style'
association of gates with qubit registers to form operations. See <a href="../qualtran/Bloq.html#on"><code>Bloq.on()</code></a> for
more details.

Args

`**qubit_regs`
: A mapping of register name to the qubits comprising that register.




See Also




<h3 id="__pow__"><code>__pow__</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L366-L374">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>__pow__(
    power: int
) -> 'GateWithRegisters'
</code></pre>




<h3 id="controlled"><code>controlled</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L455-L506">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>controlled(
    num_controls: Union[Optional[int], 'CtrlSpec'] = None,
    control_values: Optional[Union['cirq.ops.AbstractControlValues', Sequence[Union[int,
        Collection[int]]]]] = None,
    control_qid_shape: Optional[Tuple[int, ...]] = None,
    *,
    ctrl_spec: Optional['CtrlSpec'] = None
) -> 'Bloq'
</code></pre>

Return a controlled version of self. Controls can be specified via Cirq/Bloq-style APIs.

If no arguments are specified, defaults to a single qubit control.

Supports both Cirq-style API and Bloq-style API to construct controlled Bloqs. The cirq-style
API is supported by intercepting the Cirq-style way of specifying a control specification;
via arguments `num_controls`, `control_values` and `control_qid_shape`, and constructing a
`CtrlSpec` object from it before delegating to `self.get_ctrl_system`.

By default, the system will use the <a href="../qualtran/Controlled.html"><code>qualtran.Controlled</code></a> meta-bloq to wrap this
bloq. Bloqs authors can declare their own, custom controlled versions by overriding
<a href="../qualtran/Bloq.html#get_ctrl_system"><code>Bloq.get_ctrl_system</code></a> in the bloq.


Args

`num_controls`
: Cirq style API to specify control specification -
  Total number of control qubits.

`control_values`
: Cirq style API to specify control specification -
  Which control computational basis state to apply the
  sub gate.  A sequence of length `num_controls` where each
  entry is an integer (or set of integers) corresponding to the
  computational basis state (or set of possible values) where that
  control is enabled.  When all controls are enabled, the sub gate is
  applied.  If unspecified, control values default to 1.

`control_qid_shape`
: Cirq style API to specify control specification -
  The qid shape of the controls.  A tuple of the
  expected dimension of each control qid.  Defaults to
  `(2,) * num_controls`.  Specify this argument when using qudits.

`ctrl_spec`
: Bloq style API to specify a control specification -
  An optional keyword argument `CtrlSpec`, which specifies how to control
  the bloq. The default spec means the bloq will be active when one control qubit is
  in the |1> state. See the CtrlSpec documentation for more possibilities including
  negative controls, integer-equality control, and ndarrays of control values.




Returns




<h3 id="my_tensors"><code>my_tensors</code></h3>

<a target="_blank" class="external" href="https://github.com/quantumlib/Qualtran/blob/main/qualtran/_infra/gate_with_registers.py#L511-L519">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>my_tensors(
    incoming: Dict[str, 'ConnectionT'], outgoing: Dict[str, 'ConnectionT']
) -> List['qtn.Tensor']
</code></pre>

Override this method to support native quimb simulation of this Bloq.

This method is responsible for returning tensors corresponding to the unitary, state, or
effect of the bloq. Often, this method will return one tensor for a given Bloq, but
some bloqs can be represented in a factorized form using more than one tensor.

By default, calls to <a href="../qualtran/Bloq.html#tensor_contract"><code>Bloq.tensor_contract()</code></a> will first decompose and flatten the bloq
before initiating the conversion to a tensor network. This has two consequences:
 1) Overriding this method is only necessary if this bloq does not define a decomposition
    or if the fully-decomposed form contains a bloq that does not define its tensors.
 2) Even if you override this method to provide custom tensors, they may not be used
    (by default) because we prefer the flat-decomposed version. This is usually desirable
    for contraction performance; but for finer-grained control see
    <a href="../qualtran/simulation/tensor/cbloq_to_quimb.html"><code>qualtran.simulation.tensor.cbloq_to_quimb</code></a>.

Quimb defines a connection between two tensors by a shared index. The returned tensors
from this method must use the Qualtran-Quimb index convention:
 - Each tensor index is a tuple `(cxn, j)`
 - The `cxn: qualtran.Connection` entry identifies the connection between bloq instances.
 - The second integer `j` is the bit index within high-bitsize registers,
   which is necessary due to technical restrictions.

Args

`incoming`
: A mapping from register name to Connection (or an array thereof) to use as
  left indices for the tensor network. The shape of the array matches the register's
  shape.

`outgoing`
: A mapping from register name to Connection (or an array thereof) to use as
  right indices for the tensor network.




<h3 id="num_qubits"><code>num_qubits</code></h3>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>num_qubits() -> int
</code></pre>

The number of qubits this gate acts on.




