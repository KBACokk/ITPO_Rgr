from __future__ import annotations

import logging
import os
from pathlib import Path

import grpc
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import bookings_pb2
import bookings_pb2_grpc

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BOOKINGS_GRPC_TARGET = os.environ.get("BOOKINGS_GRPC_TARGET", "localhost:8272")

app = FastAPI(
    title="bookings-s11 gateway",
    description="REST вход для проекта bookings-s11 (неделя 17).",
    version="1.0.0",
)

_STATIC = Path(__file__).resolve().parent / "static"


@app.get("/")
def ui():
    """Простая HTML-страница для ручных проверок без curl."""
    index = _STATIC / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="static UI missing")
    return FileResponse(index, media_type="text/html; charset=utf-8")


_channel: grpc.Channel | None = None
_stub: bookings_pb2_grpc.BookingsServiceStub | None = None


def _get_stub() -> bookings_pb2_grpc.BookingsServiceStub:
    global _channel, _stub
    if _stub is None:
        _channel = grpc.insecure_channel(BOOKINGS_GRPC_TARGET)
        _stub = bookings_pb2_grpc.BookingsServiceStub(_channel)
    return _stub


class BookingCreate(BaseModel):
    resource_id: str = Field(..., examples=["room-A"])
    date: str = Field(..., examples=["2026-06-01"])
    title: str = Field(..., examples=["Stand-up"])


class BookingOut(BaseModel):
    id: str
    resource_id: str
    date: str
    title: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "bookings-s11-gateway"}


@app.post("/api/bookings", response_model=BookingOut)
def create_booking(body: BookingCreate):
    try:
        b = _get_stub().CreateBooking(
            bookings_pb2.CreateBookingRequest(
                resource_id=body.resource_id,
                date=body.date,
                title=body.title,
            ),
            timeout=10,
        )
        return BookingOut(
            id=b.id,
            resource_id=b.resource_id,
            date=b.date,
            title=b.title,
        )
    except grpc.RpcError as e:
        log.warning("CreateBooking failed: %s", e)
        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
            raise HTTPException(status_code=409, detail=e.details())
        raise HTTPException(status_code=502, detail=e.details()) from e


@app.get("/api/bookings", response_model=list[BookingOut])
def list_bookings():
    try:
        resp = _get_stub().ListBookings(bookings_pb2.ListBookingsRequest(), timeout=10)
        return [
            BookingOut(
                id=x.id,
                resource_id=x.resource_id,
                date=x.date,
                title=x.title,
            )
            for x in resp.bookings
        ]
    except grpc.RpcError as e:
        log.warning("ListBookings failed: %s", e)
        raise HTTPException(status_code=502, detail=e.details()) from e


@app.get("/api/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: str):
    try:
        b = _get_stub().GetBooking(
            bookings_pb2.GetBookingRequest(id=booking_id),
            timeout=10,
        )
        return BookingOut(
            id=b.id,
            resource_id=b.resource_id,
            date=b.date,
            title=b.title,
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="not found") from e
        raise HTTPException(status_code=502, detail=e.details()) from e
