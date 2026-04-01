"""Cosmos DB-backed checkpointer for LangGraph conversation state."""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    SerializerProtocol,
)

logger = logging.getLogger(__name__)


class CosmosDBCheckpointer(BaseCheckpointSaver):
    """
    LangGraph checkpoint saver that persists graph state to Azure Cosmos DB.

    Each checkpoint is stored as a Cosmos document whose ``id`` is built from
    the thread_id (conversation_id) and the checkpoint's ``ts`` timestamp so
    that multiple checkpoints per conversation are supported.

    Parameters
    ----------
    endpoint:
        Cosmos DB account URI.
    key:
        Primary or secondary master key.
    database_name:
        Database name (created on first use if it does not exist).
    container_name:
        Container name (created on first use if it does not exist).
    serde:
        Optional custom serializer; falls back to JSON.
    """

    def __init__(
        self,
        endpoint: str,
        key: str,
        database_name: str,
        container_name: str,
        serde: Optional[SerializerProtocol] = None,
    ) -> None:
        super().__init__(serde=serde)

        client = CosmosClient(url=endpoint, credential=key)

        db = client.create_database_if_not_exists(id=database_name)
        self._container = db.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/thread_id"),
            offer_throughput=400,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _doc_id(thread_id: str, ts: str) -> str:
        # Cosmos id must not contain '/' – replace with '-'
        safe_ts = ts.replace("/", "-").replace(":", "-")
        return f"{thread_id}_{safe_ts}"

    def _to_doc(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> Dict[str, Any]:
        thread_id = config["configurable"]["thread_id"]
        ts = checkpoint["ts"]
        
        # Serialize checkpoint and metadata using the new typed API
        cp_type, cp_bytes = self.serde.dumps_typed(checkpoint)
        meta_type, meta_bytes = self.serde.dumps_typed(metadata)

        return {
            "id": self._doc_id(thread_id, ts),
            "type": "checkpoint",
            "thread_id": thread_id,
            "checkpoint_id": checkpoint["id"],
            "ts": ts,
            "checkpoint": {
                "type": cp_type,
                "data": base64.b64encode(cp_bytes).decode("utf-8")
            },
            "metadata": {
                "type": meta_type,
                "data": base64.b64encode(meta_bytes).decode("utf-8")
            },
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

    def _from_doc(
        self, doc: Dict[str, Any]
    ) -> Tuple[Checkpoint, CheckpointMetadata]:
        raw_cp = doc["checkpoint"]
        raw_meta = doc.get("metadata")

        # Handle new format (dict with type and data)
        if isinstance(raw_cp, dict) and "type" in raw_cp and "data" in raw_cp:
            cp_type = raw_cp["type"]
            cp_bytes = base64.b64decode(raw_cp["data"])
            checkpoint = self.serde.loads_typed((cp_type, cp_bytes))
        else:
            # Fallback for old format (string)
            checkpoint = (
                self.serde.loads(raw_cp.encode("utf-8"))
                if hasattr(self.serde, "loads")
                else json.loads(raw_cp)
            )

        if isinstance(raw_meta, dict) and "type" in raw_meta and "data" in raw_meta:
            meta_type = raw_meta["type"]
            meta_bytes = base64.b64decode(raw_meta["data"])
            metadata = self.serde.loads_typed((meta_type, meta_bytes))
        else:
            # Fallback for old format (string)
            metadata = json.loads(raw_meta) if raw_meta else {}

        return checkpoint, metadata

    # ------------------------------------------------------------------
    # BaseCheckpointSaver interface
    # ------------------------------------------------------------------

    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """Return the latest (or specific) checkpoint for a thread."""
        thread_id = config["configurable"]["thread_id"]
        thread_ts: Optional[str] = config["configurable"].get("thread_ts")

        try:
            if thread_ts:
                doc_id = self._doc_id(thread_id, thread_ts)
                doc = self._container.read_item(item=doc_id, partition_key=thread_id)
                checkpoint, metadata = self._from_doc(doc)
                
                # Fetch pending writes
                writes_query = (
                    "SELECT * FROM c WHERE c.thread_id = @tid "
                    "AND c.checkpoint_id = @cid AND c.type = 'write'"
                )
                writes_items = self._container.query_items(
                    query=writes_query,
                    parameters=[
                        {"name": "@tid", "value": thread_id},
                        {"name": "@cid", "value": checkpoint["id"]},
                    ],
                    partition_key=thread_id,
                )
                pending_writes = []
                for wdoc in writes_items:
                    raw_v = wdoc["value"]
                    v_type = raw_v["type"]
                    v_bytes = base64.b64decode(raw_v["data"])
                    value = self.serde.loads_typed((v_type, v_bytes))
                    pending_writes.append((wdoc["task_id"], wdoc["channel"], value))

                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=metadata,
                    pending_writes=pending_writes,
                )

            # No specific ts → fetch the most recent checkpoint
            query = (
                "SELECT TOP 1 * FROM c WHERE c.thread_id = @tid "
                "AND c.type = 'checkpoint' "
                "ORDER BY c.ts DESC"
            )
            items = list(
                self._container.query_items(
                    query=query,
                    parameters=[{"name": "@tid", "value": thread_id}],
                    partition_key=thread_id,
                )
            )
            if not items:
                return None

            checkpoint, metadata = self._from_doc(items[0])
            
            # Fetch pending writes
            writes_query = (
                "SELECT * FROM c WHERE c.thread_id = @tid "
                "AND c.checkpoint_id = @cid AND c.type = 'write'"
            )
            writes_items = self._container.query_items(
                query=writes_query,
                parameters=[
                    {"name": "@tid", "value": thread_id},
                    {"name": "@cid", "value": checkpoint["id"]},
                ],
                partition_key=thread_id,
            )
            pending_writes = []
            for wdoc in writes_items:
                raw_v = wdoc["value"]
                v_type = raw_v["type"]
                v_bytes = base64.b64decode(raw_v["data"])
                value = self.serde.loads_typed((v_type, v_bytes))
                pending_writes.append((wdoc["task_id"], wdoc["channel"], value))

            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "thread_ts": items[0]["ts"],
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
                pending_writes=pending_writes,
            )

        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as exc:
            logger.error("get_tuple failed: %s", exc, exc_info=True)
            return None

    def list(
        self,
        config: Dict[str, Any],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """Yield checkpoints for a thread, newest first."""
        thread_id = config["configurable"]["thread_id"]
        top_clause = f"TOP {limit}" if limit else ""

        query = (
            f"SELECT {top_clause} * FROM c WHERE c.thread_id = @tid "
            "AND c.type = 'checkpoint' "
            "ORDER BY c.ts DESC"
        )
        try:
            items = self._container.query_items(
                query=query,
                parameters=[{"name": "@tid", "value": thread_id}],
                partition_key=thread_id,
            )
            for doc in items:
                checkpoint, metadata = self._from_doc(doc)
                
                # Fetch pending writes
                writes_query = (
                    "SELECT * FROM c WHERE c.thread_id = @tid "
                    "AND c.checkpoint_id = @cid AND c.type = 'write'"
                )
                writes_items = self._container.query_items(
                    query=writes_query,
                    parameters=[
                        {"name": "@tid", "value": thread_id},
                        {"name": "@cid", "value": checkpoint["id"]},
                    ],
                    partition_key=thread_id,
                )
                pending_writes = []
                for wdoc in writes_items:
                    raw_v = wdoc["value"]
                    v_type = raw_v["type"]
                    v_bytes = base64.b64decode(raw_v["data"])
                    value = self.serde.loads_typed((v_type, v_bytes))
                    pending_writes.append((wdoc["task_id"], wdoc["channel"], value))

                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "thread_ts": doc["ts"],
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=metadata,
                    pending_writes=pending_writes,
                )
        except Exception as exc:
            logger.error("list checkpoints failed: %s", exc, exc_info=True)

    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist a checkpoint and return the updated config."""
        doc = self._to_doc(config, checkpoint, metadata)
        try:
            self._container.upsert_item(doc)
        except Exception as exc:
            logger.error("put checkpoint failed: %s", exc, exc_info=True)

        thread_id = config["configurable"]["thread_id"]
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": checkpoint["ts"],
            }
        }

    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Store intermediate writes linked to a checkpoint."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"]["checkpoint_id"]

        for idx, (channel, value) in enumerate(writes):
            # Using a deterministic index for storage
            write_id = f"write_{thread_id}_{checkpoint_id}_{task_id}_{idx}"

            # Serialize value using the new typed API
            v_type, v_bytes = self.serde.dumps_typed(value)

            doc = {
                "id": write_id,
                "type": "write",
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "channel": channel,
                "value": {
                    "type": v_type,
                    "data": base64.b64encode(v_bytes).decode("utf-8")
                },
                "task_path": task_path,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                self._container.upsert_item(doc)
            except Exception as exc:
                logger.error("put_writes failed: %s", exc, exc_info=True)

    def delete_conversation(self, thread_id: str) -> None:
        """Delete all checkpoints and writes for a given thread_id."""
        query = "SELECT c.id FROM c WHERE c.thread_id = @tid"
        try:
            items = self._container.query_items(
                query=query,
                parameters=[{"name": "@tid", "value": thread_id}],
                partition_key=thread_id,
            )
            for item in items:
                self._container.delete_item(item["id"], partition_key=thread_id)
        except Exception as exc:
            logger.error("delete_conversation failed: %s", exc, exc_info=True)
