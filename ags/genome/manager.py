"""Genome manager — persistence, mutation, crossover, lineage."""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional

from ags.genome.traits import AgentGenome
from ags.shared.database import get_db, jdump, jload
from ags.shared.types import new_id, now_ts

log = logging.getLogger("ags.genome")

MUTATION_RATE = 0.15
MUTATION_STD = 0.08
CLAMP_MIN = 0.01
CLAMP_MAX = 0.99


class GenomeManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db = get_db(db_path) if db_path else get_db()

    def create_default(self, agent_id: str) -> AgentGenome:
        genome = AgentGenome(genome_id=new_id())
        self.save(genome, agent_id)
        return genome

    def create_random(self, agent_id: str) -> AgentGenome:
        genome = AgentGenome.random(genome_id=new_id())
        self.save(genome, agent_id)
        return genome

    def save(self, genome: AgentGenome, agent_id: str) -> None:
        d = genome.to_dict()
        with self.db.tx() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO genomes
                   (genome_id, agent_id, traits, parent_a, parent_b, generation, mutations, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    genome.genome_id,
                    agent_id,
                    jdump(d),
                    genome.parent_genome_ids[0] if genome.parent_genome_ids else None,
                    genome.parent_genome_ids[1] if len(genome.parent_genome_ids) > 1 else None,
                    genome.generation,
                    jdump(genome.mutation_history),
                    now_ts(),
                ),
            )

    def load(self, agent_id: str) -> Optional[AgentGenome]:
        row = self.db.fetchone(
            "SELECT traits FROM genomes WHERE agent_id = ? ORDER BY rowid DESC LIMIT 1",
            (agent_id,),
        )
        if not row:
            return None
        d = jload(row["traits"])
        return AgentGenome.from_dict(d) if d else None

    def mutate(
        self,
        genome: AgentGenome,
        agent_id: str,
        rate: float = MUTATION_RATE,
        std: float = MUTATION_STD,
    ) -> AgentGenome:
        new_genome = AgentGenome.from_dict(genome.to_dict())
        new_genome.genome_id = new_id()
        new_genome.parent_genome_ids = [genome.genome_id]
        mutations_applied: List[Dict[str, Any]] = []

        def mutate_dc(obj: Any) -> None:
            for fname, fval in vars(obj).items():
                if isinstance(fval, float) and random.random() < rate:
                    delta = random.gauss(0, std)
                    old_val = fval
                    new_val = max(CLAMP_MIN, min(CLAMP_MAX, fval + delta))
                    setattr(obj, fname, round(new_val, 4))
                    mutations_applied.append({
                        "trait": fname,
                        "from": round(old_val, 4),
                        "to": round(new_val, 4),
                        "delta": round(delta, 4),
                    })

        for group in (
            new_genome.cognitive,
            new_genome.curiosity,
            new_genome.learning,
            new_genome.exploration,
            new_genome.social,
            new_genome.planning,
            new_genome.personality,
        ):
            mutate_dc(group)

        for domain in list(new_genome.skill_affinities.keys()):
            if random.random() < rate:
                old = new_genome.skill_affinities[domain]
                new_val = max(0.05, min(0.95, old + random.gauss(0, std)))
                new_genome.skill_affinities[domain] = round(new_val, 4)
                mutations_applied.append({
                    "trait": f"affinity:{domain}",
                    "from": old,
                    "to": new_val,
                })

        new_genome.mutation_history = list(genome.mutation_history) + [{
            "parent": genome.genome_id,
            "mutations": mutations_applied,
            "count": len(mutations_applied),
            "timestamp": now_ts(),
        }]
        new_genome.generation = genome.generation + 1
        self.save(new_genome, agent_id)
        return new_genome

    def crossover(
        self,
        genome_a: AgentGenome,
        genome_b: AgentGenome,
        child_agent_id: str,
    ) -> AgentGenome:
        child = AgentGenome(genome_id=new_id())
        child.generation = max(genome_a.generation, genome_b.generation) + 1
        child.parent_genome_ids = [genome_a.genome_id, genome_b.genome_id]

        def xover(a_obj, b_obj, target):
            for fname in vars(a_obj):
                a_val, b_val = getattr(a_obj, fname), getattr(b_obj, fname)
                setattr(target, fname, a_val if random.random() < 0.5 else b_val)

        xover(genome_a.cognitive, genome_b.cognitive, child.cognitive)
        xover(genome_a.curiosity, genome_b.curiosity, child.curiosity)
        xover(genome_a.learning, genome_b.learning, child.learning)
        xover(genome_a.exploration, genome_b.exploration, child.exploration)
        xover(genome_a.social, genome_b.social, child.social)
        xover(genome_a.planning, genome_b.planning, child.planning)
        xover(genome_a.personality, genome_b.personality, child.personality)

        domains = set(genome_a.skill_affinities) | set(genome_b.skill_affinities)
        for d in domains:
            child.skill_affinities[d] = (
                genome_a.skill_affinities.get(d, 0.5)
                if random.random() < 0.5
                else genome_b.skill_affinities.get(d, 0.5)
            )

        child.mutation_history.append({
            "type": "crossover",
            "parent_a": genome_a.genome_id,
            "parent_b": genome_b.genome_id,
            "timestamp": now_ts(),
        })
        child = self.mutate(child, child_agent_id, rate=MUTATION_RATE * 0.5)
        return child

    def get_lineage(self, agent_id: str) -> List[Dict]:
        return self.db.fetchall(
            "SELECT genome_id, parent_a, parent_b, generation, mutations, created_at "
            "FROM genomes WHERE agent_id = ? ORDER BY generation ASC",
            (agent_id,),
        )

    def compare(self, genome_a: AgentGenome, genome_b: AgentGenome) -> Dict:
        a, b = genome_a.to_dict(), genome_b.to_dict()
        diffs = {}
        for group in (
            "cognitive",
            "curiosity",
            "learning",
            "exploration",
            "social",
            "planning",
            "personality",
        ):
            ag, bg = a.get(group, {}), b.get(group, {})
            for k in ag:
                if k in bg and isinstance(ag[k], (int, float)):
                    d = abs(ag[k] - bg[k])
                    if d > 0.001:
                        diffs[f"{group}.{k}"] = {"a": ag[k], "b": bg[k], "diff": round(d, 4)}
        return diffs
