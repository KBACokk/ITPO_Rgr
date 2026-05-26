from __future__ import annotations

import logging
import os
import sqlite3
from concurrent import futures

import grpc

import availability_pb2
import availability_pb2_grpc

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DB_PATH = os.environ.get("AVAILABILITY_DB", "availability.db")
GRPC_PORT = int(os.environ.get("GRPC_PORT", "8273"))


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def _init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS slots (
              resource_id TEXT NOT NULL,
              date TEXT NOT NULL,
              PRIMARY KEY (resource_id, date)
            )
            """
        )


class AvailabilityServicer(availability_pb2_grpc.AvailabilityServiceServicer):
    def ReserveSlot(self, request, context):
        log.info("ReserveSlot resource_id=%s date=%s", request.resource_id, request.date)
        try:
            with _conn() as conn:
                conn.execute(
                    "INSERT INTO slots (resource_id, date) VALUES (?, ?)",
                    (request.resource_id, request.date),
                )
                conn.commit()
            return availability_pb2.ReserveSlotResponse(ok=True)
        except sqlite3.IntegrityError:
            log.info(
                "slot busy resource_id=%s date=%s", request.resource_id, request.date
            )
            return availability_pb2.ReserveSlotResponse(
                ok=False, reason="slot_already_reserved"
            )

    def ReleaseSlot(self, request, context):
        log.info("ReleaseSlot resource_id=%s date=%s", request.resource_id, request.date)
        with _conn() as conn:
            conn.execute(
                "DELETE FROM slots WHERE resource_id = ? AND date = ?",
                (request.resource_id, request.date),
            )
            conn.commit()
        return availability_pb2.ReleaseSlotResponse(ok=True)


def serve() -> None:
    _init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    availability_pb2_grpc.add_AvailabilityServiceServicer_to_server(
        AvailabilityServicer(), server
    )
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    log.info("availability gRPC listening on %s", GRPC_PORT)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
