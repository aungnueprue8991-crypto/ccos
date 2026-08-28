"""AGS — Agent Genesis System (developmental organism runtime).

CCOS = constitution (what may exist / happen).
AGS  = organism (how an agent develops).
"""

from ags.core.agent import AGSAgent
from ags.genome.traits import AgentGenome
from ags.genome.manager import GenomeManager
from ags.models.adapter import MockAdapter, build_adapter_from_config

__all__ = [
    "AGSAgent",
    "AgentGenome",
    "GenomeManager",
    "MockAdapter",
    "build_adapter_from_config",
]
__version__ = "0.1.0"
