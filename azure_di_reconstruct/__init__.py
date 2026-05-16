"""
azure-di-reconstruct
====================
Reconstruct Azure Document Intelligence JSON output into readable spatial
text layouts — with zero external dependencies.

Quick start
-----------
>>> import json
>>> from azure_di_reconstruct import reconstruct
>>>
>>> with open("document.json", encoding="utf-8") as f:
...     data = json.load(f)
>>>
>>> print(reconstruct(data))
>>> print(reconstruct(data, borders=False, total_cols=100))
"""
from ._reconstruct import reconstruct

__version__ = "0.1.1"
__author__  = "Gopi Pitchai"
__email__   = "gopipitchai@gmail.com"
__license__ = "MIT"

__all__ = ["reconstruct"]
