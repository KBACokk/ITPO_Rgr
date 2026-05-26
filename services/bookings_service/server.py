from __future__ import annotations

import logging
import os
import sqlite3
import uuid
from concurrent import futures

import grpc

import availability_pb2
import availability_pb2_grpc
import bookings_pb2
import bookings_pb2_grpc

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BOOKINGS_DB = os.environ.get("BOOKINGS_DB", "bookings.db")
GRPC_PORT = int(os.environ.get("GRPC_PORT", "8272"))
AVAILABILITY_GRPC_TARGET = os.environ.get(
    "AVAILABILITY_GRPC_TARGET", "localhost:8273"
)


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(BOOKINGS_DB, check_same_thread=False)


def _init_db() -> None:
    os.makedirs(os.path.dirname(BOOKINGS_DB) or ".", exist_ok=True)
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
              id TEXT PRIMARY KEY,
              resource_id TEXT NOT NULL,
              date TEXT NOT NULL,
              title TEXT NOT NULL
            )
            """
        )


class BookingsServicer(bookings_pb2_grpc.BookingsServiceServicer):
    def __init__(self) -> None:
        chan = grpc.insecure_channel(AVAILABILITY_GRPC_TARGET)
        self._availability = availability_pb2_grpc.AvailabilityServiceStub(chan)

    def CreateBooking(self, request, context):
        log.info(
            "CreateBooking resource_id=%s date=%s title=%s",
            request.resource_id,
            request.date,
            request.title,
        )
        try:
            hold = self._availability.ReserveSlot(
                availability_pb2.ReserveSlotRequest(
                    resource_id=request.resource_id,
                    date=request.date,
                ),
                timeout=5,
            )
        except grpc.RpcError as e:
            log.exception("Availability reserve RPC failed")
            context.abort(grpc.StatusCode.INTERNAL, f"Availability service error: {e.details()}")

        if not hold.ok:
            context.abort(
                grpc.StatusCode.ALREADY_EXISTS,
                hold.reason or "slot unavailable",
            )

        booking_id = str(uuid.uuid4())
        conn = _conn()
        try:
            conn.execute(
                "INSERT INTO bookings (id, resource_id, date, title) VALUES (?,?,?,?)",
                (
                    booking_id,
                    request.resource_id,
                    request.date,
                    request.title,
                ),
            )
            conn.commit()
            return bookings_pb2.Booking(
                id=booking_id,
                resource_id=request.resource_id,
                date=request.date,
                title=request.title,
            )
        except Exception as exc:
            conn.rollback()
            log.exception("persist booking failed")
            try:
                self._availability.ReleaseSlot(
                    availability_pb2.ReleaseSlotRequest(
                        resource_id=request.resource_id,
                        date=request.date,
                    ),
                    timeout=5,
                )
            except grpc.RpcError:
                log.exception("compensating ReleaseSlot failed")
            context.abort(grpc.StatusCode.INTERNAL, str(exc))
        finally:
            conn.close()

    def GetBooking(self, request, context):
        log.info("GetBooking id=%s", request.id)
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT id, resource_id, date, title FROM bookings WHERE id = ?",
                (request.id,),
            )
            row = cur.fetchone()
            if not row:
                context.abort(grpc.StatusCode.NOT_FOUND, "booking not found")
            return bookings_pb2.Booking(
                id=row[0], resource_id=row[1], date=row[2], title=row[3]
            )
        finally:
            conn.close()

    def ListBookings(self, request, context):
        log.info("ListBookings")
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT id, resource_id, date, title FROM bookings ORDER BY date, id"
            )
            rows = cur.fetchall()
            return bookings_pb2.ListBookingsResponse(
                bookings=[
                    bookings_pb2.Booking(
                        id=r[0], resource_id=r[1], date=r[2], title=r[3]
                    )
                    for r in rows
                ]
            )
        finally:
            conn.close()


def serve() -> None:
    _init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bookings_pb2_grpc.add_BookingsServiceServicer_to_server(
        BookingsServicer(), server
    )
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    log.info("bookings gRPC listening on %s", GRPC_PORT)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
