# WebSocket Client Guide

## Connection

Connect to the WebSocket endpoint at:

```
ws://<host>:<port>/ws/events
```

After the connection is established, the server does **not** send any messages by default. You must explicitly subscribe to topics of interest.

## Protocol

All messages exchanged between client and server are JSON objects.

### Discover Available Topics

Request the list of all topics the server can produce:

```json
{ "get_topics": true }
```

Response:

```json
{
  "type": "available_topics",
  "topics": [
    "config.updated",
    "energy.state",
    "miner.state",
    "policy.context",
    "rule.engaged"
  ]
}
```

### Subscribe to Topics

Send a `subscribe` message with an array of topic patterns:

```json
{ "subscribe": ["energy.*", "miner.state"] }
```

Response (confirmation with the full list of your active subscriptions):

```json
{
  "type": "subscribed",
  "topics": ["energy.*", "miner.state"]
}
```

### Unsubscribe from Topics

```json
{ "unsubscribe": ["energy.*"] }
```

Response:

```json
{
  "type": "subscribed",
  "topics": ["miner.state"]
}
```

### Receiving Events

Once subscribed, events are pushed as they occur:

```json
{
  "topic": "energy.state",
  "payload": {
    "optimization_unit_id": "550e8400-e29b-41d4-a716-446655440000",
    "optimization_unit_name": "Solar Unit 1",
    "energy_source_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "energy_state_snapshot": { ... }
  }
}
```

## Topic Pattern Matching

Subscription patterns use glob-style matching (similar to file path wildcards):

| Pattern            | Matches                                                  |
|--------------------|----------------------------------------------------------|
| `energy.state`     | Only `energy.state`                                      |
| `energy.*`         | Any topic starting with `energy.` (e.g. `energy.state`)  |
| `miner.*`          | Any topic starting with `miner.` (e.g. `miner.state`)   |
| `*`                | All topics                                               |
| `*.state`          | Any topic ending with `.state`                           |

## Available Topics and Payloads

### `energy.state`

Emitted when a new energy state snapshot is read from an energy source.

```json
{
  "topic": "energy.state",
  "payload": {
    "optimization_unit_id": "string | null",
    "optimization_unit_name": "string",
    "energy_source_id": "string | null",
    "energy_state_snapshot": "object | null"
  }
}
```

### `miner.state`

Emitted when a miner changes its operational status (started, stopped, etc.).

```json
{
  "topic": "miner.state",
  "payload": {
    "miner_id": "string | null",
    "miner_name": "string",
    "old_status": "string | null",
    "new_status": "string | null"
  }
}
```

### `rule.engaged`

Emitted when a policy rule produces a mining decision for an optimization unit.

```json
{
  "topic": "rule.engaged",
  "payload": {
    "optimization_unit_id": "string | null",
    "optimization_unit_name": "string",
    "policy_id": "string | null",
    "policy_name": "string",
    "miner_id": "string | null",
    "decision": "string | null",
    "miner_status": "string"
  }
}
```

`decision` values: `"start_mining"`, `"stop_mining"`, `"maintain_state"`.

### `policy.context`

Emitted when a new decisional context is composed for an optimization unit.

```json
{
  "topic": "policy.context",
  "payload": {
    "optimization_unit_id": "string | null",
    "optimization_unit_name": "string",
    "context": "object | null",
    "target_miner_ids": ["string"]
  }
}
```

### `config.updated`

Emitted when a configuration entity is created, updated, or removed.

```json
{
  "topic": "config.updated",
  "payload": {
    "entity_type": "string",
    "entity_id": "string | null",
    "action": "string"
  }
}
```

`action` values: `"created"`, `"updated"`, `"removed"`.

## Client Examples

### JavaScript / Browser

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/events");

ws.onopen = () => {
  // Discover available topics
  ws.send(JSON.stringify({ get_topics: true }));

  // Subscribe to all energy and miner events
  ws.send(JSON.stringify({ subscribe: ["energy.*", "miner.*"] }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "available_topics") {
    console.log("Available topics:", data.topics);
    return;
  }

  if (data.type === "subscribed") {
    console.log("Active subscriptions:", data.topics);
    return;
  }

  // Domain event
  console.log(`[${data.topic}]`, data.payload);
};

ws.onclose = () => {
  console.log("Disconnected");
};
```

### Python (websockets library)

```python
import asyncio
import json
import websockets

async def main():
    async with websockets.connect("ws://localhost:8000/ws/events") as ws:
        # Subscribe to everything
        await ws.send(json.dumps({"subscribe": ["*"]}))

        async for raw in ws:
            data = json.loads(raw)
            if data.get("type") == "subscribed":
                print(f"Subscribed to: {data['topics']}")
            else:
                print(f"[{data['topic']}] {data['payload']}")

asyncio.run(main())
```

## Notes

- A newly connected client receives **no events** until it sends a `subscribe` message.
- Multiple `subscribe` messages are cumulative — subscriptions are added, not replaced.
- To replace all subscriptions, unsubscribe from `["*"]` first, then subscribe to the desired topics.
- Dead connections are automatically cleaned up by the server when a send fails.
- All ID fields are serialized as strings (UUID format).
