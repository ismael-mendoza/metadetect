import copy

import ngmix.procflags
from ngmix.procflags import NO_ATTEMPT  # noqa

# these flags start at 16 always
# this allows us to combine them with the flags in ngmix
EDGE_HIT = 2**16
PSF_FAILURE = 2**17
OBJ_FAILURE = 2**18
NOMOMENTS_FAILURE = 2**19
BAD_BBOX = 2**20
ZERO_WEIGHTS = 2**21
NO_DATA = 2**22

NAME_MAP = copy.deepcopy(ngmix.procflags.NAME_MAP)
NAME_MAP[EDGE_HIT] = "bbox hit edge"
NAME_MAP[PSF_FAILURE] = "PSF fit failed"
NAME_MAP[OBJ_FAILURE] = "object fit failed"
NAME_MAP[NOMOMENTS_FAILURE] = "no moments"
NAME_MAP[BAD_BBOX] = "problem making bounding box"
NAME_MAP[ZERO_WEIGHTS] = "weights all zero"
NAME_MAP[NO_DATA] = "no/missing data"
for k, v in list(NAME_MAP.items()):
    NAME_MAP[v] = k


def get_procflags_str(val):
    """Get a descriptive string given a flag value.

    Parameters
    ----------
    val : int
        The flag value.

    Returns
    -------
    flagstr : str
        A string of descriptions for each bit separated by `|`.
    """
    return ngmix.procflags.get_procflags_str(val, name_map=NAME_MAP)
