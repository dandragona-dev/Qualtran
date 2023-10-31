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


from qualtran.surface_code.algorithm_summary import AlgorithmSummary
from qualtran.surface_code.t_factory import TFactory


def test_footprint():
    factory = TFactory(
        num_qubits=5, generation_cycle_duration_ns=3, num_t_per_cycle=0.1, error_rate=1e-9
    )
    magic_count = AlgorithmSummary(t_gates=1, toffoli_gates=1)
    assert factory.footprint() == 5
    assert factory.n_cycles(magic_count) == 50
    assert factory.spacetime_footprint() == 150
    assert factory.distillation_error(magic_count, 1e-3) is NotImplemented
