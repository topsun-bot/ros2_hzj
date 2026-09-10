"""Pytest plugin: rebuild DimOS DDSConfig on Pydantic 2.13.

Does not modify ``ddsservice.py``. Enable with ``-p hzj_dds_compat`` and
``PYTHONPATH`` including ``scripts/bench``.
"""

from __future__ import annotations


def pytest_configure(config: object) -> None:  # noqa: ARG001
    try:
        from cyclonedds.qos import Qos as _Qos
        import dimos.protocol.service.ddsservice as ddsvc

        ddsvc.Qos = _Qos
        ddsvc.DDSConfig.model_rebuild()
    except Exception:
        return
