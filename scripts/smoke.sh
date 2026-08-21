#!/usr/bin/env bash
# CCOS single-command smoke — must pass before claiming green.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.

echo "=== 1. Determinism ==="
python -c "
from world.core.world import World
from world.core.entity import Label, Transform, Mass, Energy
w1 = World(seed=42); w1.spawn(Label('a'), Transform(), Mass(1), Energy(10))
h1 = [w1.tick() for _ in range(5)][-1]
w2 = World(seed=42); w2.spawn(Label('a'), Transform(), Mass(1), Energy(10))
h2 = [w2.tick() for _ in range(5)][-1]
assert h1 == h2, 'determinism broken'
print('OK', h1[:16])
"

echo "=== 2. World v1.6 science loop ==="
python scripts/world_v16_demo.py

echo "=== 3. Materials elastic/plastic ==="
python -c "
from world.materials.adapter import MaterialsAdapter, Material
m = MaterialsAdapter()
m.register(Material('steel', young_modulus=200e9, yield_stress=250e6))
assert m.strain('steel', 200e9) == 1.0
assert m.materials['steel'].plastic_strain == 0.0
m.apply_stress('steel', 300e6)
assert m.materials['steel'].plastic_strain > 0
print('OK materials')
"

echo "=== 4. Strict mode + external oracle ==="
python -m pytest tests/world/test_strict_and_oracle.py -q --tb=line

echo "=== 5. Pytest world + AGS core ==="
python -m pytest tests/world/ tests/ags/test_v12_teaching.py tests/ags/test_v13_collaboration.py tests/ags/test_v14_science.py tests/ags/test_v15_reproduction.py -q --tb=line

echo "=== SMOKE PASSED ==="
