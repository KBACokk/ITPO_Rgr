# Architecture of **bookings-s11**

This project is a resilient booking system consisting of three microservices.

## Interaction Flow

```
[ Client (Browser / curl) ]
             |
             | HTTP (REST API)
             v
     [ REST API Gateway ]  (port 8080)
             |
             | gRPC
             v
     [ BookingsService ]   (port 8272)
             |
             | gRPC
             v
   [ AvailabilityService ] (port 8273)
```

## Components

1. **REST API Gateway (port 8080)**: 
   - Client entry point. Receives REST requests and proxies them to the BookingsService gRPC service.
   - Serves the static HTML interface at `/`.
   
2. **BookingsService (port 8272)**:
   - Core booking logic (create, get, list).
   - Database: SQLite (`/data/bookings.db`).
   - Before completing a booking, it requests a slot reservation from the AvailabilityService.
   - Performs a compensating transaction (ReleaseSlot) if the local database transaction fails.

3. **AvailabilityService (port 8273)**:
   - Manages slot availability.
   - Database: SQLite (`/data/availability.db`).
   - Ensures slot uniqueness with a composite primary key (resource_id, date).

## Resiliency

- Distributed transaction pattern with compensation.
- Isolated databases for each service.