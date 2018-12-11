import copy
import ngmix
import esutil as eu
from . import detect
from . import fitting


def do_metadetect_and_cal(
        config, mbobs, rng, wcs_func=None, psf_rec_funcs=None):
    """
    Meta-detect and cal on the multi-band observations.
    """
    md = MetadetectAndCal(
        config, mbobs, rng, wcs_func=wcs_func, psf_rec_funcs=psf_rec_funcs)
    md.go()
    return md.result


class MetadetectAndCal(dict):
    """
    Meta-detect and cal on the multi-band observations.

    parameters
    ----------
    config: dict
        Configuration dictionary. Possible entries are
            metacal
            weight (if calculating weighted moments)
            max: (if running a max like fitter)
            fofs (if running MOF)
            mof (if running MOF)

    """
    def __init__(self, config, mbobs, rng, wcs_func=None, psf_rec_funcs=None):
        self._set_config(config)
        self.mbobs = mbobs
        self.nband = len(mbobs)
        self.rng = rng
        self.wcs_func = wcs_func
        if psf_rec_funcs is None:
            self.psf_rec_funcs = [None] * len(mbobs)
        else:
            assert len(psf_rec_funcs) == len(mbobs)
            self.psf_rec_funcs = psf_rec_funcs

        self._set_fitter()

    @property
    def result(self):
        """
        get the result dict, keyed by the metacal type such
        as 'noshear', '1p', '1m', '2p', '2m'
        """
        if not hasattr(self, '_result'):
            raise RuntimeError('run go() first')

        return self._result

    def go(self):
        """
        make sheared versions of the images, run detection and measurements
        on each
        """
        odict = self._get_all_metacal()

        self._result = {}
        for key, sheared_mbobs in odict.items():
            self._result[key] = self._measure(sheared_mbobs, key)

    def _measure(self, sheared_mbobs, mcal_step):
        """
        perform measurements on the input mbobs. This involves running
        detection as well as measurements
        """

        # returns a MultiBandNGMixMEDS interface for the sheared positions
        # on the **original** image
        mbm, cat = self._do_detect(sheared_mbobs)
        mbobs_list = mbm.get_mbobs_list()

        # do the desired mcal step
        mcal_config = copy.deepcopy(self['metacal'])
        mcal_config['force_required_types'] = False
        mcal_config['types'] = [mcal_step]
        mcal_mbobs_list = []
        for mbobs in mbobs_list:
            mcal_dict = ngmix.metacal.get_all_metacal(
                mbobs,
                rng=self.rng,
                **mcal_config,
            )
            mcal_mbobs_list.append(mcal_dict[mcal_step])

        res = self._fitter.go(mbobs_list)

        res = self._add_positions(cat, res)
        return res

    def _set_fitter(self):
        """
        set the fitter to be used
        """
        self._fitter = fitting.Moments(
            self,
            self.rng,
        )

    def _add_positions(self, cat, res):
        """
        add catalog positions to the result
        """
        if cat.size > 0:
            new_dt = [
                ('sx_row', 'f4'),
                ('sx_col', 'f4'),
            ]
            newres = eu.numpy_util.add_fields(
                res,
                new_dt,
            )

            newres['sx_col'] = cat['x']
            newres['sx_row'] = cat['y']
        else:
            newres = res

        return newres

    def _do_detect(self, sheared_mbobs):
        """
        use a MEDSifier to run detection
        """
        sheared_mer = detect.MEDSifier(
            sheared_mbobs,
            sx_config=self['sx'],
            meds_config=self['meds'],
            wcs=self.wcs_func,
        )

        # now build the meds interface on the **orig** obs
        mlist = []
        for obslist, psf_rec in zip(self.mbobs.copy(), self.psf_rec_funcs):
            obs = obslist[0]
            mlist.append(detect.MEDSInterface(
                obs,
                sheared_mer.seg,
                sheared_mer.cat,
                psf_rec=psf_rec))

        return detect.MultiBandNGMixMEDS(mlist), sheared_mer.cat

    def _get_all_metacal(self):
        """
        get the sheared versions of the observations
        """

        if self['metacal'].get('symmetrize_psf', False):
            assert 'psf' in self, 'need psf fitting for symmetrize_psf'
            fitting.fit_all_psfs(self.mbobs, self['psf'], self.rng)

        odict = ngmix.metacal.get_all_metacal(
            self.mbobs,
            rng=self.rng,
            **self['metacal']
        )

        return odict

    def _set_config(self, config):
        """
        set the config, dealing with defaults
        """

        self.update(config)
        assert 'metacal' in self, \
            'metacal setting must be present in config'
        assert 'sx' in self, \
            'sx setting must be present in config'
        assert 'meds' in self, \
            'meds setting must be present in config'
