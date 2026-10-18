import numpy as np

# Left DNp01 / giant fiber, FlyWire v783 (VFB; research annotation-root-ids C3).
# Sanity check only — never used to select neurons.
LEFT_DNP01_V783: int = 720575940622838154


class SanityError(Exception):
    pass


def check_left_dnp01(dnp01_ids: np.ndarray) -> None:
    if LEFT_DNP01_V783 not in set(dnp01_ids.tolist()):
        raise SanityError("known left DNp01 root ID is absent from the DNp01 lookup result")


def check_gf_in_circuit(gf_ids: np.ndarray, member_ids: np.ndarray) -> None:
    if LEFT_DNP01_V783 not in set(gf_ids.tolist()):
        raise SanityError("known left DNp01 root ID is not in the GF group")
    if LEFT_DNP01_V783 not in set(member_ids.tolist()):
        raise SanityError("known left DNp01 root ID is not in the circuit")
