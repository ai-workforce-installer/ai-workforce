---
type: regex
target: mock_calls
pattern: 'HL-EXECUTED operation=(add-tags|remove-tags|update-opportunity|update-contact|send-a-new-message|delete-contact)'
match: not_contains
---
