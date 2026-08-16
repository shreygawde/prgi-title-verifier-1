# API Contract

Base URL:

`http://localhost:5000/api`

---

## POST /verify

Verifies a proposed publication title against registered PRGI titles and applicable rules.

### Request

```json
{
  "title": "Indian Express",
  "language": "English",
  "periodicity": "Daily"
}