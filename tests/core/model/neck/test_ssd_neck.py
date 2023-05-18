import unittest

import torch
from torch import nn

from autocare_dlt.core.model.neck import SSDNeck


class TestSSDNeck(unittest.TestCase):
    def setUp(self):
        self.dummy_cfg = dict(
            in_channels=[256, 512],
            out_channels=[256, 512, 512, 256, 256, 128],
            l2_norm_scale=20,
        )
        self.dummy_input_list = [
            torch.rand(2, 256, 14, 14),
            torch.rand(2, 512, 7, 7),
        ]
        self.dummy_input_dict = {
            str(n): f for n, f in enumerate(self.dummy_input_list)
        }

    def tearDown(self):
        pass

    def test_build_neck(self):
        neck = SSDNeck(**self.dummy_cfg)
        with self.assertRaises(ValueError):
            wrong_out_channels = dict(
                in_channels=[128, 256, 512], out_channels=[256, 512]
            )
            SSDNeck(**wrong_out_channels)

    def test_run_neck(self):
        neck = SSDNeck(**self.dummy_cfg)
        res_list_input = neck(self.dummy_input_list)
        res_dict_input = neck(self.dummy_input_dict)

        self.assertIsInstance(res_list_input, list)
        self.assertIsInstance(res_dict_input, list)
        self.assertTrue(torch.is_tensor(res_list_input[0]))
        self.assertEqual(
            torch.sum(res_list_input[0]).item(),
            torch.sum(res_dict_input[0]).item(),
        )
        for res, num_ch in zip(res_list_input, self.dummy_cfg["out_channels"]):
            self.assertEqual(res.size()[1], num_ch)
