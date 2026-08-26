"""Resource lease allocate/release regression."""

from __future__ import annotations

from kernel.resources.manager import ResourceManager, Quota


def test_lease_release_restores_capacity():
    rm = ResourceManager(default_quota=Quota(cpu_units=10, memory_mb=100))
    assert rm.allocate("agent", cpu=7, memory_mb=70, lease_id="i1")
    assert not rm.allocate("agent", cpu=4, lease_id="i2")
    rm.release("agent", lease_id="i1")
    assert rm.allocate("agent", cpu=4, memory_mb=20, lease_id="i2")
    u = rm.usage("agent")
    assert u.cpu_units <= 10


def test_release_without_lease_still_works():
    rm = ResourceManager(default_quota=Quota(cpu_units=5, memory_mb=50))
    assert rm.allocate("a", cpu=2, memory_mb=10)
    rm.release("a", cpu=2, memory_mb=10)
    assert rm.usage("a").cpu_units == 0
