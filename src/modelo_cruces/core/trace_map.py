"""Equivalencia entre columnas heredadas del Excel y nombres semanticos.

Permite mantener trazabilidad de auditoria sin propagar nombres como D, E,
F, AA o AK al resto del codigo nuevo.
"""
EXCEL_TRACE_MAP = {
    'D': 'hcall_in_flag',
    'E': 'hcall_out_flag',
    'F': 'hcall_balance',
    'G': 'hcall_active',
    'H': 'hcall_end',
    'I': 'hcall_pause_accumulated',
    'J': 'time_without_hcall',
    'K': 'cycle_position_base_raw',
    'M': 'cycle_offset_base',
    'N': 'cycle_position_base',
    'R': 'effective_red_base',
    'V': 'arrivals_per_second',
    'X': 'queue_base',
    'AA': 'preclearance_lookahead_trigger',
    'AF': 'cycle_offset_preclearance',
    'AG': 'cycle_position_preclearance',
    'AK': 'effective_red_preclearance',
    'AO': 'queue_preclearance',
}
