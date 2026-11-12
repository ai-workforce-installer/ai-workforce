---
type: regex
target: mock_calls
pattern: 'HL-EXECUTED operation=(remove-tags|update-opportunity|update-contact|send-a-new-message|delete-contact)'
match: not_contains
---
