"""Modelos tipados de dominio.

Estos dataclasses no reemplazan todavia al motor historico, pero sirven como
contrato semantico para nuevos importadores, validadores y pruebas unitarias.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class FaseSemaforica:
    version_prog_id: int
    cruce_id: int
    plan_id: int
    fase_id: int
    duracion_s: int
    entreverde_s: int
    cum_inicio_s: int
    cum_fin_s: int
    es_verde_lateral: bool
    ciclo_s: int


@dataclass(frozen=True)
class PlanHorarioCruce:
    version_prog_id: int
    cruce_id: int
    tipo_dia: str
    hora_inicio_s: int
    hora_fin_s: int
    plan_id: int


@dataclass(frozen=True)
class BandaFlujoVehicular:
    campania_id: int
    cruce_id: int
    t_inicio_s: int
    t_fin_s: int
    flujo_veh_h: float
    movimiento_id: int | None = None
    tipo_dia: str = 'Laboral'


@dataclass(frozen=True)
class EventoHCall:
    itinerario_id: int
    cruce_id: int
    hcall_in_s: int
    hcall_out_s: int
    instante_paso_s: int | None = None
    servicio_id: int | None = None
    sentido: str | None = None


@dataclass(frozen=True)
class EscenarioSimulacion:
    escenario_id: int
    nombre: str
    cruce_id: int
    version_prog_id: int
    campania_id: int
    itinerario_id: int
    tipo_dia: str = 'Laboral'
    hora_inicio_s: int = 21600
    hora_fin_s: int = 75600
    headway_s: float = 2.0
    num_carriles: float = 2.0
    buffer_pre_s: int = 0
    k_dem: float = 1.1
    modo: str = 'corrected'
