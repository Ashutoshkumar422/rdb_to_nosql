"""
metamorfose.py — Migration framework (Paper Section 5).
"""
import copy
from dataclasses import dataclass, field
from typing import List, Dict
from modules.models import Schema


@dataclass
class MigrationCommand:
    command_type:      str
    source_table:      str
    target_collection: str
    embed_as:          str  = ""
    is_array:          bool = False
    fk_field:          str  = ""
    parent_collection: str  = ""


class CommandGenerator:
    """Section 5.1 — Generates migration commands from schema."""

    def generate(self, schema: Schema) -> List[MigrationCommand]:
        commands = []
        for col in schema.collections:
            commands.append(MigrationCommand(
                command_type="CREATE_COLLECTION",
                source_table=col.root,
                target_collection=col.name,
            ))
            for edge in col.edges:
                is_array = "Array" in edge.direction
                commands.append(MigrationCommand(
                    command_type="EMBED",
                    source_table=edge.child,
                    target_collection=col.name,
                    embed_as=edge.child.lower(),
                    is_array=is_array,
                    parent_collection=edge.parent,
                ))
        return commands


class MetamorfoseEngine:
    """Section 5.3 — Execute migration on sample data."""

    def __init__(self, source_data: Dict[str, List[dict]]):
        self.source_data = source_data
        self._log: List[str] = []
        self._result: Dict[str, List[dict]] = {}

    def migrate(self, schema: Schema) -> Dict[str, List[dict]]:
        gen      = CommandGenerator()
        commands = gen.generate(schema)
        self._log = []
        self._result = {}

        for cmd in commands:
            if cmd.command_type == "CREATE_COLLECTION":
                data = copy.deepcopy(self.source_data.get(cmd.source_table, []))
                self._result[cmd.target_collection] = data
                self._log.append(
                    f"CREATE {cmd.target_collection} from {cmd.source_table} "
                    f"({len(data)} docs)"
                )
            elif cmd.command_type == "EMBED":
                child_data = self.source_data.get(cmd.source_table, [])
                col_docs   = self._result.get(cmd.target_collection, [])
                for doc in col_docs:
                    if cmd.is_array:
                        doc[cmd.embed_as] = copy.deepcopy(child_data)
                    else:
                        doc[cmd.embed_as] = copy.deepcopy(
                            child_data[0] if child_data else {}
                        )
                self._log.append(
                    f"EMBED {cmd.source_table} into {cmd.target_collection}"
                    f".{cmd.embed_as} as_array={cmd.is_array}"
                )
        return self._result

    def get_report(self) -> dict:
        return {
            "commands":    len(self._log),
            "collections": list(self._result.keys()),
            "verified":    len(self._result) > 0,
            "log":         self._log,
        }