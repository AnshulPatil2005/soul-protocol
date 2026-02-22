# Soul Protocol

The open standard for portable AI identity and memory.

## Installation

```bash
pip install soul-protocol
```

## Quick Start

```python
from soul_protocol import Soul

# Birth a new soul
soul = await Soul.birth(name="Aria", archetype="The Compassionate Creator")

# Remember something
await soul.remember("User prefers Python over JavaScript", importance=8)

# Generate system prompt
prompt = soul.to_system_prompt()

# Export as portable .soul file
await soul.export("aria.soul")
```

## License

MIT
