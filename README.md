# IDCrockford

Crockford Base32 ID encoder/decoder with FastAPI dependency injection support for validation and generation of Crockford Base32 IDs.

`idcrockford` has 3 interfaces:

- CLI
- Library
- FastAPI dependency

## Installation

```bash
pip install idcrockford
```

or using [uv](https://docs.astral.sh/uv/):

```bash
uvx idcrockford
```

## CLI

```bash
uvx idcrockford --help

usage: idcrockford [-h] [--checksum] [--split SIZE] [--padding] [--strict] {encode,decode,normalize,generate} [input]

Crockford Base32 Utility

positional arguments:
  {encode,decode,normalize,generate}
                        Operation to perform
  input                 Input to process. For encode: integer or string. For generate: size (optional)

options:
  -h, --help            show this help message and exit
  --checksum            Add/validate checksum symbol
  --split SIZE          Split encoded string with hyphens (chunk size, default: no splitting)
  --padding             Add padding characters (=) to output
  --strict              Strict mode for normalize command - error if normalization needed
```

## Library

```python
from idcrockford import Base32Crockford

crockford = Base32Crockford(
    checksum=True,
    split=4,
    padding=True,
)

# Encode and decode
crockford.encode(1234567890) # 14SC-0PJV
crockford.decode("14SC-0PJV") # 1234567890

# Generate
crockford.generate() # 16 random characters
crockford.generate(size=10) # 10 random characters
crockford.generate(size=10, checksum=True, split=4, padding=True) # 10 random characters with checksum, split and padding

# TODO: add normalize
crockford.normalize("14SC-0PJV") # 14SC0PJV
```

## FastAPI Dependency

```python
from fastapi import FastAPI, Depends
from idcrockford import CFIdentifierConfig

IdentifierConfig = CFIdentifierConfig(checksum=True, size=16)

app = FastAPI()

@app.get("/items/{id}")
def read_item(id: str = Depends(IdentifierConfig.validate)):
    return {"id": id}

@app.post("/items/")
def create_item(id: str = Depends(IdentifierConfig.generate)):
    return {"id": id}
```

## Roadmap

- [ ] Add `normalize` method to `CFIdentifierConfig`
- [ ] Support Pydantic custom type for Crockford Base32 ID validation and generation

## License

MIT

### Other packages

- [inveniosoftware/base32-lib](https://github.com/inveniosoftware/base32-lib) - Python Base32 encoder/decoder with no padding
- [jbittel/base32-crockford](https://github.com/jbittel/base32-crockford) - JavaScript Base32 encoder/decoder with Crockford checksum
- [DrSLDR/krock32](https://github.com/DrSLDR/krock32) - Kotlin Base32 encoder/decoder with Crockford checksum
- [pat-jpnk/Crockford-Base32](https://github.com/pat-jpnk/Crockford-Base32) - JavaScript Base32 encoder/decoder with Crockford checksum
