# Copyright 2018 University of Groningen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Contains unittests for vermouth.processors.annotate_mut_mod.
"""

import pytest
from vermouth.molecule import Molecule
from vermouth.forcefield import ForceField
from vermouth.processors.annotate_mut_mod import (
    parse_residue_spec,
    _subdict,
    annotate_modifications,
    AnnotateMutMod
)
from vermouth.tests.datafiles import (
    FF_UNIVERSAL_TEST,
)


@pytest.fixture
def example_mol():
    mol = Molecule(force_field=ForceField(FF_UNIVERSAL_TEST))
    nodes = [
        {'chain': 'A', 'resname': 'A', 'resid': 1},  # 0
        {'chain': 'A', 'resname': 'A', 'resid': 2},  # 1
        {'chain': 'A', 'resname': 'A', 'resid': 2},  # 2
        {'chain': 'A', 'resname': 'B', 'resid': 2},  # 3
        {'chain': 'B', 'resname': 'A', 'resid': 1},  # 4
        {'chain': 'B', 'resname': 'A', 'resid': 2},  # 5
        {'chain': 'B', 'resname': 'A', 'resid': 2},  # 6
        {'chain': 'B', 'resname': 'B', 'resid': 2},  # 7
    ]
    mol.add_nodes_from(enumerate(nodes))
    return mol


@pytest.mark.parametrize('spec,expected', [
    ('', {}),
    ('-', {'chain': ''}),
    ('#', {}),
    ('-#', {'chain': ''}),
    ('A-ALA1', {'chain': 'A', 'resname': 'ALA', 'resid': 1}),
    ('A-ALA#1', {'chain': 'A', 'resname': 'ALA', 'resid': 1}),
    ('ALA1', {'resname': 'ALA', 'resid': 1}),
    ('A-ALA', {'chain': 'A', 'resname': 'ALA'}),
    ('ALA', {'resname': 'ALA'}),
    ('2', {'resid': 2}),
    ('#2', {'resid': 2}),
    ('PO4#3', {'resname': 'PO4', 'resid': 3}),
    ('PO43', {'resname': 'PO', 'resid': 43}),


])
def test_parse_residue_spec(spec, expected):
    found = parse_residue_spec(spec)
    assert found == expected


@pytest.mark.parametrize('dict1,dict2,expected', [
    ({}, {}, True),
    ({1: 1}, {}, False),
    ({}, {1: 1}, True),
    ({1: 1}, {1: 1}, True),
    ({1: 1}, {1: 1, 2: 2}, True),
    ({1: 1, 2: 2}, {1: 1}, False),
    ({1: 1}, {1: 3, 2: 2}, False),
    ({1: 1, 2: 2}, {1: 1, 2: 3}, False),
])
def test_subdict(dict1, dict2, expected):
    found = _subdict(dict1, dict2)
    assert found == expected


@pytest.mark.parametrize('mutations,expected_mut', [
    ([], {}),
    ([({'chain': 'A', 'resname': 'A', 'resid': 1}, 'ALA')], {0: {'mutation': ['ALA']}}),
    (
        [({'resname': 'A'}, 'ALA')],
        {0: {'mutation': ['ALA']},
         1: {'mutation': ['ALA']},
         2: {'mutation': ['ALA']},
         4: {'mutation': ['ALA']},
         5: {'mutation': ['ALA']},
         6: {'mutation': ['ALA']},}
    ),
    (
        [({'resid': 2, 'chain': 'B'}, 'ALA')],
        {5: {'mutation': ['ALA']},
         6: {'mutation': ['ALA']},
         7: {'mutation': ['ALA']},}
    )
])
@pytest.mark.parametrize('modifications,expected_mod', [
    ([], {}),
    ([({'chain': 'A', 'resname': 'A', 'resid': 1}, 'C-ter')], {0: {'modification': ['C-ter']}}),
    (
        [({'chain': 'A', 'resname': 'A', 'resid': 1}, 'C-ter'),
         ({'chain': 'A', 'resname': 'A', 'resid': 1}, 'HSD')],
        {0: {'modification': ['C-ter', 'HSD']}}
    ),
    ([({'resname': 'B', 'resid': 1}, 'C-ter'),], {}),
    (
        [({'resname': 'B', 'resid': 2}, 'C-ter'),],
        {3: {'modification': ['C-ter']},
         7: {'modification': ['C-ter']},}
    ),
    ([({'resname': 'B', 'resid': 1}, 'C-ter'),], {}),
])
def test_annotate_modifications(example_mol, modifications, mutations, expected_mod, expected_mut):
    annotate_modifications(example_mol, modifications, mutations)
    for node_idx, mods in expected_mod.items():
        assert _subdict(mods, example_mol.nodes[node_idx])
    for node_idx, mods in expected_mut.items():
        assert _subdict(mods, example_mol.nodes[node_idx])

@pytest.mark.parametrize('modifications,mutations', [
    ([({'chain': 'A'}, 'M')], []),  # unknown residue name
    ([], [({'resid': 1}, 'M')]),  # unknown modification name
])
def test_annotate_modifications_error(example_mol, modifications, mutations):
    with pytest.raises(NameError):
        annotate_modifications(example_mol, modifications, mutations)


@pytest.mark.parametrize('mutations,expected_mut', [
    ([], {}),
    ([('A-A1', 'ALA')], {0: {'mutation': ['ALA']}}),
    (
        [('A', 'ALA')],
        {0: {'mutation': ['ALA']},
         1: {'mutation': ['ALA']},
         2: {'mutation': ['ALA']},
         4: {'mutation': ['ALA']},
         5: {'mutation': ['ALA']},
         6: {'mutation': ['ALA']},}
    ),
    (
        [('B-2', 'ALA')],
        {5: {'mutation': ['ALA']},
         6: {'mutation': ['ALA']},
         7: {'mutation': ['ALA']},}
    )
])
@pytest.mark.parametrize('modifications,expected_mod', [
    ([], {}),
    ([('A-A1', 'C-ter')], {0: {'modification': ['C-ter']}}),
    (
        [('A-A1', 'C-ter'),
         ('A-A1', 'HSD')],
        {0: {'modification': ['C-ter', 'HSD']}}
    ),
    ([('B1', 'C-ter'),], {}),
    (
        [('B2', 'C-ter'),],
        {3: {'modification': ['C-ter']},
         7: {'modification': ['C-ter']},}
    ),
    ([('B1', 'C-ter'),], {}),
])
def test_annotate_mutmod_processor(example_mol, modifications, mutations, expected_mod, expected_mut):

    AnnotateMutMod(modifications, mutations).run_molecule(example_mol)
    for node_idx, mods in expected_mod.items():
        assert _subdict(mods, example_mol.nodes[node_idx])
    for node_idx, mods in expected_mut.items():
        assert _subdict(mods, example_mol.nodes[node_idx])